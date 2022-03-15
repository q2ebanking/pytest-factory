# pytest-factory

pytest-factory creates a test environment for your tornado service using decorators on 
test classes/methods to generate configurable and reusable test doubles of:
* inbound requests
* responses to outbound requests

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
        self.write(resp.text)


def make_app():
    return Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
```

your conftest.py:
```python
pytest_plugins = "pytest_factory.framework.pytest"
```

your test.py:
```python
import pytest
from pytest_factory import mock_request, mock_http_server

from tests.app import MainHandler

pytestmark = pytest.mark.asyncio

@mock_http_server(method='get', path='/hello', response='blah blah')
@mock_request(handler_class=MainHandler, method='get')
class TestClass:
    async def test_a(self, store):
        resp = await store.handler.run_test()
        assert resp == 'blah blah'

    @mock_http_server(method='get', path='/hello', response='Hello, world!')
    async def test_b(self, store):
        resp = await store.handler.run_test()
        assert resp == 'Hello, world!'
```


## features
### Tornado application back-end testing
currently, the component under test must be a tornado RequestHandler.

a test suite can define either a single RequestHandler in its settings.py or
different RequestHandler classes at the test class or function level.

### pytest plugin
pytest drives the tests and pytest-factory is a pytest plugin.

in addition, extensions to pytest-factory are also pytest plugins and are loaded
via conftest.py. this enables distributing commonly used
factories within a development organization. see the tests for an example of such
a plugin.

### what is a factory?
a factory is a decorator that creates test doubles. the decorator modifies a pytest
TestClass or test_method_or_function. these test doubles record inputs, can invoke
a Callable to map inputs to outputs, and are all accessible from a pytest fixture 
called "store". 

#### decorators
pytest-factory factories are decorators, which are executed
during test collection to create the test doubles for the test being collected.
these factories can be applied to test classes, methods and functions, enabling the
user to make their test fixture code DRY.

#### included factories
pytest-factory comes with factories for:
- http/smtp/ftp - test doubles for responses to outbound requests
- mock_request - test double for inbound http request for a Tornado RequestHandler

see pytest_factory.framework.factory.make_factory to create your own.

## future dev
listed in order of increasing complexity:

### support for other web frameworks
this project is purposefully organized to enable support for other web service
frameworks like django or flask.
someone familiar with those frameworks will need to write something equivalent
to pytest_factory.mock_request though this could be made easier.

### support for aiohttp, httplib, etc
currently, this project only supports requests.

### support for other languages/frameworks
support for non-python frameworks like node or rails is an eventual goal.

### caveats
testing a test framework is fundamentally challenging. please beware of the
following limitations in the current code (re: please submit a PR with a better way!:
- test function names must be unique across the project or you get fixture
  collision
- the following are functionally tested and may require more work than is
    worthwhile to unit test:
    - framework/factory.py
    - requests.py
    - framework/pytest.py
- http.py has highly specialized, tightly coupled tests. please read
    comments before updating
- when possible please use the included logger in pytest_factory.framework.logger,
    especially if pytest is suppressing your print or warn statements or if you
    need to assert that a warning/error was emitted by your test code or if you
    are trying to emit from teardown (which pytest is hardcoded to suppress).
- if you define pytest_runtest_call in pytest.py and
    execute it within your pytest_runtest_call, it will execute
    item.runtest() TWICE. i do not know if this is a bug
    or incorrect pytest documentation but it can break pytest-factory and will cause confusing
    behavior.

### style and code structure
besides PEP and general code hygiene, the following guidance is recommended,
organized by user role:
- "end user"
  - develops tests for their tornado server
  - code for their use should:
    - have functions be easily accessible via imports, including in
        __init__.py
    - be thoroughly documented per parameter and return value
    - be fully type-hinted
    - document examples where relevant
- "plugin developer"
  - develops pytest-factory plugins
  - plugin code should:
    - be imported into the settings.py for that plugin
    - define or import all pytest invocations (e.g. pytest.fixture) in a single
      module that will be included in end user's conftest.pytest_plugins
- "contributor"
  - develops pytest-factory itself
  - contributed code should:
    - "hide" with '_' attributes not intended for the end user
    - keep modules and classes not intended for the end user in "framework"
