import os
from .facilitator import Facilitator
from .app_state import app_state, ChannelState
from .message_sender import SyncMessageSender
from sqlalchemy import create_engine
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.errors import SlackApiError


# Env vars
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID")
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1) # Heroku uses the old postgres:// scheme, but SQLAlchemy requires the new postgresql:// scheme


# Installation store for OAuth / Slack app installation
store = SQLAlchemyInstallationStore(
  client_id=SLACK_CLIENT_ID,
  engine=create_engine(DATABASE_URL)
)
store.create_tables()


# Initialize the app
app = App(
  signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
  oauth_settings=OAuthSettings(
    client_id=os.environ.get("SLACK_CLIENT_ID"),
    client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
    scopes=["app_mentions:read",
            "channels:history",
            "channels:read",
            "chat:write",
            "commands",
            "users:read",
            "groups:history",
            "groups:read",
            "mpim:history",
            "mpim:read",
            "im:read"],
    installation_store=store
    # TODO Add state store
  )
)


# Start a double crux session, for the people mentioned
@app.command("/doublecrux")
def double_crux(client, ack, say, command):
  if DEBUG_MODE:
    print(command)

  channel_id = command['channel_id']
  channel_info = client.conversations_info(channel=channel_id)
  if not channel_info['channel']['is_member']:
    ack("Sorry, I don't have access to this channel! Add me via the Integrations menu, or by pinging me with @Harmony")
    return
  else:
    ack()

  # TODO User should @tag the users involved instead of writing their names
  params = command['text'].split(',')
  params = [param.strip() for param in params]
  try:
    participant_a = params[0]
    participant_b = params[1]
  except IndexError:
    client.chat_postEphemeral(
      channel=channel_id,
      user=command['user_id'],
      text="Please provide the names of two participants to start a double crux session between, separated by a comma."
    )
    return

  print(f"Starting a new double crux in Slack: {command}")
  say(f"Starting a new double crux session between {participant_a} and {participant_b}...")
  
  if channel_id in app_state.channel_states:
    app_state.channel_states[channel_id].bot = None # End any existing session
  sync_message_sender = SyncMessageSender(say)
  channel_state = ChannelState(sync_message_sender)
  app_state.channel_states[channel_id] = channel_state
  
  if DEBUG_MODE and len(params) > 2:
    # If there was a third parameter, and it's a number, use it as the message time limit
    # If it's text, use it as optional initial instructions
    try:
      message_time_limit = int(params[2])
      channel_state.bot = Facilitator(participant_a, participant_b)
      channel_state.min_time_between_messages = message_time_limit
      say(f"Setting message time limit to {message_time_limit} seconds...")
    except ValueError:
      custom_instructions = ','.join(params[2:])
      channel_state.bot = Facilitator(participant_a, participant_b, custom_instructions)
      say(f"Setting custom instructions: {','.join(params[2:])}...")
  else:
    channel_state.bot = Facilitator(participant_a, participant_b)
  
  channel_state.send_response()


# Handle incoming messages
@app.event("message")
def handle_message(client, event, say):
  # Ignore thread messages, edit updates, "member joined" etc.
  is_thread = 'thread_ts' in event and event['thread_ts'] != event['ts']
  is_system_message = 'subtype' in event
  if is_thread or is_system_message:
    if DEBUG_MODE:
      print("Received an event that wasn't a plain channel message, skipping...")
    return

  # Bot hasn't been initialized / no active double crux session
  channel_id = event['channel']
  if (channel_id not in app_state.channel_states or app_state.channel_states[channel_id].bot is None):
    if DEBUG_MODE:
      print("Received a new message, but no live bot found")
    say("Please start a double crux session first with [/doublecrux name1, name2]")
    return
  
  # Process the message
  if DEBUG_MODE:
    print("Received new message")
  channel_state = app_state.channel_states[channel_id]
  user_info = client.users_info(user=event['user'])
  user_name = user_info['user']['profile'].get('display_name') or user_info['user']['profile'].get('real_name') or user_info['user']['name']
  message = event['text']
  channel_state.handle_message(user_name, message)


# Handle @-mentions of the bot
@app.event("app_mention")
def handle_app_mention(client, event, say):
  # TODO Be useful (maybe send an ephemeral message about how to start a new conversation)
  say("Hi there!")


if __name__ == "__main__":
  app.start(port=int(os.environ.get("PORT", 3000)))