# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.models import Mission, User

# Factories are now session-agnostic. The session is injected at test runtime via a fixture.


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        # The session is now managed by the fixture in conftest.py
        # sqlalchemy_session_persistence = "flush" # Set in fixture

    id = factory.Sequence(lambda n: n + 1000) # Start from 1000 to avoid conflicts
    email = factory.LazyAttribute(lambda obj: f"user{obj.id}@example.com")
    full_name = factory.Faker("name")
    # password hash will be set by the model's default setter or method


class MissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Mission
        # sqlalchemy_session_persistence = "flush" # Set in fixture

    id = factory.Sequence(lambda n: n + 1)
    objective = factory.Faker("sentence")
    # Corrected to match 'user' relationship and 'user_id' foreign key in Mission model
    user_id = factory.SelfAttribute("user.id")
    user = factory.SubFactory(UserFactory)
