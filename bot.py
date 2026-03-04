import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.strip().lower().endswith("er"):
        last_word = message.content.strip().split()[-1]
        await message.channel.send(f"{last_word}? I hardly know her!")

client.run("MTQ3ODU5MjE2NTM1MjU3NTA2OQ.GuS0hF.hb_saK7E6dQmyfQbe-gfBfqhUCpOOO7bdTRoq4")
