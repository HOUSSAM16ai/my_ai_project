#!/usr/bin/env python3
"""
scripts/set_admin_password.py

Usage:
  export DATABASE_URL="postgres://user:pass@host:5432/dbname"
  python scripts/set_admin_password.py user@example.com "NewStrongP@ssw0rd!"

Note: Ensure you have a backup before running.
"""

import os
import sys
import argparse
import psycopg2
from passlib.context import CryptContext

# Configure passlib context as per app/models.py
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt", "pbkdf2_sha256", "sha256_crypt"],
    deprecated="auto",
)

# Confirmed via app/models.py
TABLE_NAME = "users"
EMAIL_COLUMN = "email"
PASSWORD_COLUMN = "password_hash"

def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL env var not set. Exiting.")
        sys.exit(1)
    return psycopg2.connect(db_url)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="email of admin user")
    parser.add_argument("new_password", help="new plaintext password")
    args = parser.parse_args()

    try:
        conn = get_conn()
        cur = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    try:
        # 1) Fetch existing row
        cur.execute(f"SELECT {PASSWORD_COLUMN}, id FROM {TABLE_NAME} WHERE {EMAIL_COLUMN} = %s", (args.email,))
        row = cur.fetchone()
        if not row:
            print(f"[!] No user found with email {args.email} in table {TABLE_NAME}")
            conn.close()
            sys.exit(2)

        existing_hash, user_id = row
        print(f"[i] Found user id={user_id}. Existing password column starts with: {str(existing_hash)[:30]}")

        # 2) Detect if existing hash is known to passlib
        known = False
        try:
            if existing_hash:
                _ = pwd_context.identify(existing_hash)
                known = True
                print("[i] passlib recognized existing hash scheme:", pwd_context.identify(existing_hash))
            else:
                print("[i] Existing hash is empty/None.")
        except Exception as e:
            print("[i] passlib could not identify existing hash (Unknown or plain text).", repr(e))
            known = False

        # 3) Create new hash for new_password using the preferred scheme (first in list: argon2)
        # Note: The original prompt suggested bcrypt, but app/models.py lists argon2 first.
        # Using pwd_context.hash() typically uses the default (first) scheme.
        new_hash = pwd_context.hash(args.new_password)
        print("[i] New hash generated (length: {}). Scheme: {}".format(len(new_hash), pwd_context.identify(new_hash)))

        # 4) Update DB
        cur.execute(
            f"UPDATE {TABLE_NAME} SET {PASSWORD_COLUMN} = %s WHERE id = %s",
            (new_hash, user_id),
        )
        conn.commit()
        print(f"[+] Updated password_hash for user id={user_id}. You can now try to login with the new password.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
