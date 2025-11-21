#!/usr/bin/env python3
import os
import sys
from urllib.parse import urlparse, urlunparse, quote_plus, parse_qsl, urlencode

def sanitize():
    url = os.environ.get("DATABASE_URL", "")
    if not url: return ""

    try:
        p = urlparse(url)
        # 1. Encode Password (Fixes % crash)
        safe_pwd = quote_plus(p.password) if p.password else ""

        # 2. Rebuild Netloc
        userinfo = f"{p.username}:{safe_pwd}" if safe_pwd else p.username
        netloc = f"{userinfo}@{p.hostname}"
        if p.port: netloc += f":{p.port}"

        # 3. Fix Query Params (SSL & Asyncpg)
        q = dict(parse_qsl(p.query))
        if 'sslmode' in q: del q['sslmode']
        q['ssl'] = 'require'

        # 4. Force Scheme
        return urlunparse(("postgresql+asyncpg", netloc, p.path, p.params, urlencode(q), p.fragment))
    except:
        return url

if __name__ == "__main__":
    print(sanitize())
