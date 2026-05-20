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
    timeout: int = 7200,
) -> str:
    audit_dir = os.path.dirname(code_dir)
    worker_log = os.path.join(audit_dir, "opencode.log")
    partial_file = os.path.join(audit_dir, "agent-partial.md")
    prompt_file = os.path.join(audit_dir, "prompt.txt")

    source_desc = repo_url or f"fichier uploadé (extrait dans {code_dir})"

    report_language_instruction = {
        "fr": "Le rapport final DOIT être rédigé en français.",
        "en": "The final report MUST be written in English.",
    }.get(report_language, "The final report MUST be written in English.")

    docker_steps = ""
    if docker_analysis:
        docker_steps = f"""1. Active @SastIA_docker en lui indiquant le chemin {code_dir} pour qu'il mette en place l'environnement de test
2. Active @SastIA_analyzer en lui fournissant le même chemin {code_dir} et les infos Docker pour l'audit de sécurité
3. Active @SastIA_rapport pour produire le rapport final
4. Envoie le rapport final à l'URL de callback : {callback_url}
5. Supprime les environnements de test une fois l'audit terminé"""
        docker_cleanup = "\n5. Supprime les environnements de test une fois l'audit terminé"
    else:
        docker_steps = f"""1. Passe l'étape @SastIA_docker (non requis pour cette analyse)
2. Active @SastIA_analyzer en lui fournissant le chemin {code_dir} pour l'audit de sécurité (sans validation Docker)
3. Active @SastIA_rapport pour produire le rapport final
4. Envoie le rapport final à l'URL de callback : {callback_url}"""

    prompt = f"""Tu es SastIA_manager, l'orchestrateur d'audit de sécurité.

Le code source à analyser se trouve ici : {code_dir}
Il provient de : {source_desc}
L'ID de l'audit est : {audit_id}
{report_language_instruction}

    Consignes :
{docker_steps}

Le rapport DOIT contenir un tableau de synthèse avec le format suivant pour que les compteurs soient parsés automatiquement :

| Severity | Count |
|----------|-------|
| Critical | N |
| High     | N |
| Medium   | N |
| Low      | N |

QUAND TU ACTIVES @SastIA_analyzer et @SastIA_rapport, **transmets-leur explicitement** la langue du rapport : "{report_language_instruction}"
Ne fais pas d'analyse toi-même, délègue chaque étape aux agents spécialisés (@SastIA_docker, @SastIA_analyzer, @SastIA_rapport)."""

    DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"

    model = model_id or os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL)
    if model and "/" not in model:
        model = f"opencode-go/{model}"
    opencode_cmd = _find_opencode()
    Path(prompt_file).write_text(prompt, encoding="utf-8")
    cmd = [
        *opencode_cmd, "run",
        "--model", model,
        "--dir", code_dir,
        "--dangerously-skip-permissions",
        prompt,
    ]

    print(f"[opencode] Launching agent with model {model}...")
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
            cwd=code_dir,
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
