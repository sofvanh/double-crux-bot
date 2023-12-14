import time
import unittest
from unittest.mock import MagicMock, call
from app.app_state import ChannelState

# TODO fix all the tests that no longer make sense after timer changes
# TODO more tests for the new timer
class TestChannelState(unittest.TestCase):
    def setUp(self):
        self.channel_state = ChannelState()
        self.channel_state.bot = MagicMock()
        self.channel_state.bot.conversation_ended.return_value = False
    
    def tearDown(self):
        self.channel_state.cancel_timers()

    def test_handle_message_timer_running(self):
        say_mock = MagicMock()
        self.channel_state.send_response = MagicMock()
        self.channel_state.last_message_time = time.time() - 10
        self.channel_state.start_rate_limit_timer(MagicMock())
        self.channel_state.handle_message("user", "message", say_mock)
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        #self.assertAlmostEqual(self.channel_state.rate_limit_timer.interval, 10, delta=0.1)
        self.assertFalse(self.channel_state.send_response.called)

    def test_handle_message_generation_in_progress(self):
        say_mock = MagicMock()
        self.channel_state.send_response = MagicMock()
        self.channel_state.start_response_delay_timer = MagicMock()
        self.channel_state.generation_in_progress = True
        self.channel_state.handle_message("user", "message", say_mock)
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.assertFalse(self.channel_state.send_response.called)
        self.assertTrue(self.channel_state.start_response_delay_timer.called)

    def test_handle_message_time_limit_passed(self):
        say_mock = MagicMock()
        self.channel_state.send_response = MagicMock()
        self.channel_state.start_rate_limit_timer = MagicMock()
        self.channel_state.handle_message("user", "message", say_mock)
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.channel_state.send_response.assert_called_once_with(say_mock)
        self.assertFalse(self.channel_state.start_rate_limit_timer.called)

    def test_handle_message_start_timer(self):
        say_mock = MagicMock()
        self.channel_state.send_response = MagicMock()
        self.channel_state.start_rate_limit_timer = MagicMock()
        self.channel_state.last_message_time = time.time() - 10
        self.channel_state.handle_message("user", "message", say_mock)
        self.channel_state.bot.process_message.assert_called_once_with("user", "message")
        self.assertFalse(self.channel_state.send_response.called)
        #actual_seconds = self.channel_state.start_rate_limit_timer.call_args[0][0]
        #self.assertAlmostEqual(actual_seconds, 30, delta=0.1)

    def test_response_timer(self):
        self.channel_state.last_message_time = time.time() - 10
        self.channel_state.start_rate_limit_timer(MagicMock())
        response_timer = self.channel_state.rate_limit_timer
        self.assertTrue(response_timer.is_alive())
        self.assertAlmostEqual(response_timer.interval, 30, delta=0.1)
        self.assertTrue(response_timer.is_alive())

    def test_response_timer_sending(self):
        self.channel_state.bot.generate_response.return_value = "response"
        say_mock = MagicMock()
        self.channel_state.last_message_time = time.time() - 39.80
        self.channel_state.start_rate_limit_timer(say_mock)
        time.sleep(0.5)
        say_mock.assert_called_once_with("response")
        self.assertAlmostEqual(self.channel_state.last_message_time, time.time(), delta=0.7)
    
    def test_send_response(self):
        say_mock = MagicMock()
        self.channel_state.bot.generate_response.return_value = "response"
        self.channel_state.send_response(say_mock)
        say_mock.assert_called_once_with("response")
        self.assertAlmostEqual(self.channel_state.last_message_time, time.time(), delta=0.1)
        self.assertFalse(self.channel_state.generation_in_progress)
    
    def test_bot_killed(self):
        say_mock = MagicMock()
        self.channel_state.last_message_time = time.time() - 39.80
        self.channel_state.start_rate_limit_timer(say_mock)
        self.channel_state.bot = None
        time.sleep(0.5)
        self.assertFalse(say_mock.called)

if __name__ == '__main__':
    unittest.main()