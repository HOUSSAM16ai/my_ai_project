
import asyncio
from app.main import create_app

async def main():
    app = create_app()
    print("=== Registered Routes ===")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"{route.methods} {route.path}")
        else:
            print(route)

if __name__ == "__main__":
    asyncio.run(main())
