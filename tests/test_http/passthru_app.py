import json
import requests
from urllib.parse import urlencode

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

test_url_map = {
    'endpoint0': 'http://www.test.com',
    'plugin0': 'http://somedomain.com'
}


class PassthruTestHandler(RequestHandler):
    def _handle_passthru(self, http_method: str = 'get'):
        service_name = self.request.uri.split('/')[0].split('?')[0]
        url = test_url_map.get(service_name)
        query_args = {k: v[0].decode() for k, v in self.request.query_arguments.items() if k != 'num'}

        query_str = '?' + urlencode(query=query_args) if query_args else ""
        final_url = f"{url}/{self.request.path}{query_str}"
        num_calls = int(self.get_query_argument(name='num', default='1'))
        resp_str = ''
        for _ in range(0, num_calls):
            call, args = getattr(requests, http_method), {'url': final_url}
            if http_method == 'post':
                body = json.loads(self.request.body)
                args['json'] = body
            try:
                resp = call(**args)
            except requests.RequestException as rex:
                resp_str += f'caught RequestException: {rex}'
            else:
                resp_str += resp.content.decode() if resp.content else f"ERROR: {resp.status_code}"
                self.set_status(resp.status_code or 200)
        self.write(resp_str)

    async def get(self):
        self._handle_passthru()

    async def post(self):
        self._handle_passthru(http_method='post')


def make_app():
    return Application([
        (r"/", PassthruTestHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
