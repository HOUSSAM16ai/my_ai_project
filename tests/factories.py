# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import User, Mission

# Factories are now session-agnostic. The session is injected at test runtime via a fixture.

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        # The session is now managed by the fixture in conftest.py
        # sqlalchemy_session_persistence = "flush" # Set in fixture

    id = factory.Sequence(lambda n: n + 1)
    email = factory.LazyAttribute(lambda obj: f'user{obj.id}@example.com')
    full_name = factory.Faker('name')
    # password hash will be set by the model's default setter

class MissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Mission
        # sqlalchemy_session_persistence = "flush" # Set in fixture

    id = factory.Sequence(lambda n: n + 1)
    objective = factory.Faker('sentence')
    initiator_id = factory.SelfAttribute('initiator.id') # Link via id
    initiator = factory.SubFactory(UserFactory)
