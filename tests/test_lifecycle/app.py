from pytest_factory.lifecycle.recorder.tornado import TornadoRecorderRequestHandler
from pytest_factory.lifecycle.recording import LiveException

dependency_url = 'http://some.dependency.net'


class InstrumentedHandler(TornadoRecorderRequestHandler):
    async def get(self):
        if self.request.path == 'dependency':
            self.call_get(url=dependency_url)

        me = LiveException()
        self.send_error(exception=me)
