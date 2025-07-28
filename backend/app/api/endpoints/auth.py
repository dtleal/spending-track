from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.google_oauth import google_oauth
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Register new user"""
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    
    if user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Login user"""
    # Try to find user in database
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has a password (not a Google OAuth user)
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google login. Please use 'Continue with Google' button.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/google/login")
def google_login():
    """Initiate Google OAuth login"""
    state = secrets.token_urlsafe(32)
    authorization_url = google_oauth.get_authorization_url(state=state)
    return {"authorization_url": authorization_url, "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    """Handle Google OAuth callback"""
    try:
        # Exchange code for token
        token_data = await google_oauth.exchange_code_for_token(code)
        
        # Verify ID token and get user info
        user_info = await google_oauth.verify_id_token(token_data["id_token"])
        
        # Check if user exists
        user = db.query(User).filter(
            (User.google_id == user_info["google_id"]) | 
            (User.email == user_info["email"])
        ).first()
        
        if user:
            # Update existing user with Google info if not already set
            if not user.google_id:
                user.google_id = user_info["google_id"]
                user.profile_picture = user_info.get("picture")
                db.commit()
                db.refresh(user)
        else:
            # Create new user
            user = User(
                email=user_info["email"],
                username=user_info["email"],  # Use email as username for Google users
                full_name=user_info["name"],
                google_id=user_info["google_id"],
                profile_picture=user_info.get("picture"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        redirect_url = f"{frontend_url}/auth/callback?token={access_token}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        redirect_url = f"{frontend_url}/auth/callback?error={str(e)}"
        return RedirectResponse(url=redirect_url)


@router.post("/google/token", response_model=Token)
async def google_token_login(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Login with Google ID token (for frontend use)"""
    try:
        # Verify ID token and get user info
        user_info = await google_oauth.verify_id_token(token)
        
        # Check if user exists
        user = db.query(User).filter(
            (User.google_id == user_info["google_id"]) | 
            (User.email == user_info["email"])
        ).first()
        
        if user:
            # Update existing user with Google info if not already set
            if not user.google_id:
                user.google_id = user_info["google_id"]
                user.profile_picture = user_info.get("picture")
                db.commit()
                db.refresh(user)
        else:
            # Create new user
            user = User(
                email=user_info["email"],
                username=user_info["email"],  # Use email as username for Google users
                full_name=user_info["name"],
                google_id=user_info["google_id"],
                profile_picture=user_info.get("picture"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(security.get_current_user)
) -> Any:
    """Get current user profile"""
    return current_user