import uuid
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Audit, AuditStatus
from app.schemas import (
    AdminUserResponse,
    AdminAuditResponse,
    AdminDashboardStats,
    PaginatedResponse,
)
from app.auth import get_admin_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Helpers ────────────────────────────────────────────

def _audit_to_admin(audit: Audit) -> AdminAuditResponse:
    dur = None
    if audit.created_at and audit.completed_at:
        delta = audit.completed_at - audit.created_at
        dur = int(delta.total_seconds())
    return AdminAuditResponse(
        id=audit.id,
        user_id=audit.user_id,
        user_email=audit.user.email if audit.user else "",
        name=audit.name,
        status=audit.status,
        docker_status=audit.docker_status,
        vulnerabilities_critical=audit.vulnerabilities_critical,
        vulnerabilities_high=audit.vulnerabilities_high,
        vulnerabilities_medium=audit.vulnerabilities_medium,
        vulnerabilities_low=audit.vulnerabilities_low,
        total_vulnerabilities=audit.total_vulnerabilities,
        created_at=audit.created_at,
        completed_at=audit.completed_at,
        duration_seconds=dur,
        error_message=audit.error_message,
    )


# ── Dashboard ──────────────────────────────────────────

@router.get("/dashboard", response_model=AdminDashboardStats)
def admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_audits = db.query(func.count(Audit.id)).scalar() or 0

    by_status = (
        db.query(Audit.status, func.count(Audit.id))
        .group_by(Audit.status)
        .all()
    )
    audits_by_status = {s: c for s, c in by_status}

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    by_day = (
        db.query(
            func.date(Audit.created_at).label("day"),
            func.count(Audit.id),
        )
        .filter(Audit.created_at >= seven_days_ago)
        .group_by(func.date(Audit.created_at))
        .order_by(func.date(Audit.created_at))
        .all()
    )
    audits_by_day = [{"day": str(d), "count": c} for d, c in by_day]

    recent_audits_q = (
        db.query(Audit)
        .order_by(Audit.created_at.desc())
        .limit(10)
        .all()
    )
    recent_users_q = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(10)
        .all()
    )

    return AdminDashboardStats(
        total_users=total_users,
        total_audits=total_audits,
        audits_by_status=audits_by_status,
        audits_by_day=audits_by_day,
        recent_audits=[_audit_to_admin(a) for a in recent_audits_q],
        recent_users=[
            AdminUserResponse.model_validate(u) for u in recent_users_q
        ],
    )


# ── Users ──────────────────────────────────────────────

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: str = Query("", description="Search by email or name"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        query = query.filter(
            User.email.ilike(f"%{q}%") | User.full_name.ilike(f"%{q}%")
        )
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()

    items = []
    for u in users:
        audit_count = db.query(func.count(Audit.id)).filter(Audit.user_id == u.id).scalar() or 0
        ur = AdminUserResponse.model_validate(u)
        ur.audit_count = audit_count
        items.append(ur)

    return PaginatedResponse(items=[i.model_dump() for i in items], total=total, page=page, size=size)


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    audits = (
        db.query(Audit)
        .filter(Audit.user_id == user_id)
        .order_by(Audit.created_at.desc())
        .all()
    )
    audit_count = len(audits)
    ur = AdminUserResponse.model_validate(user)
    ur.audit_count = audit_count
    return {
        "user": ur.model_dump(),
        "audits": [_audit_to_admin(a).model_dump() for a in audits],
    }


@router.patch("/users/{user_id}")
def update_user(
    user_id: uuid.UUID,
    is_active: int | None = None,
    is_admin: int | None = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if is_active is not None:
        user.is_active = is_active
    if is_admin is not None:
        user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)


# ── Audits ─────────────────────────────────────────────

@router.get("/audits")
def list_audits(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: str = Query("", alias="status"),
    user_id: str = Query("", alias="user_id"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(Audit).join(User, Audit.user_id == User.id)
    if status_filter:
        query = query.filter(Audit.status == status_filter)
    if user_id:
        try:
            uid = uuid.UUID(user_id)
            query = query.filter(Audit.user_id == uid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id UUID")
    total = query.count()
    audits = query.order_by(Audit.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(
        items=[_audit_to_admin(a).model_dump() for a in audits],
        total=total,
        page=page,
        size=size,
    )


@router.get("/audits/{audit_id}")
def get_audit_detail(
    audit_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {
        "audit": _audit_to_admin(audit).model_dump(),
        "report_markdown": audit.report_markdown,
        "error_message": audit.error_message,
    }


@router.get("/audits/{audit_id}/log")
def get_audit_log(
    audit_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
):
    worker_url = f"{settings.WORKER_URL}/log/{audit_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(worker_url)
            if resp.status_code == 404:
                return {"log": f"No log found for audit {audit_id} on worker."}
            resp.raise_for_status()
            return {"log": resp.text}
    except httpx.RequestError as e:
        return {"log": f"Worker unreachable: {e}"}


@router.post("/audits/{audit_id}/retry")
def retry_audit(
    audit_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status not in (AuditStatus.FAILED, AuditStatus.PENDING):
        raise HTTPException(
            status_code=400,
            detail="Only FAILED or PENDING audits can be retried",
        )

    audit.status = AuditStatus.PENDING
    audit.error_message = None
    audit.report_markdown = None
    audit.completed_at = None
    audit.vulnerabilities_critical = 0
    audit.vulnerabilities_high = 0
    audit.vulnerabilities_medium = 0
    audit.vulnerabilities_low = 0
    db.commit()
    db.refresh(audit)

    from app.routers.audits import _dispatch_to_worker

    _dispatch_to_worker(audit, audit.user)
    return {"status": "dispatched", "audit_id": str(audit.id)}
