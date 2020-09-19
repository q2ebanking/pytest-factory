# Tornado Drill
intended for unit testing Tornado-based RequestHandler code at the
request/response level with fully offline environment using decorators to
quickly mock up third-party services.
minimal configuration required to start but can be fully customized with inheritable
plugin architecture for custom request/response types. originally developed
within Q2 to unit test complex microservices that make multiple intranet and
internet calls per request/response cycle.

## features
### tornado application code tester
the component under test is a Tornado Application or RequestHandler. a test
suite can define either a single RequestHandler in its settings.py or different
RequestHandler types at the test class or function level. tests run in the
asyncio loop to fully simulate Tornado environment. to minimize modifying the
behavior of the component under test, a method is monkeypatched into the
RequestHandler in order to execute the handler code.
development was done on tornado 6.x.x releases but will likely
function for most other version (results not guaranteed).

### pytest plugin
pytest drives the tests and tornado-drill is architected as a pytest plugin.
see pytest.py for details. though developed on 6.x.x, other versions will likely
function.

### configurability
not only is tornado-drill a plugin, you can develop plugins for tornado-drill!
if your project requires a common set of fixtures and you want to distribute
them to your team, tornado-drill allows you to create plugins using the pytest
plugin framework. not only that, if your team is a large organization, or your
project inherits from a specific customization of Tornado, tornado-drill plugins
can be nested in a hierarchy. for example, your team may use a tornado-drill
plugin that has fixtures common for the project you are working, but also
inherits from another plugin containing fixtures for services shared across the
company

### fixture generation with decorators
live test fixtures are unpredictable and often unavailable. tornado-drill
comes with a set of fixture decorators for common client-server interactions
and tools for users to create their own.
these methods use pytest's monkeypatching feature so their scope is limited to
the test function.

#### decorators
tornado-drill represents fixture decorators with decorators, which are executed
during test collection to generate the fixture for the test being collected.
these decorators can be applied to test classes and functions, allowing the
user to create a hierarchy of default and override fixture settings when
representing the possible permutations of call types and response types in a
complex architecture.

#### included fixture decorators
tornado-drill comes with fixtures for:
- requests package - intercepts outbound calls and route them to http fixtures
- http/smtp/ftp - maps outbound http calls to mock responses
- mock_request - generates an inbound http request

these pre-made fixture decorators can be used as models for users to create
their own. the methods in tornado_drill.framework.helpers can make this as easy
as defining one function containing one function call!

#### fixture parser TODO
fixture decorators can even be generated from file. tornado drill comes with
fixture parser with an interface for users to create their own parser adapters.
the fixture parser can operate in two modes:
- load the fixtures as a module so the user can manually generate tests by
importing the fixtures
- load the fixtures then generate test cases based on the possible permutations
of request and response. see "test generation" below for more details.
examples of types of adapters:
- logging
  - parses requests/responses from logs then generates a test case that
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
tornado drill takes a simpler approach divided into two strategies:

#### descriptive - logs and test report diffing
this technique involves using historical data to generate tests or interpret
new test results.

#### predictive - failure modes
this is just a three step process (for the user):
1. define failure modes for each fixture
  - tornado-drill fixtures like http already have defaults (like 404)
  - can load from file e.g. swagger.yaml
2. define the happy paths
  - use fixture decorators
  - based on requirements
3. run tests and see the generated test results
tornado drill parameterizes your happy path tests by generating a new test case
for each failure mode defined for each fixture defined on that happy test.
if a fixture does not have failure modes defined it will go with the happy path.

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

### conventions
dear contributor, there are countless ways to develop or use this tool, but here
are some conventions that will make code changes minimal and consistent:
- test function names should be unique across the project
    - otherwise it becomes simply too complicated to keep track of tests
- unit testing for unit testing is fundamentally challenging and risks breaking
    pytest normal operation. please observe the following warnings:
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
- do not use pytest_runtest_call as it will execute item.runtest() TWICE if you
    follow pytest official documentation. i do not know if this is a bug or bad
    docs but it will break tornado-drill.

### style and code org
- TODO - pick lint
- all documentation should indicate, where appropriate, who the intended
  user is for that module, class or function:
    - "end user"
      - develops tests for their Tornado server
      - style guide:
        - methods should be easily accessible via imports, including in __init__.py
        - should be thoroughly documented per parameter and fully type-hinted
        - documentation should include examples where relevant
        - code inside these methods should be concise and transparent or carefully
            commented where it is not by necessity
    - "plugin developer"
      - develops tornado-drill plugins
      - style guide:
        - all methods, classes, objects should be defined and imported into the
            settings.py for that plugin
        - any other integrations that require pytest invocations (e.g. pytest.fixture)
            should be in a module that is included in the pytest_plugins defined
            in the user's conftest.py
    - "contributor"
      - develops tornado-drill itself
      - style guide:
        - attributes not intended for direct access should begin with '_'
        - modules and classes not intended for the user should be kept in the
            "framework" directory

### code hotspots
- nested decorators - a debugger can help untangle the order in which these
    get invoked, which exploits how python reads code and pytest's stages to
    "unwrap" each definition at the appropriate time until the final layer,
    the test function itself, gets invoked.
- framework.helpers.get_decorated_callable makes use of sys._getframe():
    - the plugin developer should beware of shimming the call stack (e.g.
        having an intermediate method call get_decorated_callable) as this
        could break how the Stores tracks fixtures
- Hashable - the critical piece to mapping requests to mock responses is
    ensuring that all request classes  have __hash__(self) defined. this allows
    the Store to treat request/response mappings as a pseudo-dict.
    - plugin developers and contributors should think hard about how to hash
        their request object so that similar-enough requests result in the same
        hash value, but different-enough requests get differing values
    - contributors please add to the test coverage of stores.py so that this
        sensitive code is 100% solid!
