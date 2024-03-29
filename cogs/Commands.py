import json
import re

import bcrypt
import nextcord
from asyncpg import Pool
from icecream import ic
from nextcord.ext import commands

from db_conn import connect

with open("config.json", "r") as f:
    CONFIG = json.load(f)
    ACCOUNTS_LIMITS = CONFIG.get("accounts_limits", {})

CREATE_TABLES_SQL = """-- Создает таблицу
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT,
    discord_id TEXT
);

-- Добавляет недостающие поля в таблицу
ALTER TABLE users
ADD COLUMN IF NOT EXISTS uuid CHAR(36) UNIQUE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS accessToken CHAR(32) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS serverID VARCHAR(41) DEFAULT NULL;

-- Добавляет расширение для генерации UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Добавляет триггер для генерации UUID, если его еще не существует
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'users_uuid_trigger') THEN
        CREATE TRIGGER users_uuid_trigger
        BEFORE INSERT ON users
        FOR EACH ROW
        EXECUTE FUNCTION public.users_uuid_trigger_func();
    END IF;
END $$;

-- Генерирует UUID для уже существующих пользователей
UPDATE users SET uuid=(SELECT uuid_generate_v4()) WHERE uuid IS NULL;"""

def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12))
    return hashed_password.decode("utf-8")


class Commands(commands.Cog):
    def __init__(self, bot) -> None:
        self.db_conn: Pool | None = None
        self.bot: nextcord.Client = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        self.db_conn = await connect()
        if not self.db_conn:
            return

        async with self.db_conn.acquire() as cursor:
            await cursor.execute(CREATE_TABLES_SQL)

    @nextcord.slash_command(
        name="register", description="Зарегистрироваться в TvinProject"
    )
    async def register(self, ctx: nextcord.Interaction, username: str, password: str):
        """
        Parameters
        ----------
        ctx: nextcord.Interaction
            Контекст discord
        username: str
            Ник игрока на серверах TvinProject
        password: str
            Пароль для входа в лаунчер
        """
        if not (ctx.user and self.db_conn):
            return
        discord_id = str(ctx.user.id)

        async with self.db_conn.acquire() as cursor:
            await ctx.response.defer(ephemeral=True)

            count: int = await cursor.fetchval("SELECT COUNT(*) FROM users WHERE discord_id = $1", discord_id)
            account_limit: int = ACCOUNTS_LIMITS.get(discord_id, 1)
            if count >= account_limit:
                await ctx.followup.send(
                    f"Вы не можете зарегистрировать больше аккаунтов. Ваш текущий лимит {account_limit}", ephemeral=True
                )
                return

            if not bool(re.match(r"^[\w\-\[\]{}^\\|`_]+$", username)):
                await ctx.followup.send(
                    "В никнейме допускается только английские буквы и специальные символы!", ephemeral=True
                )

            is_registered = await cursor.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)",
                username
            )
            if is_registered:
                await ctx.followup.send("Никнейм уже занят!", ephemeral=True)
                return

            await cursor.execute(
                "INSERT INTO users (username, password, discord_id) VALUES ($1, $2, $3)",
                username,
                hash_password(password),
                discord_id,
            )
        await ctx.followup.send("Вы были успешно зарегистрированы!", ephemeral=True)


def setup(client):
    client.add_cog(Commands(client))
