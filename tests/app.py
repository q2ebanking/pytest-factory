import requests

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application


class MainHandler(RequestHandler):
    async def get(self):
        if self.request.path == 'solo':
            self.write("Hello, world")
        elif self.request.path == 'something':
            self.write("yay")
        else:
            resp = requests.get(url='http://www.test.com/mock_endpoint')
            self.write(resp.content)



def make_app():
    return Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
