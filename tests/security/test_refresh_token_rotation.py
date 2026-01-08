from __future__ import annotations

"""اختبار حماية تدوير رموز التحديث واكتشاف إعادة الاستخدام."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.domain.models import RefreshToken
from app.services.auth import AuthService


@pytest.mark.asyncio
async def test_refresh_rotation_sets_replacement_and_replay_guard(db_session):
    service = AuthService(db_session)
    user = await service.register_user(
        full_name="Replay User",
        email="replay@example.com",
        password="Password123!",
        ip="1.1.1.1",
        user_agent="pytest-agent",
    )

    first_tokens = await service.issue_tokens(user, ip="1.1.1.1", user_agent="pytest-agent")
    first_refresh = first_tokens["refresh_token"]

    rotated = await service.refresh_session(
        refresh_token=first_refresh,
        ip="1.1.1.1",
        user_agent="pytest-agent",
    )

    # Replay attempt should revoke the entire family
    with pytest.raises(HTTPException):
        await service.refresh_session(
            refresh_token=first_refresh,
            ip="1.1.1.1",
            user_agent="pytest-agent",
        )

    old_token_id, _ = service._split_refresh_token(first_refresh)
    old_record = await service._get_refresh_record(old_token_id)
    assert old_record.replaced_by_token_id is not None
    assert old_record.revoked_at is not None

    new_token_id, _ = service._split_refresh_token(rotated["refresh_token"])
    new_record = await service._get_refresh_record(new_token_id)
    assert new_record.family_id == old_record.family_id

    family_tokens = await db_session.execute(
        select(RefreshToken).where(RefreshToken.family_id == new_record.family_id)
    )
    for token in family_tokens.scalars().all():
        assert token.revoked_at is not None
