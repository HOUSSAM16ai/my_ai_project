#!/usr/bin/env python3
import os
from urllib.parse import parse_qsl, quote_plus, unquote_plus, urlencode, urlparse, urlunparse


def sanitize():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return ""

    try:
        # Detect if it's a path-based URL like sqlite
        if url.startswith("sqlite"):
            return url

        p = urlparse(url)

        # 1. Extract and Safe Encode Password
        raw_password = p.password
        if raw_password:
            # Try to decode first to handle already encoded passwords
            try:
                decoded = unquote_plus(raw_password)
            except Exception:
                decoded = raw_password

            safe_pwd = quote_plus(decoded)
        else:
            safe_pwd = ""

        # 2. Rebuild Netloc
        username = p.username if p.username else ""
        userinfo = f"{username}:{safe_pwd}" if safe_pwd else username
        netloc = f"{userinfo}@{p.hostname}"
        if p.port:
            netloc += f":{p.port}"

        # 3. Fix Query Params (SSL & Asyncpg)
        q = dict(parse_qsl(p.query))
        if "sslmode" in q:
            del q["sslmode"]

        # Only force ssl=require for Postgres/Supabase
        if p.scheme.startswith("postgres"):
            q["ssl"] = "require"
            scheme = "postgresql+asyncpg"
        else:
            scheme = p.scheme

        # 4. Reconstruct
        clean_url = urlunparse((scheme, netloc, p.path, p.params, urlencode(q), p.fragment))

        return clean_url
    except Exception:
        return url


if __name__ == "__main__":
    print(sanitize())
