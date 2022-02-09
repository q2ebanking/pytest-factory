"""
"""
import logging


# this is to enable making assertions that the framework is logging expected warnings
class Logger(logging.Logger):
    def __init__(self):
        super().__init__(name='pytest-factory-logger')
        self.buffer = []

    def format(self, msgs) -> str:
        return ''.join([f'\npytest-factory WARNING: {msg}' for msg in msgs])

    def warning(self, *msgs):
        msg = self.format(msgs)
        super().warning(msg=msg)
        self.buffer.append(msg)


LOGGER = Logger()
