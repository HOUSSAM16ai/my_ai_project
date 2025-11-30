import asyncio
import os

from dotenv import load_dotenv

# Load env before other imports that might rely on settings
load_dotenv()

# Check if DATABASE_URL is loaded
print(f"DEBUG: DATABASE_URL={os.getenv('DATABASE_URL')}")

from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.models import User  # noqa: E402


async def main():
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == "benmerrahhoussam16@gmail.com")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            print(f"User found: {user.email}")
            user.set_password("1111")
            session.add(user)
            await session.commit()
            print("Password set to 1111")
        else:
            print("User NOT found. Creating...")
            user = User(
                email="benmerrahhoussam16@gmail.com", full_name="Houssam Admin", is_admin=True
            )
            user.set_password("1111")
            session.add(user)
            await session.commit()
            print("User created and password set to 1111")


if __name__ == "__main__":
    asyncio.run(main())
