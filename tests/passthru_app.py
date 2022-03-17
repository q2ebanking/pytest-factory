import json
import requests

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

test_url_map = {
    'endpoint0': 'http://www.test.com',
    'plugin0': 'http://somedomain.com'
}


class PassthruTestHandler(RequestHandler):
    async def get(self):
        service_name = self.request.uri.split('/')[0]
        url = test_url_map.get(service_name)
        final_url = f"{url}/{self.request.path}"
        resp = requests.get(url=final_url)
        return resp.content

    async def post(self):
        service_name = self.request.uri.split('/')[0]
        body = json.loads(self.request.body)
        url = test_url_map.get(service_name)
        final_url = f"{url}/{self.request.path}"
        resp = requests.post(url=final_url, json=body)
        return resp.content


def make_app():
    return Application([
        (r"/", PassthruTestHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
