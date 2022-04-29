import re
from typing import List
from pathlib import Path

from black import format_str, FileMode
from jinja2 import Template

from pytest_factory.http import MockHttpRequest
from pytest_factory.framework.mall import MALL
from pytest_factory.recorder.recording import Recording, reify


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


def get_template(file_path: str):
    p = Path(__file__).parent
    return p.joinpath(file_path)


class Writer:
    def __init__(self, recording: Recording, handler_path: str):
        self.recording = recording
        self.handler_path, self.handler_name = handler_path.rsplit('.', 1)

    def write_test(self, output_path: str):
        """
        writes a test module that reproduces the recorded session
        returns file path
        """

        new_data_path = MALL.get_full_path("actual_response")
        template_path = get_template("template.py.jinja")
        with open(output_path, "x") as test_file:
            with open(template_path) as template_file:
                template = Template(template_file.read())
            request_factory_path, request_factory_name = self.recording.request_factory
            incident_name = self.recording.incident_type.__name__
            inputs = {
                'recording': self.recording,
                'incident_name': incident_name,
                'handler_path': self.handler_path,
                'handler_name': self.handler_name,
                'request_factory_path': request_factory_path,
                'request_factory_name': request_factory_name,
                'generated_test_id': re.sub(r'(?<!^)(?=[A-Z])', '_', incident_name).lower(),
                'response_attributes': {
                    'status',
                    'body'
                },
                'assert_reproduction_as_success': MALL.assert_reproduction_as_success
            }

            test_module_str = template.render(**inputs)

            res = format_str(test_module_str, mode=FileMode())
            test_file.write(res)
        sut_response = self.recording.last
        if not self.recording.raises:
            if not isinstance(sut_response, str):
                sut_response = sut_response.serialize()
            with open(new_data_path, "w") as data_file:
                data_file.write(sut_response)
