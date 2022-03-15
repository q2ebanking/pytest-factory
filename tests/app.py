import requests
from urllib.parse import parse_qs

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

base_url = 'http://www.test.com/mock_endpoint'

plugin_url = 'http://somedomain.com'


class MainHandler(RequestHandler):
    # TODO restructure as a simple passthru so we can reuse the inbound params as the outbound params?
    async def get(self):
        if self.request.path == 'solo':
            self.write('Hello, world')
        elif self.request.path == 'something':
            self.write('yay')
        elif self.request.path == 'factory_plugin':
            responses = []
            for service, [param] in self.request.query_arguments.items():
                body = {
                    'service_name': service,
                    'service_param': param
                }
                resp = requests.get(url=plugin_url, json=body)
                responses.append(str(resp.content))
            self.write(','.join(responses))
        elif self.request.path == 'query_params_test':
            query_str = self.request.query
            resp = requests.get(url=f'{base_url}?{query_str}')
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
