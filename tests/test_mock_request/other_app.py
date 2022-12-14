from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application


class MockRequestTestHandler(RequestHandler):
    async def get(self):
        if self.request.path == 'solo':
            self.write('Hello, world')
        elif self.request.path == 'something':
            self.write('yay')
        else:
            self.write('')


def make_app():
    return Application([
        (r"/", MockRequestTestHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
