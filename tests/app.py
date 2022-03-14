import requests

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

base_url = 'http://www.test.com/mock_endpoint'


class MainHandler(RequestHandler):
    async def get(self):
        if self.request.path == 'solo':
            self.write('Hello, world')
        elif self.request.path == 'something':
            self.write('yay')
        elif self.request.path == 'query_params_test':
            query_str = '?wild=card'
            resp = requests.get(url=base_url + query_str)
            self.write(resp.content)
        else:
            num = int(self.get_query_argument(name='num', default='1'))
            resp_return = ''
            for _ in range(num):
                resp = requests.get(url=base_url)
                resp_return += resp.content
            self.write(resp_return)


def make_app():
    return Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
