"""Reprend un audit interrompu sans refaire les phases deja produites.

Contexte : l'agent opencode tourne dans un service de fond partage. Quand le
worker atteint son timeout (5 h web / 9 h natif), il tue le CLI, mais les
artefacts deja ecrits restent sur disque et la session opencode est perdue
(`session list` est vide) : impossible de la « reprendre » au sens conversation.

Ce script reprend donc **par les artefacts** : il relance un agent sur le meme
`code_dir` avec une consigne qui interdit de refaire les phases 0 -> 2c et qui
demande uniquement la Phase 3 (PoC, tests d'exploit, validation) puis la Phase 4
(rapport). Il rejoue ensuite la finalisation du worker (markdown, compteurs,
controle d'integrite des tests, callback) pour que l'audit passe de `failed` a
`completed` avec un vrai rapport.

Usage :
    python resume_audit.py <audit_id> --dry-run     # montre le plan, n'execute rien
    python resume_audit.py <audit_id>               # reprend et envoie le callback
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

WORKER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKER_DIR))

from exploit_audit import (  # noqa: E402
    append_integrity_section,
    audit_exploit_tests,
    write_report,
)

WORK_DIR = Path(os.getenv("WORK_DIR", "/tmp/sastia-worker"))
DB_PATH = Path('/home/debian/www/sastIA/backend/sastia.db')
CALLBACK_BASE = 'http://127.0.0.1:8000'
OPENCODE = shutil.which('opencode') or '/home/debian/.opencode/bin/opencode'
TIMEOUT = 32400  # 9 h

# Fichiers qui prouvent qu'une phase est deja faite.
DONE_MARKERS = {
    'phase0': ['target_shaping.md'],
    'phase1': ['phase1_output.md'],
    'phase2': ['phase2_merge.md'],
    'phase2b': ['phase2b_output.md'],
    'phase2c': ['phase2c_output.md'],
    'phase3': ['phase3_output.md', 'exploit_tests'],
    'phase4': ['report.json'],
}


def find_layout(audit_id: str) -> tuple[Path, Path, str]:
    """Retourne (code_dir, vulnhunt_dir, target_type) pour cet audit."""
    audit_dir = WORK_DIR / audit_id
    meta_path = audit_dir / 'meta.json'
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    target_type = (meta.get('target') or {}).get('target_type', 'web')
    results_name = meta.get('results_dir') or (
        'vulnhunt_native_results' if target_type == 'native' else 'vulnhunt_results'
    )

    code_root = audit_dir / 'code'
    candidates = [p for p in code_root.iterdir() if p.is_dir()] if code_root.is_dir() else []
    for candidate in candidates:
        if (candidate / results_name).is_dir():
            return candidate, candidate / results_name, target_type
    for candidate in candidates:
        if candidate.name not in ('extracted', 'dl2', 'out'):
            return candidate, candidate / results_name, target_type
    raise SystemExit(f'modele de travail introuvable sous {code_root}')


def phase_state(vulnhunt_dir: Path) -> dict[str, bool]:
    state = {}
    for phase, markers in DONE_MARKERS.items():
        found = False
        for marker in markers:
            path = vulnhunt_dir / marker
            if path.is_dir():
                # un dossier vide ne prouve rien
                if any(path.iterdir()):
                    found = True
            elif path.exists():
                found = True
        state[phase] = found
    return state


def db_fields(audit_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        'SELECT callback_secret, model_id, report_language, docker_analysis_enabled, name '
        'FROM audits WHERE id=?', (audit_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise SystemExit(f'audit {audit_id} introuvable en base')
    return {
        'callback_secret': row[0],
        'model_id': row[1] or 'opencode-go/deepseek-v4.1-flash',
        'report_language': row[2] or 'en',
        'docker': bool(row[3]),
        'name': row[4],
    }


def build_prompt(audit_id, code_dir, vulnhunt_dir, target_type, docker, language) -> str:
    skill = 'vulnhunt-native' if target_type == 'native' else 'vulnhunt'
    skill_dir = os.path.expanduser(f'~/.config/opencode/skills/{skill}')
    phases_dir = f'{skill_dir}/phases'
    dynamic = (
        'TARGET_MODE=dynamic : la validation s execute dans le conteneur Docker.'
        if docker else 'TARGET_MODE=static : pas de conteneur, marque les findings non prouves Potential.'
    )
    return f"""Tu reprends un audit SAST IA INTERROMPU par un timeout. Ne recommence PAS depuis le debut.

## Etat deja produit (a LIRE, ne pas refaire)
- Dossier de resultats : {vulnhunt_dir}
- Phases deja terminees : 0 (target_shaping), 1 (phase1_output.md), 2 (phase2_merge.md),
  2b (phase2b_output.md), 2c (phase2c_output.md), latent_defects.md
- Lis en priorite : phase2_merge.md (11 candidats C-01..C-11), phase2b_output.md
  (verdicts + findings confirmes), phase2c_output.md, latent_defects.md,
  invariant_register.md, et les resultats par lens dans {vulnhunt_dir}/results/

## Ce que tu dois produire maintenant, et RIEN d'autre
1. **Phase 3** — pour chaque finding CONFIRME de phase2b_output.md :
   - ecris {vulnhunt_dir}/poc/VULN-NNN_<slug>.md
   - ecris {vulnhunt_dir}/exploit_tests/test_vuln_NNN_<slug>.py (ou .c/.sh)
   - les tests DOIVENT etre executes : **Bash is AVAILABLE for exploit-test execution**.
     Aucune tautologie : l'assertion doit dependre d'un resultat observe (rapport
     ASan/UBSan, crash, signal, code retour, octets sur socket), jamais d'une
     constante codee en dur (`blocked = False`) ni d'un modele Python de la cible.
2. **Validation** — {dynamic}
   Ecris {vulnhunt_dir}/validation_results.md avec, PAR FINDING : la commande exacte,
   la sortie brute observee (verbatim) et le verdict parmi
   VALIDATED / STATIC-PROOF / FAILED / NOT-TESTED.
   Un test statique ou simule ne donne JAMAIS VALIDATED -> STATIC-PROOF.
3. **phase3_output.md** — tableau des findings + strategies de correction.
4. **Phase 4** — suis {phases_dir}/phase4_report.md et ecris
   {vulnhunt_dir}/report.json ET {vulnhunt_dir}/README.md (en-tete
   `# VulnHunter Security Audit Report`, Summary `ID | Title | CWE | Severity |
   Exploit Test | Status`, sections Resolved Input Inventory / Not Found /
   Code Quality / Sweep / Artifacts). Les liens vers poc/ et exploit_tests/
   doivent etre des liens markdown cliquables, jamais des code spans.

Langue du rapport : {language}. Ne refais pas les phases 0 a 2c. Ne tue pas de
conteneur. A la fin, termine par une ligne `## DONE resume-audit`."""


def run_agent(prompt: str, code_dir: Path, model: str, log_path: Path) -> int:
    cmd = [OPENCODE, 'run', '--model', model, prompt]
    started = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f'# resume — started at {started}\n# cwd: {code_dir}\n# model: {model}\n\n')
        log.flush()
        proc = subprocess.Popen(
            cmd, cwd=str(code_dir), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(line)
                log.flush()
            proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            log.write(f'\n[TIMEOUT] {TIMEOUT}s\n')
            proc.kill()
            return 124
    return proc.returncode or 0


def collect_artifacts(vulnhunt_dir: Path, max_bytes: int = 2_000_000) -> dict[str, str]:
    """Comme le worker : tous les fichiers texte du dossier de resultats.

    Les binaires (harness compiles, pcap) sont ignores : le backend les
    ecrirait en UTF-8 et les corromprait.
    """
    artifacts: dict[str, str] = {}
    if not vulnhunt_dir.exists():
        return artifacts
    for path in vulnhunt_dir.rglob('*'):
        if not path.is_file():
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
            raw = path.read_bytes()
        except OSError:
            continue
        if b'\x00' in raw[:8192]:
            continue
        artifacts[path.relative_to(vulnhunt_dir).as_posix()] = raw.decode('utf-8', errors='replace')
    return artifacts


def finalize(audit_id: str, vulnhunt_dir: Path, fields: dict) -> int:
    """Rejoue la finalisation du worker puis poste le callback."""
    import httpx

    report_json = vulnhunt_dir / 'report.json'
    payload: dict = {'report_markdown': ''}
    if report_json.exists():
        try:
            payload = json.loads(report_json.read_text())
        except json.JSONDecodeError:
            payload = {'report_markdown': report_json.read_text()}

    if not payload.get('report_markdown'):
        # meme selection que le worker : le plus gros markdown ressemblant a un rapport
        from main import _pick_report_markdown  # import tardif : main.py a des effets de bord
        payload['report_markdown'] = _pick_report_markdown(vulnhunt_dir) or ''
    if not payload.get('report_markdown'):
        print('ERREUR: aucun rapport produit, callback non envoye')
        return 2

    findings = audit_exploit_tests(vulnhunt_dir)
    if findings:
        real = sum(1 for f in findings if f.supports_validation)
        print(f'[resume] tests: {len(findings)} | attaques reelles: {real}')
        write_report(vulnhunt_dir)
        payload['report_markdown'] = append_integrity_section(
            payload['report_markdown'], findings
        )

    if not isinstance(payload.get('vulnerabilities'), dict):
        summary = payload.get('summary')
        if isinstance(summary, dict) and isinstance(summary.get('by_severity'), dict):
            norm = {str(k).strip().lower(): v for k, v in summary['by_severity'].items()}
            payload['vulnerabilities'] = {
                'critical': norm.get('critical', 0), 'high': norm.get('high', 0),
                'medium': norm.get('medium', 0), 'low': norm.get('low', 0),
                'info': norm.get('info', norm.get('informational', 0)),
            }

    # Les artefacts doivent partir avec le callback : le backend les ecrit sur
    # disque puis reecrit les liens relatifs du rapport vers /api/audits/.../artifacts/.
    artifacts = collect_artifacts(vulnhunt_dir)
    if artifacts:
        payload['artifacts'] = artifacts
    print(f'[resume] artefacts envoyes : {len(artifacts)}')

    url = f'{CALLBACK_BASE}/api/audits/{audit_id}/callback'
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            url, json=payload, headers={'X-Callback-Secret': fields['callback_secret']}
        )
    print(f'[resume] callback -> HTTP {resp.status_code} {resp.text[:200]}')
    return 0 if resp.status_code == 200 else 3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('audit_id')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--skip-agent', action='store_true',
                        help='ne relance pas l agent, finalise seulement')
    args = parser.parse_args()

    code_dir, vulnhunt_dir, target_type = find_layout(args.audit_id)
    fields = db_fields(args.audit_id)
    state = phase_state(vulnhunt_dir)

    print(f'audit      : {args.audit_id} ({fields["name"]})')
    print(f'cible      : {target_type}')
    print(f'code_dir   : {code_dir}')
    print(f'resultats  : {vulnhunt_dir}')
    print(f'modele     : {fields["model_id"]}  docker={fields["docker"]}')
    print('phases     : ' + ', '.join(f'{k}={"ok" if v else "-"}' for k, v in state.items()))

    prompt = build_prompt(
        args.audit_id, code_dir, vulnhunt_dir, target_type,
        fields['docker'], fields['report_language'],
    )
    print(f'prompt     : {len(prompt)} caracteres')

    if args.dry_run:
        print('\n--- prompt ---\n' + prompt)
        return 0

    if not args.skip_agent:
        log_path = code_dir.parent / 'resume.log'
        print(f'\n[resume] lancement de l agent (log: {log_path}) — jusqu a 9 h')
        rc = run_agent(prompt, code_dir, fields['model_id'], log_path)
        print(f'[resume] agent termine, code {rc}')
        if rc != 0:
            print('[resume] echec de l agent, pas de callback')
            return rc

    return finalize(args.audit_id, vulnhunt_dir, fields)


if __name__ == '__main__':
    raise SystemExit(main())
