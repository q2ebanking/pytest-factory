tornado pytest fixtures as decorators with inheritance


conftest.py
- required import of settings
- loads first when running pytest

settings.py
- actually a hierarchy of plugin settings collapsed into single object
- stored at the original settings.py as SETTINGS global

test_x.py
- tests are being read and decorators executed

request_handler.py or 

wrapper.py
- registers

store.py
- initialized from settings when first imported
