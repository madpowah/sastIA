import os
import sys
import asyncio
import shutil
from pathlib import Path


def _find_opencode() -> list[str]:
    if shutil.which("opencode"):
        return ["opencode"]
    if sys.executable:
        return [sys.executable, "-m", "opencode"]
    raise RuntimeError("opencode not found on PATH or as Python module")


async def run_manager_agent(
    code_dir: str,
    audit_id: str,
    callback_url: str,
    repo_url: str | None = None,
    model_id: str | None = None,
    report_language: str = "en",
    docker_analysis: bool = False,
    callback_secret: str | None = None,
    timeout: int = 7200,
) -> str:
    audit_dir = os.path.dirname(code_dir)
    worker_log = os.path.join(audit_dir, "opencode.log")
    partial_file = os.path.join(audit_dir, "agent-partial.md")
    prompt_file = os.path.join(audit_dir, "prompt.txt")

    source_desc = repo_url or f"uploaded file (extracted to {code_dir})"

    report_language_instruction = {
        "fr": "Le rapport final DOIT être rédigé en français.",
        "en": "The final report MUST be written in English.",
    }.get(report_language, "The final report MUST be written in English.")

<<<<<<< HEAD
    FINAL_REPORT_PATH = os.path.join(audit_dir, "final-report.json")

    docker_steps = ""
    if docker_analysis:
        docker_steps = f"""1. Active @SastIA_docker en lui indiquant le chemin {code_dir} pour qu'il mette en place l'environnement de test
2. Active @SastIA_analyzer en lui fournissant le même chemin {code_dir} et les infos Docker pour l'audit de sécurité
3. Active @SastIA_rapport pour produire le rapport final ÉCRIS-LE au chemin : {FINAL_REPORT_PATH}
4. **NETTOYAGE OBLIGATOIRE** : Active @SastIA_docker pour supprimer le conteneur (docker stop + docker rm), l'image (docker rmi) et les fichiers temporaires. Vérifie que tout est bien supprimé avant de terminer."""
    else:
        docker_steps = f"""1. Passe l'étape @SastIA_docker (non requis pour cette analyse — pas de validation Docker)
2. Active @SastIA_analyzer en lui fournissant le chemin {code_dir} pour l'audit de sécurité (sans validation Docker)
3. Active @SastIA_rapport pour produire le rapport final et ÉCRIS-LE au chemin JSON : {FINAL_REPORT_PATH}"""
=======
    docker_validation = ""
    docker_cleanup = ""
    if docker_analysis:
        docker_validation = f"""
5. **Docker Build** : Active @SastIA_docker avec CODE_DIR={code_dir} pour builder l'image et lancer le conteneur. Récupère ## Docker Environment Summary.
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)

6. **Docker Validation** : Active @SastIA_analyzer avec :
   "Validation Docker. VULNHUNT_DIR={code_dir}/vulnhunt_results DOCKER_URL=<url> DOCKER_CONTAINER=<name>
    Exécute les PoC de poc/ et exploit_tests/ contre le conteneur.
    Marque : VALIDATED / FAILED / NOT-TESTED. Écris validation_results.md"

7. **Cleanup Docker** : Active @SastIA_docker pour supprimer conteneur + image
"""
        docker_cleanup = "\n8. **NETTOYAGE** : Active @SastIA_docker pour supprimer conteneur + image"

    phases_dir = os.path.expanduser("~/.config/opencode/skills/vulnhunt/phases")
    skill_dir = os.path.expanduser("~/.config/opencode/skills/vulnhunt")

    prompt = f"""Tu es SastIA_manager, l'orchestrateur d'audit de sécurité basé sur la méthodologie VulnHunter.

Le code source à analyser se trouve ici : {code_dir}
Il provient de : {source_desc}
L'ID de l'audit est : {audit_id}
{report_language_instruction}

## Variables
- CODE_DIR={code_dir}
- VULNHUNT_DIR={code_dir}/vulnhunt_results
- PHASES_DIR={phases_dir}
- SKILL_DIR={skill_dir}
- CALLBACK_URL={callback_url} (le worker envoie le callback automatiquement)
- DOCKER_ENABLED={'true' if docker_analysis else 'false'}

Compatible tous modèles. Statique par défaut. Si DOCKER_ENABLED, validation Docker après Phase 3.

## Pipeline

Suis `${{SKILL_DIR}}/SKILL.md`. Phases dans `${{PHASES_DIR}}/`.

1. **Phase 1 - Recon** : Active @SastIA_analyzer : "Phase 1. VULNHUNT_DIR={code_dir}/vulnhunt_results PHASES_DIR={phases_dir}. Suis phase1_recon.md. Écris phase1_output.md"

2. **Phase 2 - Hunt** : Lis ${{PHASES_DIR}}/phase2_hunt.md. Crée les partitions. Dispatche les agents de traçage (3/partition + sink-driven). Utilise @SastIA_analyzer.

3. **Phase 2b - Verify** : Active @SastIA_analyzer : "Phase 2b. Mêmes vars. Suis phase2b_verify.md. Écris phase2b_output.md"

4. **Phase 3 - Reproduce/Fix/Sweep** : Active @SastIA_analyzer : "Phase 3. Mêmes vars. Suis phase3_reproduce_test.md, phase3c_fixes.md, phase3d_sweep.md. Écris poc/, exploit_tests/, phase3_output.md, phase3d_output.md"
{docker_validation}
7. **Rapport** : Active @SastIA_rapport. Suis ${{PHASES_DIR}}/phase4_report.md. Inclus validation_results.md si dispo. Écris le JSON dans ${{VULNHUNT_DIR}}/report.json
{docker_cleanup}
IMPORTANT : Ne fais pas d'analyse toi-même. Dispatche TOUT."""

    DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"

    model = model_id or os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL)
    if model and "/" not in model:
        model = f"opencode-go/{model}"
    opencode_cmd = _find_opencode()
    Path(prompt_file).write_text(prompt, encoding="utf-8")
    cmd = [
        *opencode_cmd, "run",
        "--model", model,
        "--dir", audit_dir,
        prompt,
    ]

    print(f"[opencode] Launching agent with model {model}...")
    print(f"[opencode] Workspace dir: {audit_dir}")
    print(f"[opencode] Code dir: {code_dir}")
    print(f"[opencode] Callback: {callback_url}")
    print(f"[opencode] Log file: {worker_log}")
    print(f"[opencode] Command: {' '.join(cmd[:4])} ...")

    collected_lines: list[str] = []
    save_interval = 30
    last_save = asyncio.get_event_loop().time()

    async def _stream(stream_name: str, stream: asyncio.StreamReader | None, log_f):
        nonlocal last_save
        if stream is None:
            return
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode(errors="replace")
            log_f.write(f"[{stream_name}] {text}")
            log_f.flush()
            collected_lines.append(text)

            now = asyncio.get_event_loop().time()
            if now - last_save > save_interval:
                last_save = now
                partial = "".join(collected_lines[-200:])
                try:
                    Path(partial_file).write_text(partial, encoding="utf-8")
                except OSError:
                    pass

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=audit_dir,
        )

        with open(worker_log, "w", encoding="utf-8") as lf:
            lf.write(f"# opencode log — audit {audit_id}\n")
            import time as ttime
            lf.write(f"# started at {ttime.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            lf.flush()

            stdout_task = asyncio.create_task(_stream("stdout", proc.stdout, lf))
            stderr_task = asyncio.create_task(_stream("stderr", proc.stderr, lf))

            try:
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, proc.wait()),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                lf.write(f"\n\n[TIMEOUT] Agent timed out after {timeout}s ({timeout//3600}h)\n")
                lf.flush()
                proc.kill()
                _ = await asyncio.wait_for(proc.wait(), timeout=10.0)
                partial = "".join(collected_lines)
                if partial.strip():
                    Path(partial_file).write_text(partial, encoding="utf-8")
                raise RuntimeError(
                    f"SastIA_manager agent timed out after {timeout}s. "
                    f"Log: {worker_log} (lines collected: {len(collected_lines)})"
                )

        return_code = await proc.wait()
        result = "".join(collected_lines)

        if result.strip():
            Path(partial_file).write_text(result, encoding="utf-8")

        if return_code != 0:
            print(f"[opencode] Agent exited with code {return_code}")
            if not result.strip():
                raise RuntimeError(f"Agent exited with code {return_code} and no output")

        print(f"[opencode] SastIA_manager agent completed (exit code {return_code}, {len(collected_lines)} lines)")
        return result

    except FileNotFoundError:
        raise RuntimeError("opencode not found. Install: pip install opencode")
