from importlib import import_module
from typing import Tuple, List, Optional, Set
from json import JSONDecodeError

from jinja2 import Template

from pytest_factory.http import MOCK_HTTP_RESPONSE
from pytest_factory.inbound_request_double import MockHttpRequest

Exchange = Tuple[MockHttpRequest, MOCK_HTTP_RESPONSE]

class Recording:
    def __init__(self, sut_exchange: Exchange, doc_exchanges: Optional[List[Exchange]] = []) -> None:
        self.sut_exchange = sut_exchange
        self.doc_exchanges = doc_exchanges
        self.factory_paths: List[str] = []
    
    @property
    def raises(self) -> bool:
        return isinstance(self.last, Exception)

    @property    
    def first(self) -> MockHttpRequest:
        return self.sut_exchange[0]
    
    @property
    def last(self) -> MOCK_HTTP_RESPONSE:
        return self.sut_exchange[1]
    
    def get_factories(self) -> Set[str]:
        factories = set()
        for request, _ in self.doc_exchanges:
            factories.add(request.FACTORY_NAME)
        return factories

def lex(log_line: str) -> str:
    input_dict = {}
    return 'some.import.path', input_dict


def parse(logs: List[str]) -> Recording:
    if len(logs) < 2:
        raise Exception  # TODO
    exchange_objects = []
    requests = []
    responses = []
    for log_line in logs:
        import_path, input_dict = lex(log_line=log_line)
        new_cls = import_module(import_path)
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

class Writer:
    def __init__(self, recording: Recording, handler_path: str):
        self.recording = recording
        self.handler_path = handler_path

    def write_test(self) -> str:
        """
        writes a test module that reproduces the recorded session
        returns file path
        """

        new_test_path = f"test_file.py"
        new_data_path = f"actual_response"
        template_path = f"template.jinja"
        with open(new_test_path, "w") as test_file:
            with open(template_path) as template_file:
                template = Template(template_file.read())
            test_module_str = template.render(inputs=self.recording)
            test_file.write(test_module_str)
        if not self.recording.raises:
            with open(new_data_path, "w") as data_file:
                sut_response = self.recording.last
                data_file.write(sut_response)

def test_writer():
    hp = 'tests.passthru_app.PassthruTestHandler'
    request = MockHttpRequest()
    response = JSONDecodeError
    se: Exchange = (request, response)
    de: List[Exchange] = [
        ()
    ]
    r = Recording(sut_exchange=se)
    w = Writer(recording=r, handler_path=hp)
    test_module_str = w.write_test()
    print(test_module_str)

test_writer()