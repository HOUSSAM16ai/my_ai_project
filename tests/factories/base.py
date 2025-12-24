
import factory
from app.models import User, Mission

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    is_admin = False

class MissionFactory(factory.Factory):
    class Meta:
        model = Mission

    objective = factory.Faker("sentence")
    # Mission does not have 'name' or 'goal'. 'objective' is the correct field.
