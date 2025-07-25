from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.core.config import settings
from app.api import user_router

# OAuth2 security scheme for Swagger UI
security = HTTPBearer()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Session Management API
    
    A comprehensive session management system with multi-device support.
    
    ### Features:
    - **User Authentication** with JWT tokens
    - **Multi-device Session Management** 
    - **Device Tracking** with IP addresses and user agents
    - **Granular Session Control** (logout specific devices)
    - **Security Features** (logout all devices, session monitoring)
    
    ### Authentication:
    1. **Login** with username/password to get access token
    2. **Use "Authorize" button** to set Bearer token for protected endpoints
    3. **Access protected endpoints** with Bearer authentication
    
    ### Protected Endpoints:
    Most session management endpoints require authentication.
    Click the "Authorize" button and enter your access token.
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User login and token management"
        },
        {
            "name": "Session Management", 
            "description": "Multi-device session control and monitoring"
        },
        {
            "name": "User Management",
            "description": "User CRUD operations and role management"
        }
    ]
)

@app.get("/", tags=["Health"])
def read_root():
    """
    Health check endpoint.
    
    Returns a simple welcome message to verify the API is running.
    """
    return {"message": "Welcome to the FastAPI Session Management backend!"}

app.include_router(user_router) 