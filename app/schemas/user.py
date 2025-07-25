from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserRole(BaseModel):
    role_id: int
    role_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[TokenResponse] = None

# Session Management Schemas
# ===========================
# These schemas handle multi-device session management.
# Users can view all their active sessions, see device info,
# and revoke specific sessions or all sessions at once.

class SessionInfo(BaseModel):
    """
    Represents an active user session on a specific device.
    
    This contains all the information needed to display
    active sessions to the user and manage them.
    """
    id: int
    device_name: Optional[str] = None      # "iPhone 15", "MacBook Pro"
    ip_address: Optional[str] = None       # "192.168.1.100"
    user_agent: Optional[str] = None       # Browser/app identification
    issued_at: datetime                    # When session was created
    last_used: datetime                    # Last activity timestamp
    expires_at: datetime                   # When token expires
    is_current_session: bool = False       # Is this the current device?
    
    class Config:
        from_attributes = True

class ActiveSessionsResponse(BaseModel):
    """
    Response containing all active sessions for a user.
    
    This is returned when user wants to view all their
    active sessions across different devices.
    """
    success: bool
    message: str
    total_sessions: int
    current_session_id: Optional[int] = None
    sessions: list[SessionInfo]

class SessionActionResponse(BaseModel):
    """
    Response for session management actions (logout, revoke).
    
    Used for individual session logout or logout all devices.
    """
    success: bool
    message: str
    revoked_sessions: int = 0              # How many sessions were revoked

class DeviceInfoRequest(BaseModel):
    """
    Device information sent by client during login.
    
    This helps users identify their sessions later.
    """
    device_name: Optional[str] = None      # User-friendly device name
    user_agent: Optional[str] = None       # Technical device info

class LoginRequest(BaseModel):
    """
    Complete login request including credentials and optional device info.
    
    This is the main request model for the login endpoint, combining
    user credentials with device tracking information.
    """
    username: str                          # Username for authentication
    password: str                          # Password for authentication
    device_name: Optional[str] = None      # User-friendly device name
    user_agent: Optional[str] = None       # Technical device/browser info

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None 