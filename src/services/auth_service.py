"""Authentication service with database persistence."""

import logging
import uuid
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session as DBSession

from ..database.models import User, Session

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with database persistence."""

    def __init__(self, db: DBSession):
        """
        Initialize authentication service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        logger.info("Initialized AuthService with database persistence")

    def _generate_company_id(self) -> str:
        """Generate a unique company ID."""
        # Generate format: COMP-XXXXX (5 random chars)
        while True:
            random_part = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))
            company_id = f"COMP-{random_part}"

            # Check uniqueness in database
            existing = self.db.query(User).filter(User.company_id == company_id).first()
            if not existing:
                return company_id

    def register_user(self, email: str, password: str, company_name: str,
                      company_id: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user."""
        email_lower = email.lower()

        # Validate email uniqueness
        existing_user = self.db.query(User).filter(User.email == email_lower).first()
        if existing_user:
            return {"success": False, "error": "Email already in use"}

        # Validate company_id uniqueness if provided
        if company_id:
            existing_company = self.db.query(User).filter(User.company_id == company_id).first()
            if existing_company:
                return {"success": False, "error": "Company ID already taken"}
        else:
            company_id = self._generate_company_id()

        # Hash password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=email_lower,
            password_hash=password_hash,
            company_name=company_name,
            company_id=company_id
        )

        # Store user in database
        self.db.add(user)

        # Auto-login: Create session
        session = Session(
            session_id=secrets.token_urlsafe(32),
            user_id=user.id,
            expires_at=datetime.now() + timedelta(days=7)
        )
        self.db.add(session)

        # Commit transaction
        self.db.commit()

        logger.info(f"Registered new user: {email} with company: {company_name} (ID: {user.company_id})")

        return {
            "success": True,
            "user": user.to_dict(),
            "session_id": session.session_id
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and create session."""
        email_lower = email.lower()

        # Find user in database
        user = self.db.query(User).filter(User.email == email_lower).first()
        if not user:
            return {"success": False, "error": "Invalid credentials"}

        # Verify password
        password_bytes = password.encode('utf-8')
        password_hash_bytes = user.password_hash.encode('utf-8')

        if not bcrypt.checkpw(password_bytes, password_hash_bytes):
            return {"success": False, "error": "Invalid credentials"}

        # Clean up any existing sessions for this user
        self._cleanup_user_sessions(user.id)

        # Create new session
        session = Session(
            session_id=secrets.token_urlsafe(32),
            user_id=user.id,
            expires_at=datetime.now() + timedelta(days=7)
        )
        self.db.add(session)
        self.db.commit()

        logger.info(f"User logged in: {email}")

        return {
            "success": True,
            "user": user.to_dict(),
            "session_id": session.session_id
        }

    def logout(self, session_id: str) -> bool:
        """Logout user by removing session."""
        session = self.db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            user_id = session.user_id
            self.db.delete(session)
            self.db.commit()
            logger.info(f"User {user_id} logged out")
            return True
        return False

    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user from session ID."""
        if not session_id:
            return None

        # Query session from database
        session = self.db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            return None

        # Check session validity
        if not session.is_valid():
            self.db.delete(session)
            self.db.commit()
            return None

        # Refresh session (sliding window)
        session.refresh()
        self.db.commit()

        # Get user
        user = self.db.query(User).filter(User.id == session.user_id).first()
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def _cleanup_user_sessions(self, user_id: str):
        """Remove all sessions for a user."""
        self.db.query(Session).filter(Session.user_id == user_id).delete()
        # Note: commit will happen in the calling function

    def cleanup_expired_sessions(self):
        """Remove expired sessions (can be called periodically)."""
        expired_count = self.db.query(Session).filter(
            Session.expires_at < datetime.now()
        ).delete()

        if expired_count > 0:
            self.db.commit()
            logger.info(f"Cleaned up {expired_count} expired sessions")
