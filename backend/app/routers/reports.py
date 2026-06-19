import os
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Audit, AuditStatus
from app.schemas import ReportResponse
from app.auth import get_current_user
from app.services.report import generate_pdf

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/{audit_id}", response_model=ReportResponse)
def get_report(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id), Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if not audit.report_markdown:
        raise HTTPException(status_code=404, detail="Report not yet generated")
    if audit.status != AuditStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Audit not yet completed")

    return ReportResponse(
        audit_id=audit.id,
        markdown=audit.report_markdown,
        pdf_url=f"/api/reports/{audit.id}/pdf",
    )


@router.get("/{audit_id}/pdf")
def download_pdf(audit_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == str(audit_id), Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if not audit.report_markdown:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    pdf_path = os.path.join(os.path.dirname(audit.code_file_path or "/tmp"), f"report_{audit.id}.pdf") if audit.code_file_path else f"/tmp/report_{audit.id}.pdf"
    generate_pdf(audit.report_markdown, pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"rapport-audit-{audit.name}.pdf".replace(" ", "-").lower(),
    )
