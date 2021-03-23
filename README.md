# pytest-factory
pytest-factory creates request-level unit tests and fixtures for server request
handlers without the need for any server to be listening (yours or anyone
  else's).
currently supports tornado and http.

what is a test factory? see https://docs.pytest.org/en/stable/fixture.html#factories-as-fixtures

pytest-factory extends pytest with decorators that define test factories.
pytest-factory decorators can be applied to both pytest classes and functions allowing
hierarchical and modular factory-reuse.
minimal configuration required to start but can be fully customized with
inheritable plugin architecture for custom request/response types.

originally developed within Q2 to unit test complex microservices that make
multiple asynchronous intranet and internet calls per request/response cycle.


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

from app import MainHandler

pytestmark = pytest.mark.asyncio

@mock_http_server(method='get', path='/hello', response='blah blah')
@mock_request(handler_class=MainHandler, method='get')
class TestClass:
    async def test_a(self, store):
        resp = store.handler.run_test()
        assert resp == 'blah blah'

    @mock_http_server(method='get', path='/hello', response='Hello, world!')
    async def test_b(self, store):
        resp = store.handler.run_test()
        assert resp == 'Hello, world!'
```


## features
### web application back-end testing
the component under test is currently a tornado RequestHandler.

a test suite can define either a single RequestHandler in its settings.py or
different RequestHandler classes at the test class or function level. tests
currently run in the asyncio loop to fully simulate tornado environment but can
be updated to be generic.

### pytest plugin
pytest drives the tests and pytest-factory is architected as a pytest plugin.
see pytest.py for details. though developed on 6.x.x, other versions will
likely function.

### configurability
if your project requires a common set of fixtures and you want to distribute
them to your team, pytest-factory allows you to create plugins using the pytest
plugin framework. not only that, if your team is a large organization, or your
project inherits from a specific customization of tornado, pytest-factory
plugins can be nested in a hierarchy. for example, your team may use a
pytest-factory plugin with factories for fixtures the team commonly uses, but
also inherits from a company-distributed plugin for services shared across the
company.

### factories as decorators
pytest-factory comes with a set of factories for common client-server
interactions and tools for users to create their own.
these methods use pytest's monkeypatching feature so their scope is limited to
the test function.

#### decorators
pytest-factory represents fixture factories with decorators, which are executed
during test collection to create the fixture for the test being collected.
these factories can be applied to test classes and functions, allowing the
user to create a hierarchy of default and override fixture settings when
representing the possible permutations of call types and response types.

#### included factories
pytest-factory comes with factories for:
- requests package - intercepts outbound calls and route them to http fixtures
- http/smtp/ftp - maps outbound http calls to mock responses
- mock_request - mocks an inbound http request

these pre-made factories can be used as models for users to create their own.
the methods in pytest_factory.framework.helpers can make this as easy as
defining one function containing one function call!

## future dev
listed in order of increasing complexity:

### hybrid testing
outbound calls not intercepted by fixtures can be allowed to connect to allow
hybrid, offline/online functional/integration testing by configuring the user's
`Settings.allow_outbound_calls = True`

### wildcard routing
fixture routes can be defined as wildcards using regex and respond in lower
priority to matching outbound requests

### support for other frameworks
this project is purposefully organized to enable support for other web service
frameworks like django or flask.
someone familiar with those frameworks will need to write something equivalent
to pytest_factory.mock_request though this could be made easier.

### factory parser
the factory parser loads fixture factories from file and has an interface for
plugin developers to create parser adapters. the factory parser can load the 
factories as a module so the user can manually create tests by
importing and applying them where needed

examples of types of parser adapters:
- logged requests/responses, parsed from either:
  - user's request handler can inherit pytest-factory.handler_mixin which adds
    pytest_factory breadcrumbs in logs
  - user-defined log parser if existing logger already provides
    request/response data
- WSDL, swagger or similar service interface contracts
  - creates fixture module

### support for other languages
support for non-python frameworks like node or rails is an eventual goal.

### caveats
testing a test framework is fundamentally challenging. please beware of the
following limitations in the current code (re: please submit a PR with a better way!:
- test function names must be unique across the project or you get fixture
  collision
- the following are functionally tested and may require more work than is
    worthwhile to unit test:
    - framework/helpers.py
    - framework/requests.py
    - framework/pytest.py
- http.py has highly specialized, tightly coupled tests. please read
    comments before updating
- when possible please use the included logger in framework/settings/LOGGER,
    especially if pytest is suppressing your print or warn statements or if you
    need to assert that a warning/error was emitted by your test code or if you
    are trying to emit from teardown (which pytest is hardcoded to suppress).
- if you define pytest_runtest_call in pytest.py and
    execute it within your pytest_runtest_call, it will execute
    item.runtest() TWICE. i do not know if this is a bug
    or incorrect pytest documentation but it can break pytest-factory and will cause confusing
    behavior.
- nested decorators - if you get confused, as i did, use a debugger to follow
    their execution.
- Hashable - all classes representing a request must define __hash__().
    - allows the Store to treat request/response mappings as a pseudo-dict.
    - hashing algorithms must be loose enough so that similar-enough requests result in the same
        hash value, but different-enough requests get differing values.

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
