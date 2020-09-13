# Tornado Drill
tornado pytest fixtures as decorators with inheritance

intended for unit testing Tornado-based RequestHandler code at the
request/response level with fully offline environment using decorators to
quickly mock up third-party services. runs in the asyncio loop. minimal
configuration required to start but can be fully customized with inheritable
plugin architecture for custom request/response types. originally developed
within Q2 to unit test complex microservices that make multiple intranet and
internet calls per request/response cycle.

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
- please remain consistent in considering and documenting who the given
    method or class is intended for:
    - "user" - is working on tests for their Tornado server
        - methods should be easily accessible via imports, including in __init__.py
        - should be thoroughly documented per parameter and fully type-hinted
        - documentation should include examples where relevant
        - code inside these methods should be concise and transparent or carefully
            commented where it is not by necessity
    - "plugin developer" - is working on a tornado-drill plugin
        - all methods, classes, objects should be defined and imported into the
            settings.py for that plugin
        - any other integrations that require pytest invocations (e.g. pytest.fixture)
            should be in a module that is included in the pytest_plugins defined
            in the user's conftest.py
    - "contributor" - is working on tornado-drill itself
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