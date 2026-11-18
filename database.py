import aiosqlite

DB_NAME = "bot_database.db"

async def init_db():
    """Inicializa la base de datos y crea la tabla de usuarios vinculados si no existe."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS linked_accounts (
                discord_id TEXT PRIMARY KEY,
                game_name TEXT NOT NULL,
                tag_line TEXT NOT NULL,
                region TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def link_riot_account(discord_id: str, game_name: str, tag_line: str, region: str):
    """Vincula o actualiza la cuenta de Riot de un usuario de Discord en la base de datos."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO linked_accounts (discord_id, game_name, tag_line, region)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET
                game_name = excluded.game_name,
                tag_line = excluded.tag_line,
                region = excluded.region
        """, (discord_id, game_name, tag_line, region))
        await db.commit()

async def get_linked_account(discord_id: str):
    """Busca y retorna la cuenta de Riot vinculada a un ID de Discord."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT game_name, tag_line, region FROM linked_accounts WHERE discord_id = ?",
            (discord_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "game_name": row[0],
                    "tag_line": row[1],
                    "region": row[2]
                }
            return None