"""In-memory storage implementations for analytics."""

import threading
from collections import deque
from datetime import UTC, datetime, timedelta

from . import UserData, UserEvent, UserSegment, UserSession


class InMemoryEventStore:
    """In-memory event storage"""

    def __init__(self, max_events: int = 100000):
        self.lock = threading.RLock()
        self.events: deque[UserEvent] = deque(maxlen=max_events)

    def add_event(self, event: UserEvent) -> None:
        with self.lock:
            self.events.append(event)

    def get_events(
        self, user_id: int | None = None, start_time: datetime | None = None
    ) -> list[UserEvent]:
        with self.lock:
            events = list(self.events)
            if user_id is not None:
                events = [e for e in events if e.user_id == user_id]
            if start_time is not None:
                events = [e for e in events if e.timestamp >= start_time]
            return events

    def get_recent_events(self, days: int = 30) -> list[UserEvent]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return self.get_events(start_time=cutoff)


class InMemorySessionStore:
    """In-memory session storage"""

    def __init__(self):
        self.lock = threading.RLock()
        self.sessions: dict[str, UserSession] = {}

    def add_session(self, session: UserSession) -> None:
        with self.lock:
            self.sessions[session.session_id] = session

    def get_session(self, session_id: str) -> UserSession | None:
        with self.lock:
            return self.sessions.get(session_id)

    def update_session(self, session: UserSession) -> None:
        with self.lock:
            self.sessions[session.session_id] = session

    def get_recent_sessions(self, days: int = 30) -> list[UserSession]:
        with self.lock:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            return [s for s in self.sessions.values() if s.start_time >= cutoff]


class InMemoryUserStore:
    """In-memory user data storage"""

    def __init__(self):
        self.lock = threading.RLock()
        self.users: dict[int, UserData] = {}

    def add_user(self, user_data: UserData) -> None:
        with self.lock:
            self.users[user_data.user_id] = user_data

    def get_user(self, user_id: int) -> UserData | None:
        with self.lock:
            return self.users.get(user_id)

    def update_user(self, user_data: UserData) -> None:
        with self.lock:
            self.users[user_data.user_id] = user_data

    def get_all_users(self) -> dict[int, UserData]:
        with self.lock:
            return dict(self.users)

    def get_users_by_segment(self, segment: UserSegment) -> list[int]:
        with self.lock:
            return [uid for uid, data in self.users.items() if data.segment == segment]


class InMemoryActiveUsersStore:
    """In-memory active users tracking"""

    def __init__(self):
        self.lock = threading.RLock()
        self.active_1d: set[int] = set()
        self.active_7d: set[int] = set()
        self.active_30d: set[int] = set()

    def add_active_user(self, user_id: int, period: str) -> None:
        with self.lock:
            if period == "1d":
                self.active_1d.add(user_id)
            elif period == "7d":
                self.active_7d.add(user_id)
            elif period == "30d":
                self.active_30d.add(user_id)

    def get_active_users(self, period: str) -> set[int]:
        with self.lock:
            if period == "1d":
                return set(self.active_1d)
            elif period == "7d":
                return set(self.active_7d)
            elif period == "30d":
                return set(self.active_30d)
            return set()

    def clear_period(self, period: str) -> None:
        with self.lock:
            if period == "1d":
                self.active_1d.clear()
            elif period == "7d":
                self.active_7d.clear()
            elif period == "30d":
                self.active_30d.clear()


class InMemoryABTestStore:
    """In-memory A/B test storage"""

    def __init__(self):
        self.lock = threading.RLock()
        self.tests: dict[str, dict] = {}

    def add_test(self, test_id: str, test_data: dict) -> None:
        with self.lock:
            self.tests[test_id] = test_data

    def get_test(self, test_id: str) -> dict | None:
        with self.lock:
            return self.tests.get(test_id)

    def update_test(self, test_id: str, test_data: dict) -> None:
        with self.lock:
            self.tests[test_id] = test_data

    def get_all_tests(self) -> dict[str, dict]:
        with self.lock:
            return dict(self.tests)


class InMemoryNPSStore:
    """In-memory NPS response storage"""

    def __init__(self, max_responses: int = 10000):
        self.lock = threading.RLock()
        self.responses: deque[dict] = deque(maxlen=max_responses)

    def add_response(self, response: dict) -> None:
        with self.lock:
            self.responses.append(response)

    def get_responses(self, days: int | None = None) -> list[dict]:
        with self.lock:
            if days is None:
                return list(self.responses)
            cutoff = datetime.now(UTC) - timedelta(days=days)
            return [r for r in self.responses if r["timestamp"] >= cutoff]

class InMemoryCohortStore:
    """In-memory cohort storage"""

    def __init__(self):
        self.lock = threading.RLock()
        self.cohorts: dict[str, dict] = {}

    def add_cohort(self, cohort_id: str, cohort_data: dict) -> None:
        with self.lock:
            self.cohorts[cohort_id] = cohort_data

    def get_cohort(self, cohort_id: str) -> dict | None:
        with self.lock:
            return self.cohorts.get(cohort_id)

    def update_cohort(self, cohort_id: str, cohort_data: dict) -> None:
        with self.lock:
            self.cohorts[cohort_id] = cohort_data

    def list_cohorts(self) -> list[dict]:
        with self.lock:
            return list(self.cohorts.values())

class InMemoryRevenueStore:
    """In-memory revenue storage"""

    def __init__(self):
        self.lock = threading.RLock()
        self.transactions: list[dict] = []

    def add_transaction(self, transaction: dict) -> None:
        with self.lock:
            self.transactions.append(transaction)

    def get_transactions(self) -> list[dict]:
        with self.lock:
            return list(self.transactions)
