import re
from pathlib import Path

from jinja2 import Template

from pytest_factory.framework.mall import MALL
from pytest_factory.lifecycle.recording import Recording


def get_package_path(file_path: str):
    p = Path(__file__).parent
    return p.joinpath(file_path)


class Writer:
    """
    the default test writer writes pytest unit tests
    """

    def __init__(self, recording: Recording):
        self.recording = recording
        sut_callable = recording.first.sut_callable
        self.handler_path, self.handler_name = sut_callable.__module__, sut_callable.__name__

    def write_test(self, output_path: Path):
        """
        writes a test module that reproduces the recorded session
        """

        new_data_path = MALL.get_full_path("test_factory_tests/actual_response")
        template_path = get_package_path("template.py.jinja")
        with open(output_path, "w") as test_file:
            with open(template_path) as template_file:
                template = Template(template_file.read())
            request_factory_path, request_factory_name = self.recording.request_factory
            incident_name = self.recording.incident_type.__name__
            generated_test_id = re.sub(r'(?<!^)(?=[A-Z])', '_', incident_name).lower()
            inputs = {
                'recording': self.recording,
                'incident_name': incident_name,
                'handler_path': self.handler_path,
                'handler_name': self.handler_name,
                'request_factory_path': request_factory_path,
                'request_factory_name': request_factory_name,
                'generated_test_id': generated_test_id,
                'response_attributes': {
                    'status',
                    'body'
                },
                'assert_reproduction_as_success': MALL.assert_reproduction_as_success
            }

            test_module_str = template.render(**inputs)

            test_file.write(test_module_str)
        sut_response = self.recording.last
        if not self.recording.raises:
            if not isinstance(sut_response, str):
                sut_response = sut_response.serialize()
            with open(new_data_path, "w") as data_file:
                data_file.write(sut_response)
