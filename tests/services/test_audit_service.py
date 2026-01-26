import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.audit import AuditAction, AuditService


class TestAuditService(unittest.IsolatedAsyncioTestCase):
    async def test_record_enum(self):
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # SQLAlchemy session.add is synchronous
        service = AuditService(mock_session)

        # Patch AuditLog in the service module
        with patch("app.services.audit.service.AuditLog") as mock_audit_log:
            mock_instance = MagicMock()
            mock_audit_log.return_value = mock_instance

            await service.record(
                actor_user_id=1,
                action=AuditAction.LOGIN,
                target_type="user",
                target_id="1",
                metadata={"foo": "bar"},
                ip="1.2.3.4",
                user_agent="agent",
            )

            # Assertions
            mock_audit_log.assert_called()
            call_kwargs = mock_audit_log.call_args[1]
            self.assertEqual(call_kwargs["action"], "login")

            mock_session.add.assert_called_with(mock_instance)
            mock_session.commit.assert_awaited()

    async def test_record_string(self):
        mock_session = AsyncMock()
        mock_session.add = MagicMock()  # SQLAlchemy session.add is synchronous
        service = AuditService(mock_session)

        with patch("app.services.audit.service.AuditLog") as mock_audit_log:
            await service.record(
                actor_user_id=1,
                action="custom",
                target_type="user",
                target_id="1",
                metadata={},
                ip="1.2.3.4",
                user_agent="agent",
            )
            call_kwargs = mock_audit_log.call_args[1]
            self.assertEqual(call_kwargs["action"], "custom")


if __name__ == "__main__":
    unittest.main()
