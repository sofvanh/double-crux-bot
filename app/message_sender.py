import asyncio


class MessageSender:
    def send(self, message):
        raise NotImplementedError(
            "This method should be implemented by subclasses.")


class SyncMessageSender(MessageSender):
    def __init__(self, send):
        self.send = send

    def send(self, message):
        self.send(message)


class AsyncMessageSender(MessageSender):
    def __init__(self, send_coroutine, loop):
        self.send_coroutine = send_coroutine
        self.loop = loop

    def send(self, message):
        asyncio.run_coroutine_threadsafe(
            self.send_coroutine(message), self.loop)
