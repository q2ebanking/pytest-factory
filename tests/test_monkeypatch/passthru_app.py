import json
from urllib.parse import urlencode

from aiohttp.client import ClientSession, ClientError
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

test_url_map = {
    'endpoint0': 'http://www.test.com',
    'plugin0': 'http://somedomain.com'
}


class PassthruTestHandler(RequestHandler):
    async def _handle_passthru(self, http_method: str = 'get'):
        service_name = self.request.uri.split('/')[0].split('?')[0]
        url = test_url_map.get(service_name)
        query_args = {k: v[0].decode() for k, v in self.request.query_arguments.items() if k != 'num'}

        query_str = '?' + urlencode(query=query_args) if query_args else ""
        final_url = f"{url}/{self.request.path}{query_str}"
        num_calls = int(self.get_query_argument(name='num', default='1'))
        resp_str = ''
        args = {}
        if http_method == 'post':
            body = json.loads(self.request.body)
            args['json'] = body
        async with ClientSession() as session:
            for _ in range(0, num_calls):
                try:
                    async with session.request(method=http_method, url=final_url, **args) as resp:
                        resp_str += await resp.text() or f"ERROR: {resp.status}"
                        self.set_status(resp.status or 200)
                except ClientError as ce:
                    resp_str += f'caught RequestException: {ce}'

        self.write(resp_str)

    async def get(self):
        await self._handle_passthru()

    async def post(self):
        await self._handle_passthru(http_method='post')


def make_app():
    return Application([
        (r"/", PassthruTestHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
