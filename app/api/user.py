from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.user import UserCreate, UserRead, UserLogin, UserRole, TokenResponse, LoginResponse, ErrorResponse, SessionInfo, ActiveSessionsResponse, SessionActionResponse, DeviceInfoRequest, LoginRequest
from app.services.user_service import UserService
from app.models.user import Role, Module, Resource, Permission, RoleResourcePermission, User
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import os
from datetime import datetime, timedelta
import secrets
from app.models.refresh_token import RefreshToken
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

router = APIRouter(prefix="/users")

# Security scheme for Bearer token authentication
security = HTTPBearer()

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, secret_key: str = SECRET_KEY):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Enhanced helper functions for session management
# ================================================

def store_refresh_token(db: Session, user_id: int, token: str, expires_at: datetime, request: Request = None, device_info: DeviceInfoRequest = None):
    """
    Store refresh token with enhanced device tracking.
    
    This function creates a new session record with device information
    for multi-device session management and security tracking.
    
    Args:
        db: Database session
        user_id: ID of the user logging in
        token: Generated refresh token
        expires_at: When the token expires
        request: FastAPI request object (for IP address)
        device_info: Device information from client
    """
    # Extract device information
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "Unknown")
    
    device_name = device_info.device_name if device_info else "Unknown Device"
    if device_info and device_info.user_agent:
        user_agent = device_info.user_agent
    
    db_token = RefreshToken(
        user_id=user_id, 
        token=token, 
        expires_at=expires_at,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
        last_used=datetime.utcnow()
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def revoke_refresh_token(db: Session, token: str):
    """
    Revoke a specific refresh token (logout from one device).
    
    This marks a single session as revoked, effectively logging
    out the user from that specific device only.
    """
    db_token = db.query(RefreshToken).filter_by(token=token, revoked=0).first()
    if db_token:
        db_token.revoked = 1
        db.commit()
        return True
    return False

def revoke_all_user_tokens(db: Session, user_id: int, except_token: str = None):
    """
    Revoke all refresh tokens for a user (logout from all devices).
    
    This is used for "logout all devices" functionality.
    Optionally can preserve the current session.
    
    Args:
        user_id: User whose sessions to revoke
        except_token: Optional token to keep active (current session)
    
    Returns:
        Number of sessions revoked
    """
    query = db.query(RefreshToken).filter_by(user_id=user_id, revoked=0)
    
    if except_token:
        query = query.filter(RefreshToken.token != except_token)
    
    tokens = query.all()
    revoked_count = len(tokens)
    
    # Mark all matching tokens as revoked
    query.update({"revoked": 1})
    db.commit()
    
    return revoked_count

def revoke_session_by_id(db: Session, session_id: int, user_id: int):
    """
    Revoke a specific session by its ID.
    
    This allows users to logout from a specific device
    from their session management interface.
    
    Args:
        session_id: ID of the refresh token to revoke
        user_id: User ID (for security - ensures user owns the session)
    
    Returns:
        True if session was revoked, False if not found
    """
    db_token = db.query(RefreshToken).filter_by(
        id=session_id, 
        user_id=user_id, 
        revoked=0
    ).first()
    
    if db_token:
        db_token.revoked = 1
        db.commit()
        return True
    return False

def update_session_activity(db: Session, token: str):
    """
    Update the last_used timestamp for a session.
    
    This is called whenever a refresh token is used,
    helping users see which devices are actively being used.
    """
    db_token = db.query(RefreshToken).filter_by(token=token, revoked=0).first()
    if db_token:
        db_token.last_used = datetime.utcnow()
        db.commit()

def is_refresh_token_valid(db: Session, token: str):
    db_token = db.query(RefreshToken).filter_by(token=token, revoked=0).first()
    if db_token and db_token.expires_at > datetime.utcnow():
        # Update last used timestamp
        update_session_activity(db, token)
        return True
    return False

@router.post("/login", response_model=LoginResponse, tags=["Authentication"])
def login(login_request: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Enhanced login endpoint with device tracking.
    
    This endpoint authenticates users and creates tracked sessions
    with device information for security and session management.
    
    Request Body:
    {
        "username": "your_username",
        "password": "your_password",
        "device_name": "iPhone 15 Pro" (optional),
        "user_agent": "Mozilla/5.0..." (optional)
    }
    
    Returns:
        LoginResponse with access/refresh tokens and user info
    """
    try:
        user = authenticate_user(db, login_request.username, login_request.password)
        if not user:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        if not user.is_active:
            return LoginResponse(
                success=False,
                message="Account is deactivated. Please contact support."
            )
        
        # Create tokens
        access_token = create_access_token({"sub": user.username, "user_id": user.id, "role_id": user.role_id})
        refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})
        
        # Store refresh token in DB with device tracking
        payload = verify_token(refresh_token, REFRESH_SECRET_KEY)
        expires_at = datetime.utcfromtimestamp(payload["exp"]) if payload and "exp" in payload else datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Create device info from login request
        device_info = DeviceInfoRequest(
            device_name=login_request.device_name,
            user_agent=login_request.user_agent
        )
        store_refresh_token(db, user.id, refresh_token, expires_at, request, device_info)
        
        # Get user role
        role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role_id=user.role_id,
                is_active=user.is_active,
                created_at=user.created_at if hasattr(user, 'created_at') else None,
                updated_at=user.updated_at if hasattr(user, 'updated_at') else None
            )
        )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data=token_response
        )
        
    except Exception as e:
        return LoginResponse(
            success=False,
            message="An error occurred during login. Please try again."
        )

@router.post("/refresh", response_model=LoginResponse, tags=["Authentication"])
def refresh_token(refresh_token: str, request: Request, db: Session = Depends(get_db)):
    """
    Enhanced refresh endpoint with activity tracking.
    
    This endpoint refreshes access tokens and updates
    the session's last activity timestamp for tracking.
    """
    try:
        payload = verify_token(refresh_token, REFRESH_SECRET_KEY)
        if not payload or payload.get("type") != "refresh":
            return LoginResponse(
                success=False,
                message="Invalid refresh token"
            )
        
        # Check if refresh token is valid in DB
        if not is_refresh_token_valid(db, refresh_token):
            return LoginResponse(
                success=False,
                message="Refresh token is invalid or revoked"
            )
        
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not user.is_active:
            return LoginResponse(
                success=False,
                message="User not found or inactive"
            )
        
        # Revoke old refresh token
        revoke_refresh_token(db, refresh_token)
        
        # Create new tokens
        access_token = create_access_token({"sub": user.username, "user_id": user.id, "role_id": user.role_id})
        new_refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})
        
        # Store new refresh token in DB with same device info
        old_token = db.query(RefreshToken).filter_by(token=refresh_token).first()
        device_info = None
        if old_token:
            device_info = DeviceInfoRequest(
                device_name=old_token.device_name,
                user_agent=old_token.user_agent
            )
        
        payload_new = verify_token(new_refresh_token, REFRESH_SECRET_KEY)
        expires_at_new = datetime.utcfromtimestamp(payload_new["exp"]) if payload_new and "exp" in payload_new else datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        store_refresh_token(db, user.id, new_refresh_token, expires_at_new, request, device_info)
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role_id=user.role_id,
                is_active=user.is_active,
                created_at=user.created_at if hasattr(user, 'created_at') else None,
                updated_at=user.updated_at if hasattr(user, 'updated_at') else None
            )
        )
        
        return LoginResponse(
            success=True,
            message="Token refreshed successfully",
            data=token_response
        )
        
    except Exception as e:
        return LoginResponse(
            success=False,
            message="Failed to refresh token"
        )

# Secure logout endpoint
class LogoutRequest(BaseModel):
    refresh_token: str

@router.post("/logout", tags=["Authentication"])
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    """
    Revoke the provided refresh token in the database.
    """
    try:
        revoked = revoke_refresh_token(db, request.refresh_token)
        if revoked:
            return {"success": True, "message": "Logged out successfully"}
        else:
            return {"success": False, "message": "Refresh token not found or already revoked"}
    except SQLAlchemyError as e:
        return {"success": False, "message": "Database error during logout"}

@router.post("/", response_model=UserRead, tags=["User Management"])
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = UserService.get_user_by_email(db, user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_in.password)
    user_in_data = user_in.model_dump()
    user_in_data["hashed_password"] = hashed_password
    user_obj = User(
        username=user_in_data["username"],
        email=user_in_data["email"],
        full_name=user_in_data.get("full_name"),
        hashed_password=hashed_password,
        is_active=True,
        role_id=user_in_data.get("role_id")
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

# SESSION MANAGEMENT ENDPOINTS - Must be BEFORE /{user_id} route!
# ================================================================

@router.get("/sessions", response_model=ActiveSessionsResponse, tags=["Session Management"], dependencies=[Depends(security)])
def get_active_sessions(request: Request, db: Session = Depends(get_db)):
    """Get all active sessions for the authenticated user."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return ActiveSessionsResponse(
                success=False,
                message="Authentication required",
                total_sessions=0,
                sessions=[]
            )
        
        access_token = auth_header.split(" ")[1]
        payload = verify_token(access_token)
        
        if not payload:
            return ActiveSessionsResponse(
                success=False,
                message="Invalid access token",
                total_sessions=0,
                sessions=[]
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            return ActiveSessionsResponse(
                success=False,
                message="Invalid token payload",
                total_sessions=0,
                sessions=[]
            )
        
        # Get all active sessions for this user
        active_tokens = db.query(RefreshToken).filter_by(
            user_id=user_id,
            revoked=0
        ).filter(
            RefreshToken.expires_at > datetime.utcnow()
        ).order_by(RefreshToken.last_used.desc()).all()
        
        # Convert to SessionInfo objects
        sessions = []
        current_ip = request.client.host if request.client else None
        
        for token in active_tokens:
            # Try to determine if this is the current session
            is_current = (
                token.ip_address == current_ip and 
                abs((token.last_used - datetime.utcnow()).total_seconds()) < 300  # Within 5 minutes
            )
            
            session_info = SessionInfo(
                id=token.id,
                device_name=token.device_name or "Unknown Device",
                ip_address=token.ip_address,
                user_agent=token.user_agent,
                issued_at=token.issued_at,
                last_used=token.last_used,
                expires_at=token.expires_at,
                is_current_session=is_current
            )
            sessions.append(session_info)
        
        return ActiveSessionsResponse(
            success=True,
            message=f"Found {len(sessions)} active sessions",
            total_sessions=len(sessions),
            current_session_id=next((s.id for s in sessions if s.is_current_session), None),
            sessions=sessions
        )
        
    except Exception as e:
        return ActiveSessionsResponse(
            success=False,
            message="Error retrieving sessions",
            total_sessions=0,
            sessions=[]
        )

@router.delete("/sessions/all", response_model=SessionActionResponse, tags=["Session Management"], dependencies=[Depends(security)])
def logout_all_devices(request: Request, db: Session = Depends(get_db)):
    """Logout from ALL devices including current one."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return SessionActionResponse(
                success=False,
                message="Authentication required"
            )
        
        access_token = auth_header.split(" ")[1]
        payload = verify_token(access_token)
        
        if not payload:
            return SessionActionResponse(
                success=False,
                message="Invalid access token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            return SessionActionResponse(
                success=False,
                message="Invalid token payload"
            )
        
        # Revoke ALL sessions (no exceptions)
        revoked_count = revoke_all_user_tokens(db, user_id)
        
        return SessionActionResponse(
            success=True,
            message=f"Logged out from all {revoked_count} devices. Please login again.",
            revoked_sessions=revoked_count
        )
        
    except Exception as e:
        return SessionActionResponse(
            success=False,
            message="Error logging out from all devices"
        )

@router.delete("/sessions/{session_id}", response_model=SessionActionResponse, tags=["Session Management"], dependencies=[Depends(security)])
def revoke_session(session_id: int, request: Request, db: Session = Depends(get_db)):
    """Revoke a specific session (logout from specific device)."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return SessionActionResponse(
                success=False,
                message="Authentication required"
            )
        
        access_token = auth_header.split(" ")[1]
        payload = verify_token(access_token)
        
        if not payload:
            return SessionActionResponse(
                success=False,
                message="Invalid access token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            return SessionActionResponse(
                success=False,
                message="Invalid token payload"
            )
        
        # Revoke the specific session
        revoked = revoke_session_by_id(db, session_id, user_id)
        
        if revoked:
            return SessionActionResponse(
                success=True,
                message="Session revoked successfully",
                revoked_sessions=1
            )
        else:
            return SessionActionResponse(
                success=False,
                message="Session not found or already revoked"
            )
        
    except Exception as e:
        return SessionActionResponse(
            success=False,
            message="Error revoking session"
        )

@router.delete("/sessions", response_model=SessionActionResponse, tags=["Session Management"], dependencies=[Depends(security)])
def revoke_all_sessions(request: Request, db: Session = Depends(get_db)):
    """Revoke all sessions except current one (logout from all other devices)."""
    try:
        # Get user and current refresh token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return SessionActionResponse(
                success=False,
                message="Authentication required"
            )
        
        access_token = auth_header.split(" ")[1]
        payload = verify_token(access_token)
        
        if not payload:
            return SessionActionResponse(
                success=False,
                message="Invalid access token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            return SessionActionResponse(
                success=False,
                message="Invalid token payload"
            )
        
        # Find current session to preserve it
        current_ip = request.client.host if request.client else None
        current_session = None
        
        if current_ip:
            current_session = db.query(RefreshToken).filter_by(
                user_id=user_id,
                ip_address=current_ip,
                revoked=0
            ).order_by(RefreshToken.last_used.desc()).first()
        
        # Revoke all other sessions
        current_token = current_session.token if current_session else None
        revoked_count = revoke_all_user_tokens(db, user_id, current_token)
        
        return SessionActionResponse(
            success=True,
            message=f"Revoked {revoked_count} sessions. You remain logged in on this device.",
            revoked_sessions=revoked_count
        )
        
    except Exception as e:
        return SessionActionResponse(
            success=False,
            message="Error revoking sessions"
        )

@router.get("/{user_id}", response_model=UserRead, tags=["User Management"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# RBAC Endpoints
@router.get("/roles/", response_model=List[UserRole])
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return [UserRole(role_id=r.id, role_name=r.name) for r in roles]

@router.get("/modules/")
def list_modules(db: Session = Depends(get_db)):
    return db.query(Module).all()

@router.get("/resources/")
def list_resources(db: Session = Depends(get_db)):
    return db.query(Resource).all()

@router.get("/permissions/")
def list_permissions(db: Session = Depends(get_db)):
    return db.query(Permission).all()

@router.get("/role/{role_id}/permissions/")
def get_role_permissions(role_id: int, db: Session = Depends(get_db)):
    perms = db.query(RoleResourcePermission).filter(RoleResourcePermission.role_id == role_id).all()
    return [{
        "resource": db.query(Resource).get(p.resource_id).name,
        "permission": db.query(Permission).get(p.permission_id).name
    } for p in perms]

@router.post("/assign-role/{user_id}/{role_id}")
def assign_role(user_id: int, role_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    role = db.query(Role).get(role_id)
    if not user or not role:
        raise HTTPException(status_code=404, detail="User or Role not found")
    user.role_id = role_id
    db.commit()
    return {"message": f"Role '{role.name}' assigned to user '{user.username}'"} 