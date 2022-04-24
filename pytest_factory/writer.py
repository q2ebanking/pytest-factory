from typing import List

from black import format_str, FileMode
from jinja2 import Template
from requests import Response

from pytest_factory.http import MockHttpRequest
from pytest_factory.recorder.recording import Recording, reify

# TODO find a home for this
assert_reproduction_as_success = True


def parse(logs: List[str]) -> Recording:
    if len(logs) < 2:
        raise Exception  # TODO
    exchange_objects = []
    requests = []
    responses = []
    for log_line in logs:
        new_obj = reify(path=log_line)
        if isinstance(new_obj, MockHttpRequest):
            requests.append(new_obj)
        else:
            responses.append(new_obj)
        matching_pair_indices = tuple()
        for i, request in enumerate(requests):
            for j, response in enumerate(responses):
                if request.exchange_id == response.exchange_id:
                    matching_pair_indices = (i, j)
        matching_request = requests.pop(matching_pair_indices[0])
        matching_response = responses.pop(matching_pair_indices[1])
        exchange_objects.append(tuple({matching_request, matching_response}))
    doc_exchanges = exchange_objects[1:] if len(exchange_objects) > 1 else []
    recording = Recording(sut_exchange=exchange_objects[0], doc_exchanges=doc_exchanges)
    return recording


class Writer:
    def __init__(self, recording: Recording, handler_path: str):
        self.recording = recording
        self.handler_path, self.handler_name = handler_path.rsplit('.', 1)

    def write_test(self, output_path: str = 'tests/test_file.py'):
        """
        writes a test module that reproduces the recorded session
        returns file path
        """
        new_data_path = f"tests/actual_response"
        template_path = f"pytest_factory/template.py.jinja"
        with open(output_path, "x") as test_file:
            with open(template_path) as template_file:
                template = Template(template_file.read())
            request_factory_path, request_factory_name = self.recording.request_factory
            inputs = {
                'recording': self.recording,
                'incident_name': self.recording.incident_type.__name__,
                'handler_path': self.handler_path,
                'handler_name': self.handler_name,
                'request_factory_path': request_factory_path,
                'request_factory_name': request_factory_name,
                'generated_test_id': 'example_0',
                'response_attributes': {
                    'status_code',
                    'content'
                },
                'assert_reproduction_as_success': assert_reproduction_as_success
            }

            test_module_str = template.render(**inputs)

            res = format_str(test_module_str, mode=FileMode())
            test_file.write(res)
        sut_response = self.recording.last
        if not self.recording.raises:
            if not isinstance(sut_response, str):
                sut_response = str(sut_response)
            with open(new_data_path, "w") as data_file:
                data_file.write(sut_response)
