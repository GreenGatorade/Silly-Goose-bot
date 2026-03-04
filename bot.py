import discord
from collections import defaultdict
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

TRACKED_WORD = "nigger"

# Stores count per user: {user_display_name: count}
word_counts = defaultdict(int)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}. Scanning message history...')

    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None):
                    if message.author.bot:
                        continue
                    if TRACKED_WORD in message.content.lower().split():
                        word_counts[message.author.display_name] += 1
            except discord.Forbidden:
                print(f'No access to #{channel.name}, skipping...')

    print('Finished scanning history!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Track new messages
    if TRACKED_WORD in message.content.lower().split():
        word_counts[message.author.display_name] += 1

    # !topword command
    if message.content.lower().strip() == "!topword":
        if not word_counts:
            await message.channel.send("Nobody has said the n word yet!")
            return

        rankings = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        result = "**N-word Leaderboard **\n"
        for i, (user, count) in enumerate(rankings[:10], 1):
            result += f"{i}. {user} — {count} times\n"

        await message.channel.send(result)

    # "er" joke
    elif message.content.strip().lower().endswith("er"):
        last_word = message.content.strip().split()[-1]
        await message.channel.send(f"{last_word}? I hardly know her!")

client.run(os.getenv("MTQ3ODU5MjE2NTM1MjU3NTA2OQ.GuS0hF.hb_saK7E6dQmyfQbe-gfBfqhUCpOOO7bdTRoq4"))
