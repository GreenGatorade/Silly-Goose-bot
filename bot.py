import discord
from collections import defaultdict
import os
import re
import json
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
client = discord.Client(intents=intents)

TRACKED_WORDS = ["nigger", "niggers", "nigga"]
message_log = []

def message_contains_tracked_word(content):
    for word in TRACKED_WORDS:
        if re.search(rf'\b{word}\b', content.lower()):
            return True
    return False

def save_log():
    with open("messages.json", "w") as f:
        json.dump(message_log, f, indent=2)

def get_word_counts():
    counts = defaultdict(int)
    for entry in message_log:
        counts[entry["user"]] += 1
    return counts

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
                        message_log.append({
                            "user": message.author.display_name,
                            "message": message.content,
                            "timestamp": message.created_at.isoformat()
                        })
            except discord.Forbidden:
                print(f'No access to #{channel.name}, skipping...')
            except discord.HTTPException as e:
                print(f'Error scanning #{channel.name}: {e}, skipping...')

    save_log()
    print(f'Finished scanning history! Logged {len(message_log)} messages.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message_contains_tracked_word(message.content):
        message_log.append({
            "user": message.author.display_name,
            "message": message.content,
            "timestamp": datetime.utcnow().isoformat()
        })
        save_log()

    if message.content.lower().strip() == "!topword":
        if not message_log:
            await message.channel.send("Nobody has said any tracked words yet!")
            return
        word_counts = get_word_counts()
        rankings = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        result = "**Leaderboard 💪**\n"
        for i, (user, count) in enumerate(rankings[:10], 1):
            result += f"{i}. {user} — {count} times\n"
        await message.channel.send(result)

    elif message.content.strip().lower().endswith("er"):
        last_word = message.content.strip().split()[-1]
        await message.channel.send(f"{last_word}? I hardly know her!")

client.run(os.getenv("TOKEN"))
