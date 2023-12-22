import os
import discord
from discord import app_commands


# Env vars
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_TEST_SERVER_ID = os.environ.get("DISCORD_TEST_SERVER_ID")

if DISCORD_TEST_SERVER_ID:
    test_guild = discord.Object(id=int(DISCORD_TEST_SERVER_ID))
    print(f'Using test server id {DISCORD_TEST_SERVER_ID}')
else:
    test_guild = None
    print('No test server id found')


# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# Bot behaviour
@client.event
async def on_ready():
    await tree.sync(guild=test_guild)
    print(f'Logged in as {client.user}')


@tree.command(name='doublecrux', description='Start a new double crux session', guild=test_guild)
@app_commands.describe(member1='The first participant of the double crux', member2='The second participant of the double crux')
async def doublecrux(interaction: discord.Interaction, member1: discord.Member, member2: discord.Member):
    print("In /doublecrux")
    await interaction.response.send_message(f'Would start a double crux session between {member1.display_name} and {member2.display_name}, but functionality not added yet.')


@client.event
async def on_message(message):
    print("In on_message")
    if message.author == client.user:
        print('self sent a msg')
        return

    if message.content.lower().startswith('hello'):
        await message.channel.send('Hi there!')


client.run(DISCORD_BOT_TOKEN)
