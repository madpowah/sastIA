import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from code_fetcher import fetch_code, _is_safe_url, _is_trusted_url
from opencode_runner import run_manager_agent
from docker_cleanup import cleanup_audit_by_id
from sastia_report import merge_reports

WORK_DIR = Path(os.getenv("WORK_DIR", "/tmp/sastia-worker"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_SRC = PROJECT_ROOT / ".opencode" / "agents"
AGENTS_DST = Path(os.path.expanduser("~/.config/opencode/agents"))
SKILLS_SRC = PROJECT_ROOT / ".opencode" / "skills"
SKILLS_DST = Path(os.path.expanduser("~/.config/opencode/skills"))


def _sync_agents():
    if not AGENTS_SRC.exists():
        return
    AGENTS_DST.mkdir(parents=True, exist_ok=True)
    for f in AGENTS_SRC.glob("*.md"):
        dst = AGENTS_DST / f.name
        if not dst.exists() or dst.stat().st_mtime < f.stat().st_mtime:
            dst.write_text(f.read_text())


def _sync_skills():
    if not SKILLS_SRC.exists():
        return
    for src_dir in SKILLS_SRC.iterdir():
        if src_dir.is_dir():
            dst_dir = SKILLS_DST / src_dir.name
            dst_dir.mkdir(parents=True, exist_ok=True)
            for f in src_dir.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(src_dir)
                    dst = dst_dir / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if not dst.exists() or dst.stat().st_mtime < f.stat().st_mtime:
                        dst.write_text(f.read_text())


_sync_agents()
_sync_skills()

app = FastAPI(title="SAST IA Worker", version="1.0.0")

# ── In-memory active jobs ──────────────────────────────
_active_jobs: dict[str, datetime] = {}


class AnalyzeRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    audit_id: str
    user_id: str
    callback_url: str
    callback_secret: Optional[str] = None
    repo_url: Optional[str] = None
    code_path: Optional[str] = None
    analysis_type: str = "code"
    docker_analysis: bool = False
    model_id: Optional[str] = None
    report_language: str = "en"
    backend_base_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    audit_id: str
    status: str
    message: str


# ── Helpers ────────────────────────────────────────────

def _meta_path(audit_id: str) -> Path:
    return WORK_DIR / audit_id / "meta.json"


def _write_meta(audit_id: str, **kwargs):
    path = _meta_path(audit_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"audit_id": audit_id}
    if path.exists():
        data.update(json.loads(path.read_text()))
    data.update(kwargs)
    path.write_text(json.dumps(data, indent=2, default=str))


def _find_log(audit_id: str) -> Optional[Path]:
    candidates = [
        WORK_DIR / audit_id / "opencode.log",
        WORK_DIR / audit_id / "code" / "opencode.log",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _partial_log(audit_id: str) -> str:
    parts = []
    log_path = _find_log(audit_id)
    if log_path:
        parts.append(log_path.read_text(encoding="utf-8", errors="replace"))

    for partial_name in ["agent-partial.md"]:
        for base in [WORK_DIR / audit_id, WORK_DIR / audit_id / "code"]:
            p = base / partial_name
            if p.exists():
                parts.append(f"\n\n## AGENT OUTPUT ({p.name})\n\n" + p.read_text(encoding="utf-8", errors="replace"))

    return "\n".join(parts)


async def _callback_with_secret(url: str, secret: str | None, payload: dict):
    import httpx

    headers = {}
    if secret:
        headers["X-Callback-Secret"] = secret
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload, headers=headers)
    except Exception as cb_err:
        print(f"[worker] Callback failed: {cb_err}")


async def run_analysis(job: AnalyzeRequest):
    audit_dir = WORK_DIR / job.audit_id
    audit_dir.mkdir(parents=True, exist_ok=True)

    _write_meta(job.audit_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
    _active_jobs[job.audit_id] = datetime.now(timezone.utc)

    try:
        print(f"[worker] Starting analysis for audit {job.audit_id}")
        code_dir = await fetch_code(job, audit_dir / "code")
        print(f"[worker] Code fetched to {code_dir}")

        vulnhunt_dir = Path(str(code_dir)) / "vulnhunt_results"
        vulnhunt_dir.mkdir(parents=True, exist_ok=True)
        print(f"[worker] VULNHUNT_DIR created at {vulnhunt_dir}")

        await run_manager_agent(
            code_dir=str(code_dir),
            audit_id=job.audit_id,
            callback_url=job.callback_url,
            repo_url=job.repo_url,
            model_id=job.model_id,
            report_language=job.report_language,
            docker_analysis=job.docker_analysis,
            callback_secret=job.callback_secret,
        )
<<<<<<< HEAD
        print(f"[worker] Agent analysis complete for audit {job.audit_id}")

        # ── Post-agent: merge raw results with agent report and callback ──
        audit_dir_path = audit_dir
        agent_report = audit_dir_path / "final-report.json"
        payload = merge_reports(audit_dir_path, agent_report)
        print(f"[worker] Merged report: {len(payload['vulnerabilities'])} vulns, "
              f"metrics={payload['metrics']}")

        await _callback_with_secret(job.callback_url, job.callback_secret, payload)
        print(f"[worker] Callback completed for audit {job.audit_id}")

=======
        print(f"[worker] Analysis complete for audit {job.audit_id}")

        # Worker handles callback (agent may not include secret properly)
        report_json = vulnhunt_dir / "report.json"
        report_readme = vulnhunt_dir / "README.md"
        payload = {"report_markdown": ""}
        if report_json.exists():
            raw = report_json.read_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload["report_markdown"] = raw
        if not payload.get("report_markdown") and report_readme.exists():
            payload["report_markdown"] = report_readme.read_text()

        # Collect PoC and exploit test artifacts for the callback
        artifacts = {}
        poc_dir = vulnhunt_dir / "poc"
        test_dir = vulnhunt_dir / "exploit_tests"
        if poc_dir.exists():
            for f in poc_dir.iterdir():
                if f.is_file():
                    artifacts[f"poc/{f.name}"] = f.read_text(encoding="utf-8", errors="replace")
        if test_dir.exists():
            for f in test_dir.iterdir():
                if f.is_file():
                    artifacts[f"exploit_tests/{f.name}"] = f.read_text(encoding="utf-8", errors="replace")
        if artifacts:
            payload["artifacts"] = artifacts
            print(f"[worker] Collected {len(artifacts)} artifacts")

        await _callback_with_secret(job.callback_url, job.callback_secret, payload)
        print(f"[worker] Callback sent to {job.callback_url}")
>>>>>>> fa71c93 (v0.2: VulnHunter pipeline + real Docker validation)
        _write_meta(job.audit_id, status="completed", finished_at=datetime.now(timezone.utc).isoformat())

    except Exception as e:
        print(f"[worker] Error during analysis: {e}")
        _write_meta(job.audit_id, status="failed", error=str(e), finished_at=datetime.now(timezone.utc).isoformat())

        partial = _partial_log(job.audit_id)
        error_payload = {
            "report_markdown": partial if partial else "",
            "error": str(e),
        }
        await _callback_with_secret(job.callback_url, job.callback_secret, error_payload)

    finally:
        _active_jobs.pop(job.audit_id, None)
        if job.docker_analysis:
            try:
                cleanup_audit_by_id(job.audit_id)
                print(f"[worker] Docker cleanup done for audit {job.audit_id}")
            except Exception as clean_err:
                print(f"[worker] Docker cleanup error: {clean_err}")


# ── Endpoints ──────────────────────────────────────────

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    if request.code_path and not _is_safe_url(request.code_path) and not _is_trusted_url(request.code_path, request.backend_base_url):
        raise HTTPException(status_code=400, detail="Invalid code_path URL")
    asyncio.create_task(run_analysis(request))
    return AnalyzeResponse(
        audit_id=request.audit_id,
        status="started",
        message="Analysis job started. SastIA_manager will handle agents and callback.",
    )


@app.get("/log/{audit_id}", response_class=PlainTextResponse)
def view_log(audit_id: str):
    content = _partial_log(audit_id)
    if not content:
        raise HTTPException(status_code=404, detail="No log found for this audit")
    return content


@app.get("/status")
def worker_status():
    return {
        "active_jobs": list(_active_jobs.keys()),
        "active_job_count": len(_active_jobs),
    }


@app.get("/meta/{audit_id}")
def get_meta(audit_id: str):
    path = _meta_path(audit_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="No meta found for this audit")
    return json.loads(path.read_text())


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
