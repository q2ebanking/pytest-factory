from importlib import import_module
from typing import Tuple, List, Dict

from jinja2 import Template
from requests import Response

from pytest_factory.http import MOCK_HTTP_RESPONSE, MockHttpRequest
from pytest_factory.recorder.recording import Recording

Exchange = Tuple[MockHttpRequest, MOCK_HTTP_RESPONSE]

# TODO find a home for this
assert_reproduction_as_success = True


def lex(log_line: str) -> Tuple[str, str, Dict]:
    input_dict = {}
    return 'some.import.path', 'class_name', input_dict


def parse(logs: List[str]) -> Recording:
    if len(logs) < 2:
        raise Exception  # TODO
    exchange_objects = []
    requests = []
    responses = []
    for log_line in logs:
        import_path, import_name, input_dict = lex(log_line=log_line)
        new_module = import_module(import_path)
        new_cls = getattr(new_module, import_name)
        new_obj = new_cls(**input_dict)
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
    doc_exchanges = exchange_objects[1:] if len(exchange_objects > 1) else []
    recording = Recording(sut_exchange=exchange_objects[0], doc_exchanges=doc_exchanges)
    return recording


EXCEPTION_PATH_LOOKUP = {
    'JSONDecodeError': 'json'
}


class Writer:
    def __init__(self, recording: Recording, handler_path: str):
        self.recording = recording
        self.handler_path, self.handler_name = handler_path.rsplit('.', 1)
        if self.recording.raises:
            import_path = EXCEPTION_PATH_LOOKUP.get(self.recording.last.__name__)
            setattr(self.recording.last, 'IMPORT_PATH', import_path)

    def write_test(self, output_path: str = 'tests/test_file.py'):
        """
        writes a test module that reproduces the recorded session
        returns file path
        """
        new_data_path = f"tests/actual_response"
        template_path = f"pytest_factory/template.py.jinja"
        with open(output_path, "w") as test_file:
            with open(template_path) as template_file:
                template = Template(template_file.read())

            inputs = {
                'recording': self.recording,
                'incident_name': self.recording.incident_type.__name__,
                'handler_path': self.handler_path,
                'handler_name': self.handler_name,
                'generated_test_id': 'example_0',
                'assert_reproduction_as_success': assert_reproduction_as_success
            }

            test_module_str = template.render(**inputs)
            test_file.write(test_module_str)
        sut_response = self.recording.last
        if not self.recording.raises:
            if isinstance(sut_response, Response) and sut_response.content:
                sut_response = sut_response.content.decode()
            if not isinstance(sut_response, str):
                sut_response = str(sut_response)
            with open(new_data_path, "w") as data_file:
                data_file.write(sut_response)
