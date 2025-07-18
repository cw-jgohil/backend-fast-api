from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.user import UserCreate, UserRead, UserLogin, UserRole, TokenResponse, LoginResponse, ErrorResponse
from app.services.user_service import UserService
from app.models.user import Role, Module, Resource, Permission, RoleResourcePermission, User
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import os
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/users", tags=["users"])

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

@router.post("/login", response_model=LoginResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, login_data.username, login_data.password)
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

@router.post("/refresh", response_model=LoginResponse)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = verify_token(refresh_token, REFRESH_SECRET_KEY)
        if not payload or payload.get("type") != "refresh":
            return LoginResponse(
                success=False,
                message="Invalid refresh token"
            )
        
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not user.is_active:
            return LoginResponse(
                success=False,
                message="User not found or inactive"
            )
        
        # Create new tokens
        access_token = create_access_token({"sub": user.username, "user_id": user.id, "role_id": user.role_id})
        new_refresh_token = create_refresh_token({"sub": user.username, "user_id": user.id})
        
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

@router.post("/", response_model=UserRead)
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

@router.get("/{user_id}", response_model=UserRead)
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