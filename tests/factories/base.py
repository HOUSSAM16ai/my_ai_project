
import factory

from app.core.domain.models import Mission, User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    full_name = factory.Faker('name')
    is_admin = False

class MissionFactory(factory.Factory):
    class Meta:
        model = Mission

    objective = factory.Faker('sentence')
