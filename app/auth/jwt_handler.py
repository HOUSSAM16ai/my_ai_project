"""
معالج JWT المتقدم (Advanced JWT Handler).

يوفر إدارة كاملة لـ JWT tokens مع دعم refresh tokens وrevocation.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """
    حمولة Token.
    
    Attributes:
        sub: معرف المستخدم
        exp: وقت الانتهاء
        iat: وقت الإصدار
        type: نوع Token (access/refresh)
        scopes: الصلاحيات
    """
    
    sub: str
    exp: datetime
    iat: datetime
    type: str = "access"
    scopes: list[str] = []


class JWTHandler:
    """
    معالج JWT المتقدم.
    
    الميزات:
    - Access tokens
    - Refresh tokens
    - Token revocation
    - Token rotation
    - Scope-based permissions
    
    المبادئ:
    - Secure: استخدام خوارزميات آمنة
    - Stateless: لا حاجة لتخزين tokens
    - Flexible: دعم scopes مخصصة
    - Observable: تسجيل جميع العمليات
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ) -> None:
        """
        تهيئة معالج JWT.
        
        Args:
            secret_key: المفتاح السري
            algorithm: خوارزمية التشفير
            access_token_expire_minutes: مدة صلاحية access token
            refresh_token_expire_days: مدة صلاحية refresh token
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # قائمة سوداء للـ tokens الملغاة
        self._revoked_tokens: set[str] = set()
        
        logger.info("✅ JWT Handler initialized")
    
    def create_access_token(
        self,
        subject: str,
        scopes: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        ينشئ access token.
        
        Args:
            subject: معرف المستخدم
            scopes: الصلاحيات
            expires_delta: مدة صلاحية مخصصة
            
        Returns:
            str: JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "scopes": scopes or [],
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"✅ Access token created for user: {subject}")
        
        return token
    
    def create_refresh_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        ينشئ refresh token.
        
        Args:
            subject: معرف المستخدم
            expires_delta: مدة صلاحية مخصصة
            
        Returns:
            str: JWT refresh token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"✅ Refresh token created for user: {subject}")
        
        return token
    
    def verify_token(self, token: str) -> TokenPayload | None:
        """
        يتحقق من صحة token.
        
        Args:
            token: JWT token
            
        Returns:
            TokenPayload | None: حمولة Token أو None
        """
        # التحقق من القائمة السوداء
        if token in self._revoked_tokens:
            logger.warning("⚠️ Attempted to use revoked token")
            return None
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            return TokenPayload(**payload)
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token has expired")
            return None
            
        except jwt.InvalidTokenError as exc:
            logger.warning(f"⚠️ Invalid token: {exc}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> str | None:
        """
        يجدد access token باستخدام refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            str | None: Access token جديد أو None
        """
        payload = self.verify_token(refresh_token)
        
        if not payload:
            return None
        
        if payload.type != "refresh":
            logger.warning("⚠️ Attempted to refresh with non-refresh token")
            return None
        
        # إنشاء access token جديد
        return self.create_access_token(payload.sub)
    
    def revoke_token(self, token: str) -> bool:
        """
        يلغي token.
        
        Args:
            token: JWT token
            
        Returns:
            bool: True إذا تم الإلغاء
        """
        self._revoked_tokens.add(token)
        logger.info("✅ Token revoked")
        return True
    
    def has_scope(self, token: str, required_scope: str) -> bool:
        """
        يتحقق من وجود صلاحية معينة.
        
        Args:
            token: JWT token
            required_scope: الصلاحية المطلوبة
            
        Returns:
            bool: True إذا كانت الصلاحية موجودة
        """
        payload = self.verify_token(token)
        
        if not payload:
            return False
        
        return required_scope in payload.scopes
    
    def get_token_info(self, token: str) -> dict[str, Any] | None:
        """
        يحصل على معلومات token.
        
        Args:
            token: JWT token
            
        Returns:
            dict[str, Any] | None: معلومات Token
        """
        payload = self.verify_token(token)
        
        if not payload:
            return None
        
        return {
            "subject": payload.sub,
            "type": payload.type,
            "scopes": payload.scopes,
            "issued_at": payload.iat.isoformat(),
            "expires_at": payload.exp.isoformat(),
            "is_expired": payload.exp < datetime.utcnow(),
            "is_revoked": token in self._revoked_tokens,
        }


# مثيل عام
_global_jwt_handler: JWTHandler | None = None


def get_jwt_handler(secret_key: str | None = None) -> JWTHandler:
    """
    يحصل على معالج JWT العام.
    
    Args:
        secret_key: المفتاح السري (مطلوب في أول استدعاء)
        
    Returns:
        JWTHandler: معالج JWT
    """
    global _global_jwt_handler
    
    if _global_jwt_handler is None:
        if not secret_key:
            raise ValueError("secret_key is required for first initialization")
        _global_jwt_handler = JWTHandler(secret_key)
    
    return _global_jwt_handler
