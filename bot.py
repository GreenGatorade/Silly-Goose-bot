import discord
from collections import defaultdict
import os
import re
import json
import asyncio
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
client = discord.Client(intents=intents)

TRACKED_WORDS = ["nigger", "niggers", "nigga"]
message_log = []
logged_message_ids = set()

def load_log():
    global message_log, logged_message_ids
    if os.path.exists("messages.json"):
        with open("messages.json", "r") as f:
            message_log = json.load(f)
            logged_message_ids = {entry["id"] for entry in message_log if "id" in entry}

def save_log():
    with open("messages.json", "w") as f:
        json.dump(message_log, f, indent=2)

def message_contains_tracked_word(content):
    for word in TRACKED_WORDS:
        if re.search(rf'\b{word}\b', content.lower()):
            return True
    return False

def get_word_counts():
    counts = defaultdict(int)
    for entry in message_log:
        counts[entry["user"]] += 1
    return counts

@client.event
async def on_ready():
    load_log()
    print(f'Logged in as {client.user}. Already have {len(message_log)} messages. Starting background scan...')
    asyncio.create_task(scan_history())

async def scan_history():
    new_count = 0
    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None):
                    if message.author.bot:
                        continue
                    if message.id in logged_message_ids:
                        continue
                    if message_contains_tracked_word(message.content):
                        entry = {
                            "id": message.id,
                            "user": message.author.display_name,
                            "message": message.content,
                            "timestamp": message.created_at.isoformat()
                        }
                        message_log.append(entry)
                        logged_message_ids.add(message.id)
                        new_count += 1
            except discord.Forbidden:
                print(f'No access to #{channel.name}, skipping...')
            except discord.HTTPException as e:
                print(f'Error scanning #{channel.name}: {e}, skipping...')
    save_log()
    print(f'Scan complete! Added {new_count} new messages. Total: {len(message_log)}.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message_contains_tracked_word(message.content):
        if message.id not in logged_message_ids:
            entry = {
                "id": message.id,
                "user": message.author.display_name,
                "message": message.content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            message_log.append(entry)
            logged_message_ids.add(message.id)
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
