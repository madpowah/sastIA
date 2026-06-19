import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AuditStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING_CODE = "analyzing_code"
    ANALYZING_DOCKER = "analyzing_docker"
    COMPLETED = "completed"
    FAILED = "failed"


class DockerStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    must_change_password = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    audits = relationship("Audit", back_populates="user", cascade="all, delete-orphan")


class Audit(Base):
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    callback_secret = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repo_url = Column(String(1024), nullable=True)
    code_file_path = Column(String(1024), nullable=True)
    status = Column(String(50), default=AuditStatus.PENDING.value, nullable=False)
    docker_status = Column(String(50), default=DockerStatus.NOT_STARTED.value, nullable=False)
    vulnerabilities_critical = Column(Integer, default=0)
    vulnerabilities_high = Column(Integer, default=0)
    vulnerabilities_medium = Column(Integer, default=0)
    vulnerabilities_low = Column(Integer, default=0)
    vulnerabilities_info = Column(Integer, default=0)
    report_markdown = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    analysis_type = Column(String(50), default="code")
    docker_analysis_enabled = Column(Integer, default=0)
    model_id = Column(String(255), nullable=True)
    report_language = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="audits")

    @property
    def total_vulnerabilities(self) -> int:
        return (self.vulnerabilities_critical + self.vulnerabilities_high +
                self.vulnerabilities_medium + self.vulnerabilities_low +
                self.vulnerabilities_info)


class Provider(Base):
    __tablename__ = "providers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    base_url = Column(String(1024), nullable=False)
    api_key = Column(Text, nullable=True)
    models_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


class AvailableModel(Base):
    __tablename__ = "available_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    enabled = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))



