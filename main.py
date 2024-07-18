import asyncio

from data.orm import AsyncORM

asyncio.run(AsyncORM.insert_workers())

