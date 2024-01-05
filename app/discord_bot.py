import os
import asyncio
from .facilitator import Facilitator
from .app_state import app_state, ChannelState
from .message_sender import AsyncMessageSender
import discord
from discord import app_commands


# Env vars
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
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

    async_message_sender = AsyncMessageSender(
        channel.send, asyncio.get_event_loop())
    channel_state = ChannelState(async_message_sender)
    app_state.channel_states[interaction.channel_id] = channel_state
    channel_state.bot = Facilitator(member1.mention, member2.mention)

    print(
        f"Starting a new double crux in Discord server '{interaction.guild.name}' between {member1.mention} and {member2.mention}")
    await interaction.response.send_message(f"Starting a new double crux session between {member1.mention} and {member2.mention}...")
    await asyncio.to_thread(channel_state.send_response)


@tree.command(name='enddoublecrux', description='End the current double crux session', guild=test_guild)
async def enddoublecrux(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in app_state.channel_states and app_state.channel_states[channel_id].bot:
        app_state.channel_states[channel_id].bot = None
        user_name = interaction.user.mention
        await interaction.response.send_message(f"The double crux session has been ended by {user_name}.")
    else:
        await interaction.response.send_message("There is no active double crux session to end.", ephemeral=True)



@client.event
async def on_message(message):
    # Ignore messages from the bot itself or system messages
    if message.author == client.user or message.type != discord.MessageType.default:
        if DEBUG_MODE:
            print("Received an event that wasn't a plain channel message, skipping...")
        return

    # Bot hasn't been initialized / no active double crux session
    channel_id = message.channel.id
    if channel_id not in app_state.channel_states or app_state.channel_states[channel_id].bot is None:
        if DEBUG_MODE:
            print("Received a new message, but no live bot found")
        return

    # Process the message
    if DEBUG_MODE:
        print("Reveived new message")
    channel_state = app_state.channel_states[channel_id]
    user_name = message.author.mention
    message_content = message.content
    await asyncio.to_thread(channel_state.handle_message, user_name, message_content)


client.run(DISCORD_BOT_TOKEN)
