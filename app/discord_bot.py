import os
import asyncio
from .facilitator import Facilitator
from .app_state import app_state, ChannelState
from .message_sender import AsyncMessageSender
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
    channel = client.get_channel(interaction.channel_id)
    if channel is None or not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message("The bot is not present or does not have permission to send messages in this channel.", ephemeral=True)
        return

    # Check if the channel already has an ongoing session and end it
    if interaction.channel_id in app_state.channel_states:
        app_state.channel_states[interaction.channel_id].bot = None

    async_message_sender = AsyncMessageSender(channel.send, asyncio.get_event_loop())
    channel_state = ChannelState(async_message_sender)
    app_state.channel_states[interaction.channel_id] = channel_state
    channel_state.bot = Facilitator(member1.display_name, member2.display_name)

    print(f"Starting a new double crux in Discord server '{interaction.guild.name}' between {member1.display_name} and {member2.display_name}")
    await interaction.response.send_message(f"Starting a new double crux session between {member1.display_name} and {member2.display_name}...")
    await asyncio.to_thread(channel_state.send_response)


@client.event
async def on_message(message):
    # Ignore messages from the bot itself or system messages
    if message.author == client.user or message.type != discord.MessageType.default:
        return

    channel_id = message.channel.id
    # Bot hasn't been initialized / no active double crux session
    if channel_id not in app_state.channel_states or app_state.channel_states[channel_id].bot is None:
        await message.channel.send("Please start a double crux session first with /doublecrux")
        return

    # Process the message
    channel_state = app_state.channel_states[channel_id]
    user_name = message.author.display_name
    message_content = message.content
    await asyncio.to_thread(channel_state.handle_message, user_name, message_content)


client.run(DISCORD_BOT_TOKEN)
