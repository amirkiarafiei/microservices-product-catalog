import logging
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)
security = HTTPBearer()

class UserContext(BaseModel):
    user_id: str
    username: str
    role: str

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    # In a real microservice, you'd pass the public key via env or fetch it once
    public_key: str = None,
    algorithm: str = "RS256"
) -> UserContext:
    """
    FastAPI dependency to validate JWT token and return user context.

    Args:
        token: The bearer token from the request.
        public_key: The RSA public key for verification.
        algorithm: The signing algorithm.

    Returns:
        UserContext object with user details.
    """
    if not public_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Public key for JWT verification not configured"
        )

    try:
        payload = jwt.decode(token.credentials, public_key, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")

        if user_id is None or username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return UserContext(user_id=user_id, username=username, role=role)

    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class RoleChecker:
    """
    Dependency to check if the current user has required roles.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserContext = Depends(get_current_user)) -> UserContext:
        if user.role not in self.allowed_roles:
            logger.warning(f"User {user.username} with role {user.role} attempted unauthorized access")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
