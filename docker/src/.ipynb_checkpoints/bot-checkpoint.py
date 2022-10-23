# This example requires the 'message_content' intent.

import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    # on demand
    if message.content.startswith('badminton for 2 hours between 19:00 and 21:00 in Erith'):
        findAvailableSlots(...)
        await message.channel.send('Hello!')


        
client.run('MTAzMzQ4Mjg3NDk4NjQzODcyNg.GenKtg.ENGfxsK68gbYT7z_vHZYI-Ac-KWNqf9OrOrE2s')

while True:
    print("I am being called")
