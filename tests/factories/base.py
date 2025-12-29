
import factory

from app.models import Mission, User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = None  # overridden in conftest or subclass

    email = factory.Faker('email')
    full_name = factory.Faker('name')
    is_admin = False

class MissionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Mission
        sqlalchemy_session = None  # overridden in conftest or subclass

    objective = factory.Faker('sentence')
