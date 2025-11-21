#!/usr/bin/env python3
import os
import sys
from urllib.parse import parse_qsl, quote_plus, unquote_plus, urlencode, urlparse, urlunparse


def sanitize_database_url(url: str) -> str:
    """
    Sanitizes and repairs the DATABASE_URL to be compatible with:
    1. SQLAlchemy (needs encoded passwords)
    2. Asyncpg (needs postgresql+asyncpg://)
    3. Supabase (needs ssl=require)
    4. PgBouncer (needs specific handling, though mostly in connect_args)
    """
    if not url:
        return ""

    try:
        # 0. Quick exit for SQLite
        if url.startswith("sqlite"):
            return url

        # 1. Parse the URL
        # Handle the case where scheme is missing or weird
        if "://" not in url:
            # Assume it's a connection string or badly formatted
            return url

        p = urlparse(url)

        # 2. Encode Password
        # Passwords with special chars like '@', ':', '%' must be encoded
        safe_pwd = ""
        if p.password:
            try:
                # Decode first to avoid double encoding if it was already encoded
                decoded = unquote_plus(p.password)
            except Exception:
                decoded = p.password
            safe_pwd = quote_plus(decoded)

        # 3. Rebuild User Info
        username = p.username if p.username else ""
        userinfo = f"{username}:{safe_pwd}" if safe_pwd else username

        # 4. Rebuild Netloc
        # netloc includes userinfo@host:port
        hostname = p.hostname if p.hostname else ""
        port = p.port

        netloc = userinfo
        if hostname:
            netloc += f"@{hostname}"
        if port:
            netloc += f":{port}"

        # 5. Fix Scheme
        scheme = p.scheme
        if scheme.startswith("postgres"):
            scheme = "postgresql+asyncpg"

        # 6. Fix Query Parameters (SSL)
        # asyncpg connection string uses ?ssl=require
        # legacy libpq uses ?sslmode=require
        qs = dict(parse_qsl(p.query))

        # Remove legacy sslmode if present
        qs.pop("sslmode", None)

        # Force SSL for Postgres/Supabase
        if "postgresql" in scheme:
            qs["ssl"] = "require"

        # Re-encode query params
        query_string = urlencode(qs)

        # 7. Reconstruct URL
        clean_url = urlunparse((scheme, netloc, p.path, p.params, query_string, p.fragment))
        return clean_url

    except Exception as e:
        # If parsing fails, output the original URL (or handled error)
        # But since we are in a bootstrap script, we should probably fail or return original
        # We'll log to stderr for debugging and return original
        sys.stderr.write(f"Error sanitizing URL: {e}\n")
        return url


if __name__ == "__main__":
    raw_url = os.environ.get("DATABASE_URL", "")
    if not raw_url:
        # Fallback or empty
        print("")
    else:
        print(sanitize_database_url(raw_url))
