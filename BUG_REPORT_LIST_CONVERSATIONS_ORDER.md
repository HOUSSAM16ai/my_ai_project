# Bug Report: Non-Deterministic Conversation Ordering

## Location
File: `app/api/routers/admin.py`
Function: `list_conversations`
Lines: ~225-230

## Description
The `list_conversations` endpoint retrieves a list of conversations for the current user. It currently orders the results only by `created_at` in descending order.

```python
    stmt = (
        select(AdminConversation)
        .where(AdminConversation.user_id == user_id)
        .order_by(AdminConversation.created_at.desc())
    )
```

If multiple conversations have the exact same `created_at` timestamp (which can happen in high-throughput scenarios or during automated testing), the database is free to return them in any order. This leads to non-deterministic behavior and unstable UI lists.

This violates the requirement documented in the project memory:
> When querying database records for the 'latest' entry (e.g., `AdminConversation`, `AdminMessage`), a secondary sort key (e.g., `.id.desc()`) must be used alongside `created_at.desc()` to guarantee deterministic ordering.

## Impact
- **User Interface**: Users may see conversations jumping around in the list if they were created at the same time.
- **Testing**: Tests that rely on order (like pagination tests or "latest conversation" checks) may flake.
- **API Consistency**: Repeated calls to the API might return results in different orders.

## Proposed Fix
Modify the SQLAlchemy query to include `AdminConversation.id.desc()` as a secondary sort key. This ensures that if timestamps are tied, the conversation with the higher ID (which was created later) appears first.

```python
    stmt = (
        select(AdminConversation)
        .where(AdminConversation.user_id == user_id)
        .order_by(AdminConversation.created_at.desc(), AdminConversation.id.desc())
    )
```
