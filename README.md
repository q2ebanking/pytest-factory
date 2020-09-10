# Tornado Drill
tornado pytest fixtures as decorators with inheritance

intended for unit testing Tornado-based RequestHandler code at the
request/response level with fully offline environment using decorators to
quickly mock up third-party services. runs in the asyncio loop. minimal
configuration required to start but can be fully customized with inheritable
plugin architecture for custom request/response types. originally developed
within Q2 to unit test complex microservices that make multiple intranet and
internet calls.

## contributing
please look at the unit tests to get an idea of what needs to be done! or if
you think there needs to be a feature, add unit tests! how do you unit test
a test framework? by writing a test using the feature as if it exists, updating
the fake app.py to exhibit the behavior your want to the new feature to test,
then running pytest. write code wherever it throws errors.

there are also TODOs scattered throughout the code where additional work could
yield a new feature.

finally, every function and class ought to have docstrings. framework.helpers
and mock_request in particular require more detail as the code can be
challenging to grasp and anyone working in those files will need all the help
they can get.
