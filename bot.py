import os
import asyncio
import aiosqlite
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.db = None

bot = Bot()

# ---------- STARTUP ----------
@bot.event
async def on_ready():
    bot.db = await aiosqlite.connect("cards.sqlite")
    await bot.db.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            user_id INTEGER PRIMARY KEY,
            color TEXT NOT NULL,
            note TEXT
        )
        """
    )
    await bot.db.commit()

    # GLOBAL command sync (takes up to 1 hour to appear everywhere)
    await bot.tree.sync()
    print("bot online (global commands syncing)")

# ---------- COMMAND GROUP ----------
card = app_commands.Group(
    name="card",
    description="global kindergarten card",
)
bot.tree.add_command(card)

# ---------- SET CARD ----------
@card.command(name="set")
async def set_card(
    interaction: discord.Interaction,
    user: discord.User,
    color: str,
    note: str = "",
):
    color = color.lower()
    if color not in ["green", "yellow", "red"]:
        return await interaction.response.send_message(
            "color must be green, yellow, or red",
            ephemeral=True,
        )

    await bot.db.execute(
        """
        INSERT OR REPLACE INTO cards (user_id, color, note)
        VALUES (?, ?, ?)
        """,
        (user.id, color, note),
    )
    await bot.db.commit()

    await interaction.response.send_message(
        f"{user.name} → {color}",
        ephemeral=True,
    )

# ---------- SHOW ALL ----------
@card.command(name="show")
async def show_cards(interaction: discord.Interaction):
    cur = await bot.db.execute("SELECT user_id, color, note FROM cards")
    rows = await cur.fetchall()

    if not rows:
        return await interaction.response.send_message(
            "no one has a card yet",
            ephemeral=True,
        )

    lines = []
    for user_id, color, note in rows:
        user = await bot.fetch_user(user_id)
        line = f"{user.name} - {color}"
        if note:
            line += f" ({note})"
        lines.append(line)

    embed = discord.Embed(
        title="kindergarten card chart",
        description="\n".join(lines),
    )

    await interaction.response.send_message(embed=embed)

# ---------- RUN ----------
async def main():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set")
    await bot.start(TOKEN)

asyncio.run(main())
