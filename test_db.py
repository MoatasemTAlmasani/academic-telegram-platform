import asyncio

from sqlalchemy import text
from database.session import engine


async def main():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        print("DATABASE CONNECTION OK:", result.scalar())


if __name__ == "__main__":
    asyncio.run(main())