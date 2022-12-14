# pytest-factory
pytest-factory creates a test environment for your service using decorators on 
test classes/methods to generate configurable and reusable test doubles. it accomplishes this
by monkeypatching the system-under-test (SUT) (as little as possible), its environment
variables, and the packages it uses to connect with its depended-on-components (DOC).

DOC packages supported:
* requests
* smtplib
* aiohttp

SUT packages supported:
* tornado

Requires pytest >= 7.x.x

## example
given a tornado application app.py (see tests/ for a more complex
examples):
```python
#app.py
import requests

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application


class MainHandler(RequestHandler):
    async def get(self):
        resp = requests.get(url='https://www.world.com/hello')
        self.write(resp.content)


def make_app():
    return Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()

```

```python
#conftest.py
pytest_plugins = ["pytest_factory.framework.pytest"]

```

```ini
;config.ini
[tests]
requests = pytest_factory.monkeypatch.requests
tornado = pytest_factory.monkeypatch.tornado
imports = requests, tornado
```

```python
#test.py
import pytest
from pytest_factory import mock_http_server
from pytest_factory.monkeypatch.tornado import tornado_handler

from app import MainHandler

pytestmark = pytest.mark.asyncio


@mock_http_server(method='get', url='https://www.world.com/hello', response='blah blah')
@tornado_handler(sut_callable=MainHandler, method='get')
class TestClass:
    async def test_a(self, store):
        resp = await store.sut.run_test()
        assert resp.body.decode() == 'blah blah'

    @mock_http_server(method='get', url='https://www.world.com/hello', response='Hello, world!')
    async def test_b(self, store):
        resp = await store.sut.run_test()
        assert resp.body.decode() == 'Hello, world!'

```

## features
### Tornado application back-end testing
currently, the component under test must be a tornado RequestHandler.

a test suite can define either a single RequestHandler in its settings.py or
different RequestHandler classes at the test class or function level.

### pytest plugin
pytest drives the tests and pytest-factory is a pytest plugin. 
see pytest_factory.framework.pytest

### what is a factory?
a factory is a decorator that creates test doubles and puts them in a Store. the decorator modifies a pytest
TestClass or test_method_or_function. test doubles can be functions that map inputs to outputs. the Store is
unique to each test method and can be accessed from a pytest fixture called "store". the Store records any
inputs and outputs to the Store during the test in its "messages" property.

#### decorators
pytest-factory factories are decorators, which are executed
during test collection to create the test doubles for the test being collected.
these factories can be applied to test classes, methods and functions, enabling the
user to make their test double code DRY.

#### included factories
pytest-factory comes with several factories:
- mock_http_server - creates a fake http service DOC
- tornado_handler - creates a fake Tornado RequestHandler SUT

see pytest_factory.framework.factory.make_factory to create your own.

## future dev
listed in order of increasing complexity:

### proper capitalization
the original developer of this project is lazy about capitalization. please help!

### support for ftplib

### support for aiohttp
see pytest_factory.monkeypatch.requests for an example of what is needed.

### support for other python web frameworks
someone familiar with those frameworks will need to write something equivalent
to pytest_factory.monkeypatch.tornado.

### support for other languages/frameworks
support for non-python frameworks like node or rails is an eventual goal.