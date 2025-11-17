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


# ===== Document Editor Models =====

class Document(Base):
    """Collaborative document model for contract editing."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    negotiation_id = Column(String, ForeignKey("negotiations.id", ondelete="CASCADE"), nullable=True, index=True)
    analysis_job_id = Column(String, ForeignKey("analysis_jobs.job_id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, index=True)
    yjs_state_vector = Column(Text, nullable=True)  # Store as base64-encoded string
    status = Column(String, default='draft', nullable=False)  # draft, under_review, finalized
    import_source = Column(String, nullable=True)  # NULL, 'original', 'ai_redlined'

    # DOCX file storage fields
    original_file_path = Column(String, nullable=True)  # Path to original DOCX file
    original_file_name = Column(String, nullable=True)  # Original filename
    original_file_size = Column(Integer, nullable=True)  # File size in bytes
    lexical_state = Column(Text, nullable=True)  # Lexical JSON editor state

    # Relationships
    negotiation = relationship("Negotiation", foreign_keys=[negotiation_id])
    analysis_job = relationship("AnalysisJob", foreign_keys=[analysis_job_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version_number.desc()")
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan", order_by="DocumentComment.created_at")
    changes = relationship("DocumentChange", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChange.created_at")
    collaborators = relationship("DocumentCollaborator", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert document to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "negotiation_id": self.negotiation_id,
            "analysis_job_id": self.analysis_job_id,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "lexical_state": self.lexical_state,  # Initial content (HTML or Lexical JSON)
            "yjs_state_vector": self.yjs_state_vector,  # Yjs binary data (base64)
            "status": self.status,
            "import_source": self.import_source,
            "original_file_path": self.original_file_path,  # Path to DOCX file (for SuperDoc)
            "original_file_name": self.original_file_name,
            "original_file_size": self.original_file_size,
            "created_by": self.created_by.to_dict() if self.created_by else None,
        }


class DocumentVersion(Base):
    """Document version snapshot."""

    __tablename__ = "document_versions"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    yjs_state_vector = Column(Text, nullable=False)  # Full Yjs state at this version
    snapshot_data = Column(Text, nullable=False)  # JSON metadata
    created_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    def to_dict(self):
        """Convert version to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "created_by": self.created_by.to_dict() if self.created_by else None,
        }


class DocumentComment(Base):
    """Inline comment on document text."""

    __tablename__ = "document_comments"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id = Column(String, ForeignKey("document_comments.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    text_range_start = Column(Integer, nullable=False)
    text_range_end = Column(Integer, nullable=False)
    status = Column(String, default='open', nullable=False)  # open, resolved
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="comments")
    parent_comment = relationship("DocumentComment", remote_side=[id], backref="replies")
    user = relationship("User", foreign_keys=[user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])

    def to_dict(self):
        """Convert comment to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "parent_comment_id": self.parent_comment_id,
            "user_id": self.user_id,
            "content": self.content,
            "text_range_start": self.text_range_start,
            "text_range_end": self.text_range_end,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "user": self.user.to_dict() if self.user else None,
        }


class DocumentChange(Base):
    """Track changes audit trail."""

    __tablename__ = "document_changes"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    change_type = Column(String, nullable=False)  # insert, delete, format
    position = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    change_metadata = Column(Text, nullable=True)  # JSON (renamed from metadata to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejected_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="changes")
    user = relationship("User", foreign_keys=[user_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_user_id])

    def to_dict(self):
        """Convert change to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "change_type": self.change_type,
            "position": self.position,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "user": self.user.to_dict() if self.user else None,
        }


class DocumentCollaborator(Base):
    """Document access control."""

    __tablename__ = "document_collaborators"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String, default='edit', nullable=False)  # edit only for MVP
    added_by_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id])
    added_by = relationship("User", foreign_keys=[added_by_user_id])

    def to_dict(self):
        """Convert collaborator to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "permission": self.permission,
            "added_at": self.added_at.isoformat(),
            "user": self.user.to_dict() if self.user else None,
        }


# Create indexes for common queries
Index('idx_sessions_user_expires', Session.user_id, Session.expires_at)
Index('idx_jobs_user_created', AnalysisJob.user_id, AnalysisJob.created_at.desc())
Index('idx_negotiations_status', Negotiation.status, Negotiation.created_at.desc())
Index('idx_messages_negotiation_created', NegotiationMessage.negotiation_id, NegotiationMessage.created_at)

# Document indexes
Index('idx_documents_created_by', Document.created_by_user_id, Document.created_at.desc())
Index('idx_document_versions_doc_version', DocumentVersion.document_id, DocumentVersion.version_number)
Index('idx_document_comments_doc', DocumentComment.document_id, DocumentComment.created_at)
Index('idx_document_changes_doc', DocumentChange.document_id, DocumentChange.created_at)
Index('idx_document_collaborators_doc_user', DocumentCollaborator.document_id, DocumentCollaborator.user_id)
