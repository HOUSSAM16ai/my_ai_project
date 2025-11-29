# Bug Report: Non-deterministic Conversation Ordering in `get_latest_chat`

## Location
File: `app/api/routers/admin.py`
Function: `get_latest_chat`
Lines: ~180-185

## Description
The `get_latest_chat` endpoint retrieves the latest conversation for a user by ordering records by `created_at` in descending order. However, it fails to include a secondary sort key. In cases where multiple conversations are created at the exact same timestamp (common in high-throughput environments or test scenarios), the database returns an arbitrary record (often the one with the lower ID, i.e., created earlier) instead of the true latest one.

This behavior is non-deterministic and incorrect. The expected behavior is that among conversations with the same timestamp, the one with the highest ID (which was inserted last) should be returned.

## Impact
- Users may not see their most recent conversation if multiple were created quickly.
- Tests relying on creating conversations and immediately fetching the "latest" one may fail or be flaky.
- Inconsistent UI state where the "latest" chat might be an older empty one instead of the new active one.

## Proposed Fix
Add `AdminConversation.id.desc()` as a secondary sort key to the SQLAlchemy query in `get_latest_chat`.

```python
    stmt = (
        select(AdminConversation)
        .where(AdminConversation.user_id == user_id)
        .order_by(AdminConversation.created_at.desc(), AdminConversation.id.desc())  # Added id.desc()
        .limit(1)
    )
```
