# Tornado Drill
tornado pytest fixtures as decorators with inheritance

intended for unit testing Tornado-based RequestHandler code at the
request/response level with fully offline environment using decorators to
quickly mock up third-party services. runs in the asyncio loop. minimal
configuration required to start but can be fully customized with inheritable
plugin architecture for custom request/response types. originally developed
within Q2 to unit test complex microservices that make multiple intranet and
internet calls.
