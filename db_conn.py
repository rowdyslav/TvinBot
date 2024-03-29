from os import environ

import asyncpg
from dotenv import load_dotenv
from icecream import ic

load_dotenv()
database_config = {
    "user": environ["DB_USER"],
    "password": environ["DB_PASSWORD"],
    "database": environ["DB_NAME"],
    "host": environ["DB_HOST"],
}


async def connect() -> asyncpg.Pool | None:
    try:
        db_conn = await asyncpg.create_pool(**database_config)  # type: ignore
        if not db_conn:
            print("Ошибка подключения к базе данных!")
        return db_conn
    except Exception as e:
        ic(e)
