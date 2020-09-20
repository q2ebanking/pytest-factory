# pytest-factory
pytest-factory creates request-level unit tests and fixtures for server request
handlers without the need for any server to be listening (yours or anyone
  else's).
currently supports tornado and http.

what is a factory? see https://docs.pytest.org/en/stable/fixture.html#factories-as-fixtures

pytest-factory takes that concept of factories as functional fixtures one step
further: factories as decorators.
decorators can be applied to both pytest classes and functions allowing
hierarchical and modular fixture-reuse.
minimal configuration required to start but can be fully customized with
inheritable plugin architecture for custom request/response types.

originally developed within Q2 to unit test complex microservices that make
multiple asynchronous intranet and internet calls per request/response cycle.

*NOTE*
as with all software tools, this can be used to encourage both good and bad
laziness. pytest-factory is NOT a substitute for human-written tests! it does
not guarantee your code will work, it just guarantees it will not break in the
ways that it tells you about. it is still the responsibility of a human
developer to decide the happy path and validate the behavior that
pytest-factory reports with real-world data.

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
the features of

#### decorators
pytest-factory represents fixture factories with decorators, which are executed
during test collection to create the fixture for the test being collected.
these factories can be applied to test classes and functions, allowing the
user to create a hierarchy of default and override fixture settings when
representing the possible permutations of call types and response types in a
complex architecture.

#### included factories
pytest-factory comes with factories for:
- requests package - intercepts outbound calls and route them to http fixtures
- http/smtp/ftp - maps outbound http calls to mock responses
- mock_request - mocks an inbound http request

these pre-made factories can be used as models for users to create their own.
the methods in pytest_factory.framework.helpers can make this as easy as
defining one function containing one function call!

## future dev
listed in order of difficulty:

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
plugin developers to create parser adapters. the factory parser can operate in
two modes:
- load the factories as a module so the user can manually create tests by
importing and applying them where needed
- load the factories then produce test cases based on the possible permutations
of request and response. see "test parameterization" below for more details.

examples of types of parser adapters:
- logged requests/responses, parsed from either of:
  - user's request handler can inherit pytest-factory.handler_mixin which adds
    pytest_factory breadcrumbs in logs
  - user-defined log parser if existing logger already provides
    request/response data
- WSDL, swagger or similar service interface contracts
  - creates fixture module
  - if interfaces are sufficiently defined can create test suite

### support for other languages
support for non-python frameworks like node or rails is an eventual goal.

### test parameterization
pytest-factory takes a simple, domain model approach to semi-automating
test parameterization. new tests are extrapolated from existing test cases by
comparing differences in the requests and responses of each service or model.
these differences can be reported along several dimensions:
- time
- logs vs test logs
- failure modes for each fixture
- test pass vs fail

the parameters reported are saved in a hidden file for analysis:
`.pytest-factory/<test_name>/<timestamp>`
as well as a file to track the current state of each test:
`.pytest-factory/<test_name>/current_expectations`
it's up to the user if they want to git add all, none or just the
current_expectations file.

if any parameterized assertion fails and it's because the expectations have
changed, the user can either specify a test or for all tests call:
`pytest-factory --update-expected [test-name]`
or just:
`pytest-factory -u [test-name]`
or edit the current_expectations file directly:
  1. comment out or delete the line that references a given test's data
    (represented as a timestamp) or set the timestamp to be the latest test's
    timestamp
  2. next time pytest_factory runs, for each test missing from
  current_expectations, that file is updated from last timestamp's test data

the data plus the following pytest_factory tools provide the user with multiple
strategies for discovering errors in their code or tests or to update the
expected behavior if the new behavior is correct. these strategies can be
divided in two categories:

#### descriptive - logs and test report diffing
these strategies use historical data to validate or create tests and
vary on the type of data:
- pytest_factory.parameterization.parse_logs
  1. user marks their test or test module with parse_logs
  2. user configures log parser to use either adapter or breadcrumbs
  3. parse_logs creates fixtures' requests/responses from logs
  4. define and collect new test function that asserts logged responses match
      mock/test responses
- pytest_factory.parameterization.diff_recordings
  1. user marks their test or test module with diff_recordings
  2. define and collect new test function that asserts that last recorded
    responses and handler logs match current test's

#### predictive - failure modes
this strategy predicts what behavior will be from known requirements as defined
by the user and any services they are connecting to.
this is just a three step process (for the user):
1. mark tests with pytest_factory.parameterization.cause_failures
2. define failure_modes when calling or defining factories
  - pytest-factory factories like mock_http_server already have defaults
      (like 404)
  - can load from file see "factory parser"
3. define the happy paths
  - use fixture factories
  - based on requirements
4. run tests and see the parameterized test results
5. optionally, when parameterizing a test or factory run:
  `pytest-factory --reify [test-name|factory-name]`
  or for all tests:
  `pytest-factory -r`
  to have pytest-factory write the code for the parameterized tests to file for
  the user to review or customize. the generated code will be marked with
  comments saying it was written by pytest-factory.

## contributing
please look at "future dev" and the unit tests (either failing or missing
cases) to get an idea of what needs to be done! or if you think there needs to
be a feature, add unit tests!
how do you unit test a test framework? by writing a test using the feature as
if it exists, updating the fake app.py to exhibit the behavior you want the new
feature to test. if you're still lost at that point, just run pytest and write
code wherever it throws errors.

there are also TODOs scattered throughout the code where additional work could
yield a new feature.

### caveats
testing a test framework is fundamentally challenging. please beware of the
following limitations in the current code:
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
