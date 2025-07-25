from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from .user import Base

class RefreshToken(Base):
    """
    RefreshToken Model for Session Management
    
    This table stores all active user sessions across different devices.
    Each refresh token represents one active session on one device.
    
    Key Features:
    - Multi-device support: Users can be logged in on multiple devices
    - Session tracking: We track device info, IP, and last activity
    - Granular control: Can revoke individual sessions or all sessions
    - Security: Stolen devices can be revoked without affecting other devices
    """
    __tablename__ = "refresh_tokens"
    
    # Primary key and user relationship
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token data
    token = Column(String, unique=True, nullable=False, index=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Integer, default=0)  # 0 = valid, 1 = revoked
    
    # Device and session tracking (NEW FIELDS)
    device_name = Column(String, nullable=True)  # "iPhone 15", "MacBook Pro", etc.
    ip_address = Column(String, nullable=True)   # IP address when token was created
    user_agent = Column(String, nullable=True)   # Browser/app info for identification
    last_used = Column(DateTime, default=datetime.utcnow)  # Track session activity

    # Relationship to User model
    user = relationship("User", backref="refresh_tokens") 