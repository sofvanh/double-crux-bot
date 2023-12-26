import time
import unittest
from unittest.mock import MagicMock, call
from app.app_state import ChannelState, AppState

class TestChannelState(unittest.TestCase):
    def setUp(self):
        message_sender = MagicMock()
        self.channel_state = ChannelState(message_sender)
        self.channel_state.bot = MagicMock()
        self.channel_state.bot.conversation_ended.return_value = False
    
    def tearDown(self):
        self.channel_state.cancel_timers()

    def test_handle_message_timer_running(self):
        self.channel_state.send_response = MagicMock()
        self.channel_state.last_message_time = time.time() - 10
        self.channel_state.start_rate_limit_timer()
        self.channel_state.handle_message("user", "message")
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.assertFalse(self.channel_state.send_response.called)

    def test_handle_message_generation_in_progress(self):
        self.channel_state.send_response = MagicMock()
        self.channel_state.start_response_delay_timer = MagicMock()
        self.channel_state.generation_in_progress = True
        self.channel_state.handle_message("user", "message")
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.assertFalse(self.channel_state.send_response.called)
        self.assertTrue(self.channel_state.start_response_delay_timer.called)

    def test_handle_message_time_limit_passed(self):
        self.channel_state.send_response = MagicMock()
        self.channel_state.start_rate_limit_timer = MagicMock()
        self.channel_state.handle_message("user", "message")
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.channel_state.send_response.assert_called_once()
        self.assertFalse(self.channel_state.start_rate_limit_timer.called)

    def test_handle_message_start_timer(self):
        self.channel_state.send_response = MagicMock()
        self.channel_state.start_rate_limit_timer = MagicMock()
        self.channel_state.last_message_time = time.time() - 10
        self.channel_state.handle_message("user", "message")
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.assertFalse(self.channel_state.send_response.called)
        self.assertTrue(self.channel_state.start_rate_limit_timer.called)

    def test_response_timer(self):
        self.channel_state.last_message_time = time.time() - 10
        self.channel_state.start_rate_limit_timer()
        response_timer = self.channel_state.rate_limit_timer
        self.assertTrue(response_timer.is_alive())
        self.assertAlmostEqual(response_timer.interval, 30, delta=0.1)
        self.assertTrue(response_timer.is_alive())

    def test_response_timer_sending(self):
        self.channel_state.bot.generate_response.return_value = "response"
        self.channel_state.last_message_time = time.time() - 39.80
        self.channel_state.start_rate_limit_timer()
        time.sleep(0.5)
        self.channel_state.message_sender.send.assert_called_once_with("response")
        self.assertAlmostEqual(self.channel_state.last_message_time, time.time(), delta=0.7)
    
    def test_send_response(self):
        self.channel_state.bot.generate_response.return_value = "response"
        self.channel_state.send_response()
        self.channel_state.message_sender.send.assert_called_once_with("response")
        self.assertAlmostEqual(self.channel_state.last_message_time, time.time(), delta=0.1)
        self.assertFalse(self.channel_state.generation_in_progress)
    
    def test_bot_killed(self):
        self.channel_state.last_message_time = time.time() - 39.80
        self.channel_state.start_rate_limit_timer()
        self.channel_state.bot = None
        time.sleep(0.5)
        self.assertFalse(self.channel_state.message_sender.send.called)

if __name__ == '__main__':
    unittest.main()