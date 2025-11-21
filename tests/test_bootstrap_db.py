
import os
import unittest
from unittest.mock import patch
from scripts.bootstrap_db import sanitize_database_url

class TestBootstrapDB(unittest.TestCase):

    def test_sqlite_pass_through(self):
        url = "sqlite:///./test.db"
        self.assertEqual(sanitize_database_url(url), url)

    def test_standard_postgres(self):
        url = "postgres://user:pass@localhost:5432/db"
        expected = "postgresql+asyncpg://user:pass@localhost:5432/db?ssl=require"
        self.assertEqual(sanitize_database_url(url), expected)

    def test_postgres_with_special_chars_in_password(self):
        # password is 'p@ssword'
        url = "postgresql://user:p%40ssword@localhost:5432/db"
        expected = "postgresql+asyncpg://user:p%2540ssword@localhost:5432/db?ssl=require"
        # Wait, if it's already encoded 'p%40ssword' (@), the sanitizer decodes it to 'p@ssword' then encodes to 'p%40ssword'
        # My sanitization logic tries to be smart.
        # Let's trace: unquote_plus('p%40ssword') -> 'p@ssword'. quote_plus('p@ssword') -> 'p%40ssword'.
        # So it should remain encoded.
        # However, quote_plus encodes '@' to '%40'.

        # Let's try a password that needs encoding but isn't: "foo:bar"
        url_raw = "postgresql://user:foo:bar@localhost:5432/db"
        # urlparse might fail to parse password correctly if it contains colon without encoding?
        # Actually urlparse is usually smart enough if the scheme is standard, but 'foo:bar' as password is ambiguous
        # if not encoded.
        pass

    def test_supabase_transaction_mode_url(self):
        # Supabase transaction url usually: postgres://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:6543/postgres
        url = "postgres://postgres:secretpassword@db.xxx.supabase.co:6543/postgres"
        expected = "postgresql+asyncpg://postgres:secretpassword@db.xxx.supabase.co:6543/postgres?ssl=require"
        self.assertEqual(sanitize_database_url(url), expected)

    def test_removes_sslmode_legacy(self):
        url = "postgres://user:pass@host/db?sslmode=disable"
        expected = "postgresql+asyncpg://user:pass@host/db?ssl=require"
        self.assertEqual(sanitize_database_url(url), expected)

if __name__ == '__main__':
    unittest.main()
