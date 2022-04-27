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

## example
given a tornado application app.py (see tests/app.py for a more complex
example):
```python
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

touch conftest.py:
```python
from pytest_factory.framework.parse_configs import prep_stores_update_local

prep_stores_update_local(dir_name=__name__)

pytest_plugins = ["pytest_factory.framework.pytest"]
```

touch config.ini:
```ini
[default]
requests = pytest_factory.monkeypatch.requests
tornado = pytest_factory.monkeypatch.tornado
imports = requests, tornado
```

touch test.py:

```python
import pytest
from pytest_factory import mock_http_server
from pytest_factory.monkeypatch.tornado import tornado_handler

from .app import MainHandler

pytestmark = pytest.mark.asyncio


@mock_http_server(method='get', path='https://www.world.com/hello', response='blah blah')
@tornado_handler(handler_class=MainHandler, method='get')
class TestClass:
    async def test_a(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'blah blah'

    @mock_http_server(method='get', path='https://www.world.com/hello', response='Hello, world!')
    async def test_b(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'Hello, world!'

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

### caveats
testing a test framework is fundamentally challenging. please beware of the
following limitations in the current code (re: please submit a PR with a better way!):
- test function names must be unique across the project or you will have test double
  collision
- when possible please use the included logger in pytest_factory.framework.logger,
    especially if pytest is suppressing your print or warn statements or if you
    need to assert that a warning/error was emitted by your test code or if you
    are trying to emit from teardown (which pytest is hardcoded to suppress).
- if you define pytest_runtest_call in pytest.py and
    execute it within your pytest_runtest_call, it will execute
    item.runtest() TWICE. i do not know if this is a bug
    or incorrect pytest documentation, but it can break pytest-factory and will cause confusing
    behavior.
