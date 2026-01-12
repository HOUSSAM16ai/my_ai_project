"""
مزود بروتوكول OAuth2 (OAuth2 Provider).

يسمح هذا المكون للنظام بالعمل كمزود هوية (Identity Provider - IdP)
باستخدام بروتوكول OAuth2 / OpenID Connect.

الميزات:
- دعم Authorization Code Flow (PKCE).
- دعم Client Credentials Flow (للخدمات).
- إدارة العملاء (Clients).
"""

from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status

GrantType = Literal["authorization_code", "client_credentials", "refresh_token"]


@dataclass
class OAuth2Client:
    """تعريف تطبيق عميل (Client Application)."""

    client_id: str
    client_secret_hash: str
    redirect_uris: list[str]
    allowed_grant_types: list[GrantType]
    name: str
    is_confidential: bool = True


@dataclass
class ClientRegistration:
    """نتيجة تسجيل العميل (تحتوي على السر الخام)."""

    client: OAuth2Client
    raw_secret: str | None


class OAuth2Provider:
    """
    مزود خدمة OAuth2.

    ملاحظة: يستخدم التخزين في الذاكرة حالياً كمرجع للتنفيذ (Reference Implementation).
    في بيئة الإنتاج، يجب استبدال `self._clients` و `self._auth_codes` بمستودع بيانات (Repository).
    """

    def __init__(self) -> None:
        # In a real app, this would be a database repository
        self._clients: dict[str, OAuth2Client] = {}
        self._auth_codes: dict[str, dict] = {}

    def register_client(
        self,
        name: str,
        redirect_uris: list[str],
        grant_types: list[GrantType] | None = None,
        is_confidential: bool = True,
    ) -> ClientRegistration:
        """
        تسجيل عميل جديد وإرجاع السر الخام.

        Returns:
            ClientRegistration: كائن يحتوي على بيانات العميل والسر الخام (يجب عرضه مرة واحدة).
        """
        import hashlib
        import secrets

        client_id = secrets.token_urlsafe(16)
        resolved_grant_types = grant_types or ["authorization_code"]
        client_secret = None
        secret_hash = "none"

        if is_confidential:
            client_secret = secrets.token_urlsafe(32)
            secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

        client = OAuth2Client(
            client_id=client_id,
            client_secret_hash=secret_hash,
            redirect_uris=redirect_uris,
            allowed_grant_types=resolved_grant_types,
            name=name,
            is_confidential=is_confidential,
        )
        self._clients[client_id] = client

        return ClientRegistration(client=client, raw_secret=client_secret)

    def validate_client(self, client_id: str, client_secret: str | None = None) -> OAuth2Client:
        """التحقق من صحة العميل."""
        import hashlib

        client = self._clients.get(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client_id"
            )

        if client.is_confidential:
            if not client_secret:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Client secret required"
                )

            input_hash = hashlib.sha256(client_secret.encode()).hexdigest()
            if input_hash != client.client_secret_hash:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client_secret"
                )

        return client

    def create_authorization_code(
        self,
        client_id: str,
        user_id: str,
        scope: str,
        redirect_uri: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        """إنشاء رمز ترخيص (Auth Code)."""
        import secrets

        client = self._clients.get(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client_id")

        if redirect_uri not in client.redirect_uris:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect_uri"
            )

        code = secrets.token_urlsafe(32)
        self._auth_codes[code] = {
            "client_id": client_id,
            "user_id": user_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }
        return code

    def exchange_code_for_token(
        self, code: str, client_id: str, redirect_uri: str, code_verifier: str | None = None
    ) -> dict:
        """استبدال الرمز بالتوكن."""
        data = self._auth_codes.get(code)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code"
            )

        if data["client_id"] != client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client for this code"
            )

        if data["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Redirect URI mismatch"
            )

        # PKCE Check
        if data.get("code_challenge"):
            if not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Code verifier required (PKCE)"
                )
            self._verify_pkce(
                code_verifier, data["code_challenge"], data.get("code_challenge_method")
            )

        # Burn the code
        del self._auth_codes[code]

        return {"user_id": data["user_id"], "scope": data["scope"]}

    def _verify_pkce(self, verifier: str, challenge: str, method: str | None) -> None:
        import base64
        import hashlib

        if method == "S256":
            # S256: BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
            hashed = hashlib.sha256(verifier.encode("ascii")).digest()
            encoded = base64.urlsafe_b64encode(hashed).decode("ascii").rstrip("=")
            if encoded != challenge:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="PKCE verification failed"
                )
        # plain
        elif verifier != challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="PKCE verification failed"
            )
