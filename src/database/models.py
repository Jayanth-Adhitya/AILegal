"""SQLAlchemy database models for persistent storage."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, Boolean, Integer
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    company_id = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("AnalysisJob", back_populates="user", cascade="all, delete-orphan")
    initiated_negotiations = relationship("Negotiation", foreign_keys="[Negotiation.initiator_user_id]", back_populates="initiator", cascade="all, delete-orphan")
    received_negotiations = relationship("Negotiation", foreign_keys="[Negotiation.receiver_user_id]", back_populates="receiver", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert user to dictionary (without password)."""
        return {
            "id": self.id,
            "email": self.email,
            "company_name": self.company_name,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat()
        }


class Session(Base):
    """User session model for authentication."""

    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_activity = Column(DateTime, default=datetime.now, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Relationship
    user = relationship("User", back_populates="sessions")

    def is_valid(self) -> bool:
        """Check if session is still valid."""
        return datetime.now() < self.expires_at

    def refresh(self):
        """Refresh session with sliding window."""
        from datetime import timedelta
        self.last_activity = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=7)


class AnalysisJob(Base):
    """Contract analysis job model."""

    __tablename__ = "analysis_jobs"

    job_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    upload_path = Column(String, nullable=False)
    output_path = Column(String)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    result_json = Column(Text)  # Store full analysis results as JSON
    error = Column(Text)

    # Relationship
    user = relationship("User", back_populates="jobs")

    def to_dict(self):
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "upload_path": self.upload_path,
            "output_path": self.output_path,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error
        }


class Negotiation(Base):
    """Contract negotiation between two parties."""

    __tablename__ = "negotiations"

    id = Column(String, primary_key=True)
    contract_name = Column(String, nullable=False)
    contract_job_id = Column(String, ForeignKey("analysis_jobs.job_id", ondelete="SET NULL"), nullable=True)

    # Parties
    initiator_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status: pending, active, completed, rejected, cancelled
    status = Column(String, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    initiator = relationship("User", foreign_keys=[initiator_user_id], back_populates="initiated_negotiations")
    receiver = relationship("User", foreign_keys=[receiver_user_id], back_populates="received_negotiations")
    contract_job = relationship("AnalysisJob", foreign_keys=[contract_job_id])
    messages = relationship("NegotiationMessage", back_populates="negotiation", cascade="all, delete-orphan", order_by="NegotiationMessage.created_at")

    def to_dict(self):
        """Convert negotiation to dictionary."""
        return {
            "id": self.id,
            "contract_name": self.contract_name,
            "contract_job_id": self.contract_job_id,
            "initiator_user_id": self.initiator_user_id,
            "receiver_user_id": self.receiver_user_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "initiator": self.initiator.to_dict() if self.initiator else None,
            "receiver": self.receiver.to_dict() if self.receiver else None,
        }


class NegotiationMessage(Base):
    """Messages exchanged during negotiation."""

    __tablename__ = "negotiation_messages"

    id = Column(String, primary_key=True)
    negotiation_id = Column(String, ForeignKey("negotiations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sender identification
    sender_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    sender_type = Column(String, nullable=False)  # "user", "system"

    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # "text", "system"

    # Metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    negotiation = relationship("Negotiation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_user_id])

    def to_dict(self):
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "negotiation_id": self.negotiation_id,
            "sender_user_id": self.sender_user_id,
            "sender_type": self.sender_type,
            "content": self.content,
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sender": self.sender.to_dict() if self.sender else None,
        }


# Create indexes for common queries
Index('idx_sessions_user_expires', Session.user_id, Session.expires_at)
Index('idx_jobs_user_created', AnalysisJob.user_id, AnalysisJob.created_at.desc())
Index('idx_negotiations_status', Negotiation.status, Negotiation.created_at.desc())
Index('idx_messages_negotiation_created', NegotiationMessage.negotiation_id, NegotiationMessage.created_at)
