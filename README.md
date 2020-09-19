# pytest-factory
pytest-factory fixture factories create request-level unit tests and fixtures
for server request handlers without the need for any server to be listening
(yours or anyone else's).
currently supports just tornado and http.

fixture factories are implemented as decorators that can be applied to pytest
classes and functions allowing fixture-reuse and programmability.
fixture factories
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
    async def get(self)::
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

your test.py (contrived to illustrate point on decorators as fixture
factories):
```python
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
### web application back-end test factory
the component under test is currently a tornado Application or RequestHandler
but the code is currently being updated to be generic for any network-based
request handler.

a test suite can define either a single RequestHandler in its settings.py or
different RequestHandler types at the test class or function level. tests
currently run in the asyncio loop to fully simulate tornado environment but can
be updated to be generic.

to minimize modifying the behavior of the component under test, a method is
monkeypatched into the RequestHandler in order to execute the handler code.

### pytest plugin
pytest drives the tests and pytest-factory is architected as a pytest plugin.
see pytest.py for details. though developed on 6.x.x, other versions will
likely function.

### configurability
if your project requires a common set of fixtures and you want to distribute
them to your team, pytest-factory allows you to create plugins using the pytest
plugin framework. not only that, if your team is a large organization, or your
project inherits from a specific customization of tornado, pytest-factory
plugins can be nested in a hierarchy. for example, your team may use a pytest-
factory plugin that has fixtures common for the project you are working, but
also inherits from another plugin containing fixtures for services shared
across the company.

### fixture factories with decorators
live test fixtures are unpredictable and often unavailable. pytest-factory
comes with a set of fixture factories for common client-server interactions
and tools for users to create their own.
these methods use pytest's monkeypatching feature so their scope is limited to
the test function.

#### decorators
pytest-factory represents fixture factories with decorators, which are executed
during test collection to create the fixture for the test being collected.
these factories can be applied to test classes and functions, allowing the
user to create a hierarchy of default and override fixture settings when
representing the possible permutations of call types and response types in a
complex architecture.

#### included fixture factories
pytest-factory comes with factories for:
- requests package - intercepts outbound calls and route them to http fixtures
- http/smtp/ftp - maps outbound http calls to mock responses
- mock_request - generates an inbound http request

these pre-made factories can be used as models for users to create their own.
the methods in pytest_factory.framework.helpers can make this as easy as
defining one function containing one function call!

#### fixture factory parser TODO
factories can even be generated from file. pytest-factory comes with a
factory parser with an interface for users to create their own parser adapters.
the factory parser can operate in two modes:
- load the factories as a module so the user can manually generate tests by
importing and applying them where needed
- load the factories then produce test cases based on the possible permutations
of request and response. see "test generation" below for more details.
examples of types of adapters:
- logging
  - parses requests/responses from logs then generate test case that
matches the live behavior
  - TODO maybe add a logging adapter that will format logs to leave breadcrumbs
    for this parser?
- WSDL, swagger or similar service interface contracts
  - generates fixture module
  - if interfaces are sufficiently defined can generate test suite


### test generation - not yet implemented
test generation is generally speaking an unsolved problem and attempts often
involve code analysis or variations of genetic algorithms to mutate inputs or
other computationally intensive and/or insufficiently precise for a given
domain (for example in http server testing there is usually no improvement in
test coverage from randomizing url and query params).
pytest-factory takes a simpler approach divided into two strategies:

#### descriptive - logs and test report diffing
this technique involves using historical data to generate tests or interpret
new test results.

#### predictive - failure modes
this is just a three step process (for the user):
1. define failure modes for each fixture
  - pytest-factory factories like mock_http_server already have defaults
      (like 404)
  - can load from file e.g. swagger.yaml
2. define the happy paths
  - use fixture factories
  - based on requirements
3. run tests and see the generated test results
pytest-factory parameterizes your happy path tests by generating a new test
case for each failure mode defined for each factory that created a fixture for
that happy path.
if a fixture does not have failure modes defined it will go with the happy
path.

####

## contributing
please look at the unit tests (either failing or missing cases) to get an idea
of what needs to be done! or if you think there needs to be a feature, add unit
tests!
how do you unit test a test framework? by writing a test using the feature as
if it exists, updating the fake app.py to exhibit the behavior your want to the
new feature to test, then running pytest. write code wherever it throws errors.

there are also TODOs scattered throughout the code where additional work could
yield a new feature.

### caveats
testing a test framework is fundamentally challenging. please beware of the
following limitations in the current code:
- test function names must be unique across the project
    - otherwise you get fixture collision
    - TODO find way to make test names include module at least?
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
- do not define pytest_runtest_call in pytest.py as it will execute
    item.runtest() TWICE if you follow pytest official documentation and
    execute it within your pytest_runtest_call. i do not know if this is a bug
    or bad docs but it can break pytest-factory and will cause confusing
    behavior.
- nested decorators - if you get confused, as i did, use a debugger to follow
    their execution.
- Hashable - all classes representing a request must define __hash__().
    - allows the Store to treat request/response mappings as a pseudo-dict.
    - plugin developers and contributors should think hard about how to hash
        their request object so that similar-enough requests result in the same
        hash value, but different-enough requests get differing values

### style and code org
- TODO - pick lint
- all documentation should indicate, where appropriate, who the intended
  user is for that module, class or function:
    - "end user"
      - develops tests for their tornado server
      - style guide:
        - methods should be easily accessible via imports, including in
            __init__.py
        - should be thoroughly documented per parameter and fully type-hinted
        - documentation should include examples where relevant
        - code inside these methods should be concise and transparent or
            carefully commented where it is not by necessity
    - "plugin developer"
      - develops pytest-factory plugins
      - style guide:
        - all methods, classes, objects should be defined and imported into the
            settings.py for that plugin
        - any other integrations that require pytest invocations (e.g.
            pytest.fixture) should be in a module that is included in the
            pytest_plugins defined in the user's conftest.py
    - "contributor"
      - develops pytest-factory itself
      - style guide:
        - attributes not intended for direct access should begin with '_'
        - modules and classes not intended for the user should be kept in the
            "framework" directory
