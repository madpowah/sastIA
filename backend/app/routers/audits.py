import os
import re
import uuid
import shutil
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import User, Audit, AuditStatus, DockerStatus
from app.schemas import AuditCreate, AuditResponse, AuditListResponse, DashboardStats
from app.auth import get_current_user
from app.config import get_settings


def parse_vulnerabilities_from_markdown(markdown: str) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    table_pattern = re.compile(
        r"(?:critique|critical).*?[|]\s*(\d+)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    for severity, keyword in [("critical", r"critiqu"), ("high", r"[ée]lev"), ("medium", r"moyen"), ("low", r"basse")]:
        pattern = rf"{keyword}.*?[|]\s*(\d+)\s*(?:\||$)"
        match = re.search(pattern, markdown, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            counts[severity] = int(match.group(1))
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
        status=AuditStatus.PENDING,
        docker_status=DockerStatus.NOT_STARTED if docker_analysis_enabled else DockerStatus.NOT_STARTED,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    if code_file:
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id), str(audit.id))
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(code_file.filename or "code.zip")[1]
        file_path = os.path.join(upload_dir, f"code{file_ext}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(code_file.file, f)
        audit.code_file_path = file_path
        db.commit()
        db.refresh(audit)

    return AuditResponse.model_validate(audit)


@router.get("/{audit_id}", response_model=AuditResponse)
def get_audit(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id, Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return AuditResponse.model_validate(audit)


@router.post("/{audit_id}/start", response_model=AuditResponse)
def start_analysis(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id, Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != AuditStatus.PENDING:
        raise HTTPException(status_code=400, detail="Audit already started")

    audit.status = AuditStatus.ANALYZING_CODE
    db.commit()
    db.refresh(audit)

    # Send to worker asynchronously
    _dispatch_to_worker(audit, current_user)

    return AuditResponse.model_validate(audit)


def _dispatch_to_worker(audit: Audit, user: User):
    worker_url = f"{settings.WORKER_URL}/analyze"
    callback_url = f"{settings.CODE_DOWNLOAD_BASE_URL}/api/audits/{audit.id}/callback"
    download_base = f"{settings.CODE_DOWNLOAD_BASE_URL}/api/audits/{audit.id}/download"

    payload = {
        "audit_id": str(audit.id),
        "user_id": str(user.id),
        "callback_url": callback_url,
        "repo_url": audit.repo_url,
        "code_path": download_base if audit.code_file_path else None,
        "analysis_type": audit.analysis_type,
        "docker_analysis": bool(audit.docker_analysis_enabled),
        "model_id": audit.model_id,
        "backend_base_url": settings.CODE_DOWNLOAD_BASE_URL,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(worker_url, json=payload)
    except Exception as e:
        print(f"[backend] Failed to dispatch to worker: {e}")


@router.get("/{audit_id}/download", include_in_schema=False)
def download_code(audit_id: uuid.UUID, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit or not audit.code_file_path:
        raise HTTPException(status_code=404, detail="No code file available")

    if not os.path.exists(audit.code_file_path):
        raise HTTPException(status_code=404, detail="Code file not found on disk")

    return FileResponse(
        audit.code_file_path,
        filename=os.path.basename(audit.code_file_path),
    )


class CallbackBody(BaseModel):
    report_markdown: str
    vulnerabilities: Optional[dict] = None
    docker_success: Optional[bool] = None
    error: Optional[str] = None


@router.post("/{audit_id}/callback", include_in_schema=False)
def analysis_callback(audit_id: uuid.UUID, body: CallbackBody, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if body.error:
        audit.status = AuditStatus.FAILED
        audit.error_message = body.error
        audit.completed_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "failed"}

    audit.report_markdown = body.report_markdown
    audit.status = AuditStatus.COMPLETED
    audit.completed_at = datetime.now(timezone.utc)

    if body.vulnerabilities:
        audit.vulnerabilities_critical = body.vulnerabilities.get("critical", 0)
        audit.vulnerabilities_high = body.vulnerabilities.get("high", 0)
        audit.vulnerabilities_medium = body.vulnerabilities.get("medium", 0)
        audit.vulnerabilities_low = body.vulnerabilities.get("low", 0)
    else:
        parsed = parse_vulnerabilities_from_markdown(body.report_markdown)
        audit.vulnerabilities_critical = parsed["critical"]
        audit.vulnerabilities_high = parsed["high"]
        audit.vulnerabilities_medium = parsed["medium"]
        audit.vulnerabilities_low = parsed["low"]

    if body.docker_success is not None:
        audit.docker_status = DockerStatus.SUCCESS if body.docker_success else DockerStatus.FAILED

    db.commit()
    return {"status": "completed"}


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audit(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id, Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.code_file_path and os.path.exists(audit.code_file_path):
        os.remove(audit.code_file_path)

    db.delete(audit)
    db.commit()
