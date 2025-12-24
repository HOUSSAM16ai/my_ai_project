import factory
from app.models import User, Mission

class UserFactory(factory.Factory):
    class Meta:
        model = User
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    full_name = "Test User"

class MissionFactory(factory.Factory):
    class Meta:
        model = Mission
    objective = "Test Mission"
