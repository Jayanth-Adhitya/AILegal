"""Authentication service with database persistence."""

import logging
import uuid
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session as DBSession

from ..database.models import User, Session, PasswordResetToken

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

    # ===== Password Reset Methods =====

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request a password reset for a user.

        Args:
            email: User's email address

        Returns:
            Dictionary with success status and token (if user exists)
        """
        email_lower = email.lower()

        # Find user in database
        user = self.db.query(User).filter(User.email == email_lower).first()

        # Always return success to prevent email enumeration
        # But only create token and return it if user exists
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return {"success": True, "token": None, "user_exists": False}

        # Check rate limiting (3 requests per hour)
        if not self._check_reset_rate_limit(user.id):
            logger.warning(f"Password reset rate limit exceeded for user: {email}")
            return {"success": True, "token": None, "user_exists": True, "rate_limited": True}

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Hash token for storage
        token_bytes = token.encode('utf-8')
        salt = bcrypt.gensalt()
        token_hash = bcrypt.hashpw(token_bytes, salt).decode('utf-8')

        # Create password reset token
        reset_token = PasswordResetToken(
            id=str(uuid.uuid4()),
            token_hash=token_hash,
            user_id=user.id,
            expires_at=datetime.now() + timedelta(minutes=15),
            request_count=1,
            window_start=datetime.now()
        )

        self.db.add(reset_token)
        self.db.commit()

        logger.info(f"Password reset token created for user: {email}")

        return {
            "success": True,
            "token": token,  # Return unhashed token to send via email
            "user_exists": True,
            "rate_limited": False
        }

    def _check_reset_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded password reset rate limit.

        Args:
            user_id: User ID

        Returns:
            True if within rate limit, False if exceeded
        """
        # Get all reset tokens for this user in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)

        recent_tokens = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.created_at >= one_hour_ago
        ).all()

        # Count total requests (each token has request_count)
        total_requests = sum(token.request_count for token in recent_tokens)

        # Rate limit: 3 requests per hour
        return total_requests < 3

    def validate_reset_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a password reset token.

        Args:
            token: The reset token from the URL

        Returns:
            Dictionary with validation result and user info
        """
        # Hash the provided token to compare with stored hashes
        token_bytes = token.encode('utf-8')

        # Find all non-expired, non-used tokens
        valid_tokens = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at > datetime.now(),
            PasswordResetToken.used_at.is_(None)
        ).all()

        # Check each token hash
        for reset_token in valid_tokens:
            token_hash_bytes = reset_token.token_hash.encode('utf-8')
            if bcrypt.checkpw(token_bytes, token_hash_bytes):
                # Token found and valid
                user = self.db.query(User).filter(User.id == reset_token.user_id).first()
                return {
                    "valid": True,
                    "token_id": reset_token.id,
                    "user_id": user.id,
                    "email": user.email
                }

        # Token not found or invalid
        return {"valid": False, "error": "Invalid or expired reset token"}

    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset user password using a valid token.

        Args:
            token: The reset token from the URL
            new_password: New password to set

        Returns:
            Dictionary with success status and any errors
        """
        # Validate password strength
        if len(new_password) < 8:
            return {
                "success": False,
                "error": "Password must be at least 8 characters long"
            }

        # Validate the token
        validation_result = self.validate_reset_token(token)
        if not validation_result.get("valid"):
            return {
                "success": False,
                "error": validation_result.get("error", "Invalid token")
            }

        user_id = validation_result["user_id"]
        token_id = validation_result["token_id"]

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}

        # Hash new password
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Update user password
        user.password_hash = password_hash
        user.updated_at = datetime.now()

        # Mark token as used
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.id == token_id
        ).first()
        if reset_token:
            reset_token.mark_as_used()

        # Invalidate all existing sessions for security
        self._cleanup_user_sessions(user_id)

        # Commit all changes
        self.db.commit()

        logger.info(f"Password reset completed for user: {user.email}")

        return {
            "success": True,
            "user": user.to_dict()
        }

    def cleanup_expired_reset_tokens(self) -> int:
        """
        Remove expired password reset tokens (older than 24 hours).

        Returns:
            Number of tokens cleaned up
        """
        # Delete tokens older than 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)

        expired_count = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.created_at < cutoff_time
        ).delete()

        if expired_count > 0:
            self.db.commit()
            logger.info(f"Cleaned up {expired_count} expired password reset tokens")

        return expired_count
