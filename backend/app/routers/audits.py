import os
import re
import uuid
import shutil
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Audit, AuditStatus, DockerStatus
from app.schemas import AuditResponse, AuditListResponse, DashboardStats
from app.auth import get_current_user
from app.config import get_settings

ALLOWED_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".sh", ".bash", ".dockerfile", ".txt", ".md", ".xml", ".sql", ".gradle", ".mvn", ".csproj", ".sln"}


def parse_vulnerabilities_from_markdown(markdown: str) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    # Try parsing VulnHunter-style Summary table: | ID | Title | CWE | Severity | Status |
    vulnhunt_pattern = r"\|\s*(VULN-\d+)\s*\|\s*[^|]*\|\s*CWE-\d+\s*\|\s*(Critical|High|Medium|Low|Info|Informational)\s*\|"
    for match in re.finditer(vulnhunt_pattern, markdown, re.IGNORECASE):
        sev = match.group(2).lower()
        if sev == "informational":
            sev = "info"
        if sev in counts:
            counts[sev] += 1

    # Fallback: try legacy severity summary table
    if sum(counts.values()) == 0:
        for severity, keywords in [
            ("critical", [r"critiqu", r"critical"]),
            ("high", [r"[ée]lev", r"high"]),
            ("medium", [r"moyen", r"medium"]),
            ("low", [r"basse", r"low"]),
            ("info", [r"info", r"informational"]),
        ]:
            for kw in keywords:
                pattern = rf"{kw}.*?[|]\s*(\d+)\s*(?:\||$)"
                match = re.search(pattern, markdown, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    counts[severity] = int(match.group(1))
                    break

    return counts

settings = get_settings()
router = APIRouter(prefix="/api/audits", tags=["Audits"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audits = db.query(Audit).filter(Audit.user_id == current_user.id).order_by(Audit.created_at.desc()).all()

    stats = DashboardStats(
        total_audits=len(audits),
        pending_audits=sum(1 for a in audits if a.status in (AuditStatus.PENDING, AuditStatus.ANALYZING_CODE, AuditStatus.ANALYZING_DOCKER)),
        completed_audits=sum(1 for a in audits if a.status == AuditStatus.COMPLETED),
        failed_audits=sum(1 for a in audits if a.status == AuditStatus.FAILED),
        total_critical=sum(a.vulnerabilities_critical for a in audits),
        total_high=sum(a.vulnerabilities_high for a in audits),
        total_medium=sum(a.vulnerabilities_medium for a in audits),
        total_low=sum(a.vulnerabilities_low for a in audits),
        total_info=sum(a.vulnerabilities_info for a in audits),
        recent_audits=[AuditListResponse.model_validate(a) for a in audits[:10]],
    )
    return stats


@router.get("/", response_model=list[AuditListResponse])
def list_audits(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audits = db.query(Audit).filter(Audit.user_id == current_user.id).order_by(Audit.created_at.desc()).all()
    return [AuditListResponse.model_validate(a) for a in audits]


@router.post("/", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
def create_audit(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    repo_url: Optional[str] = Form(None),
    analysis_type: str = Form("code"),
    docker_analysis_enabled: bool = Form(False),
    model_id: Optional[str] = Form(None),
    report_language: str = Form("en"),
    code_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    audit = Audit(
        user_id=current_user.id,
        name=name,
        description=description,
        repo_url=repo_url,
        analysis_type=analysis_type,
        docker_analysis_enabled=1 if docker_analysis_enabled else 0,
        model_id=model_id,
        report_language=report_language,
        status=AuditStatus.PENDING,
        docker_status=DockerStatus.SUCCESS if docker_analysis_enabled else DockerStatus.NOT_STARTED,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    if code_file:
        file_ext = os.path.splitext(code_file.filename or "code.zip")[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id), str(audit.id))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"code{file_ext}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(code_file.file, f)
        audit.code_file_path = file_path
        db.commit()
        db.refresh(audit)

    return AuditResponse.model_validate(audit)


@router.get("/{audit_id}", response_model=AuditResponse)
def get_audit(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id), Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return AuditResponse.model_validate(audit)


@router.post("/{audit_id}/start", response_model=AuditResponse)
def start_analysis(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id), Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status not in (AuditStatus.PENDING, AuditStatus.FAILED):
        raise HTTPException(status_code=400, detail="Audit already started")

    audit.status = AuditStatus.ANALYZING_CODE
    audit.error_message = None
    db.commit()
    db.refresh(audit)

    # Send to worker asynchronously
    _dispatch_to_worker(audit, current_user, db)

    return AuditResponse.model_validate(audit)


def _dispatch_to_worker(audit: Audit, user: User, db: Session):
    audit.callback_secret = str(uuid.uuid4())
    db.commit()
    worker_url = f"{settings.WORKER_URL}/analyze"
    callback_url = f"{settings.CODE_DOWNLOAD_BASE_URL}/api/audits/{audit.id}/callback"
    download_base = f"{settings.CODE_DOWNLOAD_BASE_URL}/api/audits/{audit.id}/download"

    payload = {
        "audit_id": str(audit.id),
        "user_id": str(user.id),
        "callback_url": callback_url,
        "callback_secret": audit.callback_secret,
        "repo_url": audit.repo_url,
        "code_path": download_base if audit.code_file_path else None,
        "analysis_type": audit.analysis_type,
        "docker_analysis": bool(audit.docker_analysis_enabled),
        "model_id": audit.model_id,
        "report_language": audit.report_language or "en",
        "backend_base_url": settings.CODE_DOWNLOAD_BASE_URL,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(worker_url, json=payload)
    except Exception as e:
        print(f"[backend] Failed to dispatch to worker: {e}")


ARTIFACTS_DIR = os.path.join(settings.UPLOAD_DIR, "artifacts")

PHASE_LABELS = {
    "recon": "Phase 1: Reconnaissance",
    "hunt": "Phase 2: Vulnerability Hunt",
    "verify": "Phase 2b: Adversarial Verification",
    "reproduce": "Phase 3: Reproduce & Fix",
    "sweep": "Phase 3d: Codebase Sweep",
    "docker": "Docker Build & Validation",
    "report": "Phase 4: Report Generation",
}


@router.get("/{audit_id}/progress")
def get_audit_progress(audit_id: str, current_user: User = Depends(get_current_user)):
    """Return current phase progress by parsing worker logs for ##PHASE: markers."""
    audit = None
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        audit = db.query(Audit).filter(Audit.id == audit_id, Audit.user_id == current_user.id).first()
    finally:
        db.close()

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    progress = {"phase": None, "phase_label": None, "phase_num": 0, "total_phases": 6}

    try:
        import httpx
        r = httpx.get(f"{settings.WORKER_URL}/log/{audit_id}", timeout=5)
        if r.status_code == 200:
            log_text = r.text
            import re
            matches = re.findall(r"##PHASE:\s*(\w+)##", log_text)
            if matches:
                last = matches[-1].lower()
                phases = ["recon", "hunt", "verify", "reproduce", "docker", "report"]
                if last in phases:
                    idx = phases.index(last)
                    progress["phase"] = last
                    progress["phase_label"] = PHASE_LABELS.get(last, last)
                    progress["phase_num"] = idx + 1
                    progress["worker_log_preview"] = log_text[-500:]
    except Exception as e:
        progress["error"] = str(e)

    if audit.status == "completed":
        progress["phase"] = "complete"
        progress["phase_label"] = "Analysis Complete"
        progress["phase_num"] = 6
    elif audit.status == "failed":
        progress["phase"] = "failed"
        progress["phase_label"] = "Analysis Failed"

    return progress


@router.get("/{audit_id}/artifacts/{filepath:path}", include_in_schema=False)
def serve_artifact(audit_id: str, filepath: str):
    safe_path = os.path.normpath(filepath).lstrip("/")
    if ".." in safe_path.split(os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    full_path = os.path.join(ARTIFACTS_DIR, audit_id, safe_path)
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(full_path)


@router.get("/{audit_id}/download", include_in_schema=False)
def download_code(audit_id: uuid.UUID, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id)).first()
    if not audit or not audit.code_file_path:
        raise HTTPException(status_code=404, detail="No code file available")

    if not os.path.exists(audit.code_file_path):
        raise HTTPException(status_code=404, detail="Code file not found on disk")

    return FileResponse(
        audit.code_file_path,
        filename=os.path.basename(audit.code_file_path),
    )


class CallbackBody(BaseModel):
    report_markdown: Optional[str] = None
    vulnerabilities: Optional[dict] = None
    docker_success: Optional[bool] = None
    error: Optional[str] = None


SEVERITY_MAP = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low", "info": "Info", "informational": "Info"}
CVSS_THRESHOLDS = {"Critical": 9.0, "High": 7.0, "Medium": 4.0, "Low": 0.0}


def _severity_from_cvss(cvss: float) -> str:
    for sev, threshold in [("Critical", 9.0), ("High", 7.0), ("Medium", 4.0)]:
        if cvss >= threshold:
            return sev
    return "Low"


def _build_markdown_from_vulns(vulns: list[dict], summary: str = "", metrics: Optional[dict] = None) -> str:
    if not metrics:
        metrics = {}
    critical = metrics.get("critical", 0)
    high = metrics.get("high", 0)
    medium = metrics.get("medium", 0)
    low = metrics.get("low", 0)
    info = metrics.get("info", 0) or metrics.get("informational", 0)
    total = metrics.get("total_vulnerabilities", critical + high + medium + low + info)

    if not total:
        for v in vulns:
            sev = v.get("severity", "").lower()
            if sev in ("info", "informational"):
                info += 1
            elif sev in SEVERITY_MAP:
                if sev == "critical": critical += 1
                elif sev == "high": high += 1
                elif sev == "medium": medium += 1
                elif sev == "low": low += 1
            elif "cvss" in v:
                s = _severity_from_cvss(float(v["cvss"]))
                if s == "Critical": critical += 1
                elif s == "High": high += 1
                elif s == "Medium": medium += 1
                else: low += 1
        total = critical + high + medium + low + info

    lines = ["# SAST IA Security Audit Report"]
    if summary:
        lines.append(f"\n{summary}")
    lines.append(f"\n## Summary\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| Critical | {critical} |")
    lines.append(f"| High     | {high} |")
    lines.append(f"| Medium   | {medium} |")
    lines.append(f"| Low      | {low} |")
    if info:
        lines.append(f"| Info     | {info} |")
    lines.append(f"\n**Total: {total} vulnerabilities**")

    if vulns:
        lines.append(f"\n## Vulnerability Details\n")
        for v in vulns:
            vid = v.get("id", "")
            severity = v.get("severity", v.get("type", "Info"))
            cvss = v.get("cvss", "")
            title = v.get("title", vid or "Vulnerability")
            file_path = v.get("file_path", "")
            line = v.get("line", "")
            cwe = v.get("cwe", "")
            description = v.get("description", "")
            impact = v.get("impact", "")
            recommendation = v.get("recommendation", "")
            validation = v.get("validation_status", "") or "Not validated"
            code_snippet = v.get("code_snippet", "")
            remediation = v.get("remediation", "")
            proof = v.get("proof", "")
            entry_point = v.get("entry_point", "")
            data_flow = v.get("data_flow", "")
            root_cause = v.get("root_cause", "")

            if code_snippet:
                code_snippet = re.sub(r'^```\w*\s*\n?', '', code_snippet)
                code_snippet = re.sub(r'\n?```\s*$', '', code_snippet)

            lines.append(f"### {vid} — {title}")
            lines.append(f"- **Severity**: {severity} | **CVSS**: {cvss} | **Status**: {validation}")
            if file_path:
                lines.append(f"- **File**: `{file_path}`" + (f" | **Line**: {line}" if line else ""))
            if cwe:
                lines.append(f"- **CWE**: {cwe}")
            if entry_point:
                lines.append(f"- **Entry Point**: {entry_point}")
            if data_flow:
                lines.append(f"- **Data Flow**: {data_flow}")
            if description:
                lines.append(f"\n**Description**\n\n{description}")
            if impact:
                lines.append(f"\n**Impact**\n\n{impact}")
            if proof:
                lines.append(f"\n**Proof**\n\n{proof}")
            if code_snippet:
                lines.append(f"\n**Code**\n\n```\n{code_snippet}\n```")
            if root_cause:
                lines.append(f"\n**Root Cause**\n\n{root_cause}")
            if recommendation:
                lines.append(f"\n**Recommendation**\n\n{recommendation}")
            if remediation:
                lines.append(f"\n**Fix**\n\n{remediation}")
            lines.append("")

    return "\n".join(lines)


@router.post("/{audit_id}/callback", include_in_schema=False)
def analysis_callback(audit_id: uuid.UUID, request: Request, body: dict, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id)).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    secret = request.headers.get("X-Callback-Secret") or body.get("callback_secret")
    if not audit.callback_secret or secret != audit.callback_secret:
        raise HTTPException(status_code=403, detail="Invalid callback secret")

    error = body.get("error")
    if error:
        audit.status = AuditStatus.FAILED
        audit.error_message = str(error)
        audit.completed_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "failed"}

    report_markdown = body.get("report_markdown")
    if not report_markdown:
        vulns = body.get("vulnerabilities", [])
        if isinstance(vulns, list):
            report_markdown = _build_markdown_from_vulns(
                vulns,
                summary=body.get("summary", ""),
                metrics=body.get("metrics"),
            )
        else:
            report_markdown = "# Rapport d'Audit\n\n*Aucun détail disponible*"

    audit.report_markdown = report_markdown
    audit.status = AuditStatus.COMPLETED
    audit.completed_at = datetime.now(timezone.utc)

    vulns_dict = body.get("vulnerabilities")
    if isinstance(vulns_dict, dict):
        audit.vulnerabilities_critical = vulns_dict.get("critical", 0)
        audit.vulnerabilities_high = vulns_dict.get("high", 0)
        audit.vulnerabilities_medium = vulns_dict.get("medium", 0)
        audit.vulnerabilities_low = vulns_dict.get("low", 0)
        audit.vulnerabilities_info = vulns_dict.get("info", 0) or vulns_dict.get("informational", 0)
    else:
        metrics = body.get("metrics", {})
        if metrics.get("critical") is not None:
            audit.vulnerabilities_critical = metrics.get("critical", 0)
            audit.vulnerabilities_high = metrics.get("high", 0)
            audit.vulnerabilities_medium = metrics.get("medium", 0)
            audit.vulnerabilities_low = metrics.get("low", 0)
            audit.vulnerabilities_info = metrics.get("info", 0) or metrics.get("informational", 0)
        else:
            parsed = parse_vulnerabilities_from_markdown(report_markdown)
            audit.vulnerabilities_critical = parsed["critical"]
            audit.vulnerabilities_high = parsed["high"]
            audit.vulnerabilities_medium = parsed["medium"]
            audit.vulnerabilities_low = parsed["low"]
            audit.vulnerabilities_info = parsed["info"]

    docker_success = body.get("docker_success")
    if docker_success is not None:
        audit.docker_status = DockerStatus.SUCCESS if docker_success else DockerStatus.FAILED

    docker_validation = body.get("docker_validation")
    if isinstance(docker_validation, list) and docker_validation:
        validated = sum(1 for v in docker_validation if v.get("result") == "VALIDATED")
        failed = sum(1 for v in docker_validation if v.get("result") == "FAILED")
        not_tested = sum(1 for v in docker_validation if v.get("result") == "NOT-TESTED")
        if audit.docker_status == DockerStatus.NOT_STARTED and validated > 0:
            audit.docker_status = DockerStatus.SUCCESS

    # Store artifacts (PoCs, exploit tests)
    artifacts = body.get("artifacts")
    if isinstance(artifacts, dict):
        artifact_base = os.path.join(ARTIFACTS_DIR, str(audit.id))
        for rel_path, content in artifacts.items():
            target = os.path.join(artifact_base, rel_path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
        # Rewrite markdown links to use artifact endpoint
        if audit.report_markdown:
            base_url = f"/api/audits/{audit.id}/artifacts/"
            md = audit.report_markdown
            import re
            md = re.sub(r'(\[PoC\]\()poc/', r'\1' + base_url + 'poc/', md)
            md = re.sub(r'(\[Test\]\()exploit_tests/', r'\1' + base_url + 'exploit_tests/', md)
            md = re.sub(r'(\[Exploit Test\]\()exploit_tests/', r'\1' + base_url + 'exploit_tests/', md)
            audit.report_markdown = md

    db.commit()
    return {"status": "completed"}


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audit(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id), Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.code_file_path and os.path.exists(audit.code_file_path):
        os.remove(audit.code_file_path)

    db.delete(audit)
    db.commit()
