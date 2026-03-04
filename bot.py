import discord
from collections import defaultdict
import os
import re

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

TRACKED_WORDS = ["nigger", "niggers", "nigga"]  # Add your words here

word_counts = defaultdict(int)

def message_contains_tracked_word(content):
    for word in TRACKED_WORDS:
        if re.search(rf'\b{word}\b', content.lower()):
            return True
    return False

@client.event
async def on_ready():
    print(f'Logged in as {client.user}. Scanning message history...')

    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None):
                    if message.author.bot:
                        continue
                    if message_contains_tracked_word(message.content):
                        word_counts[message.author.display_name] += 1
            except discord.Forbidden:
                print(f'No access to #{channel.name}, skipping...')

    print('Finished scanning history!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message_contains_tracked_word(message.content):
        word_counts[message.author.display_name] += 1

    if message.content.lower().strip() == "!topword":
        if not word_counts:
            await message.channel.send("Nobody has said any tracked words yet!")
            return

        rankings = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        result = "**Leaderboard 💪**\n"
        for i, (user, count) in enumerate(rankings[:10], 1):
            result += f"{i}. {user} — {count} times\n"

        await message.channel.send(result)

    elif message.content.strip().lower().endswith("er"):
        last_word = message.content.strip().split()[-1]
        await message.channel.send(f"{last_word}? I hardly know her!")

client.run(os.getenv("TOKEN"))
