tornado pytest fixtures as decorators with inheritance


conftest.py
- required import of settings
- loads first when running pytest

settings.py
- actually a hierarchy of plugin settings collapsed into single object
- stored at the original settings.py as SETTINGS global

test_x.py
- tests are being read and decorators executed

mock_request.py
- instantiates request object
- applies overrides
- updates store with request object
- iterates over test methods if decorator applies to class

http/mock_http_server.py
-

wrapper.py
- updates store with mock response

store.py
- initialized from settings when first imported
