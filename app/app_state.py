import os
import time
from threading import Timer
from .message_sender import MessageSender


DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"


class ChannelState:
    RATE_LIMIT_INTERVAL = 40
    RESPONSE_DELAY_INTERVAL = 90

    def __init__(self, message_sender: MessageSender):
        self.message_sender = message_sender
        self.bot = None
        self.last_message_time = 0
        self.min_time_between_messages = self.RATE_LIMIT_INTERVAL
        self.rate_limit_timer = None
        self.response_delay_timer = None
        self.generation_in_progress = False

    def start_rate_limit_timer(self):
        seconds = self.min_time_between_messages - \
            (time.time() - self.last_message_time)
        self.rate_limit_timer = Timer(seconds, self.send_response)
        self.rate_limit_timer.start()

    def start_response_delay_timer(self):
        self.response_delay_timer = Timer(self.RESPONSE_DELAY_INTERVAL, self.send_response, [
                                          f"It has been {self.RESPONSE_DELAY_INTERVAL} seconds without anyone sending a message. You should send one."])
        self.response_delay_timer.start()

    def cancel_timers(self):
        if self.rate_limit_timer and self.rate_limit_timer.is_alive():
            self.rate_limit_timer.cancel()
        if self.response_delay_timer and self.response_delay_timer.is_alive():
            self.response_delay_timer.cancel()

    def handle_message(self, user_name, message):
        self.bot.process_message(user_name, message)
        if self.generation_in_progress:
            if self.response_delay_timer and self.response_delay_timer.is_alive():
                if DEBUG_MODE:
                    print(
                        "Generation is already in progress, but response delay timer is running, skipping...")
            else:
                if DEBUG_MODE:
                    print(
                        "Generation is already in progress, starting a response delay timer...")
                self.start_response_delay_timer()
        elif time.time() - self.last_message_time > self.min_time_between_messages:
            if DEBUG_MODE:
                print("Message time limit has passed, sending response...")
            self.send_response()
        elif self.rate_limit_timer and self.rate_limit_timer.is_alive():
            if DEBUG_MODE:
                print(
                    f"Message time limit has not passed, but response timer is running, skipping...")
        else:
            if DEBUG_MODE:
                print("Starting timer to send response...")
            self.start_rate_limit_timer()

    def send_response(self, optional_instructions=''):
        if self.bot is None:
            return
        self.cancel_timers()
        self.generation_in_progress = True
        response = self.bot.generate_response(optional_instructions)
        if self.bot is None:  # Need to check again in case the conversation was ended during generation
            return
        if response is not None:
            self.message_sender.send(response)
            self.last_message_time = time.time()
        else:
            if self.rate_limit_timer and self.rate_limit_timer.is_alive():
                if DEBUG_MODE:
                    print(
                        f"Decided not to answer. Response timer is running, skipping...")
            else:
                if DEBUG_MODE:
                    print("Decided not to answer, starting a max wait timer...")
                self.start_response_delay_timer()
        if self.bot.conversation_ended():
            self.message_sender.send(
                "_Feel free to continue the discussion with the bot. If you want to start a new discussion, type '/doublecrux name 1, name 2'._")
        self.generation_in_progress = False


# TODO Conversation states should be stored in a database so that we don't lose them every time the bot restarts
class AppState:
    def __init__(self):
        self.channel_states = {}  # key: channel_id, value: ChannelState


app_state = AppState()
