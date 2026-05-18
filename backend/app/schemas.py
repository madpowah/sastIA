from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models import AuditStatus, DockerStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    company: Optional[str] = None
    is_active: int
    is_admin: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuditCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    analysis_type: str = "code"
    docker_analysis_enabled: bool = False


class AuditResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    code_file_path: Optional[str] = None
    status: AuditStatus
    docker_status: DockerStatus
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_medium: int
    vulnerabilities_low: int
    vulnerabilities_info: int
    total_vulnerabilities: int
    report_markdown: Optional[str] = None
    error_message: Optional[str] = None
    analysis_type: str
    docker_analysis_enabled: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    id: UUID
    name: str
    status: AuditStatus
    docker_status: DockerStatus
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_medium: int
    vulnerabilities_low: int
    total_vulnerabilities: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    audit_id: UUID
    markdown: str
    pdf_url: Optional[str] = None


class DashboardStats(BaseModel):
    total_audits: int
    pending_audits: int
    completed_audits: int
    failed_audits: int
    total_critical: int
    total_high: int
    total_medium: int
    total_low: int
    recent_audits: list[AuditListResponse]


# ── Admin schemas ──────────────────────────────────────

class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    company: Optional[str] = None
    is_active: int
    is_admin: int
    created_at: datetime
    audit_count: int = 0

    class Config:
        from_attributes = True


class AdminAuditResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str = ""
    name: str
    status: AuditStatus
    docker_status: DockerStatus
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_medium: int
    vulnerabilities_low: int
    total_vulnerabilities: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AdminDashboardStats(BaseModel):
    total_users: int
    total_audits: int
    audits_by_status: dict[str, int]
    audits_by_day: list[dict]
    recent_audits: list[AdminAuditResponse]
    recent_users: list[AdminUserResponse]


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
