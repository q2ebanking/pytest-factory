import json
from smtplib import SMTP, SMTPException

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

test_url_map = {
    'endpoint0': 'smtp.test.com:25',
    'endpoint1': 'smtp.somedomain.com'
}


class SmtpTestHandler(RequestHandler):
    async def post(self):
        body_dict = json.loads(self.request.body.decode())
        to_addrs = body_dict.get('to_addrs')
        from_addr = body_dict.get('from_addr')
        msg = body_dict.get('msg')
        host = test_url_map.get(self.request.path)
        smtp_client = SMTP(host=host)
        try:
            response = smtp_client.sendmail(from_addr=from_addr, to_addrs=to_addrs, msg=msg)
        except SMTPException as se:
            response = str(se)
        self.write(str(response))


def make_app():
    return Application([
        (r"/", SmtpTestHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
