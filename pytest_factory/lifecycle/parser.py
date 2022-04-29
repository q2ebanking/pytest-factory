from typing import List

from pytest_factory.lifecycle.recording import reify, BaseMockRequest, Recording, RecorderException


def parse(logs: List[str]) -> Recording:
    if len(logs) < 2:
        raise RecorderException(log_msg='insufficient logs to parse a full recording!')
    exchange_objects = []
    requests = []
    responses = []
    for log_line in logs:
        new_obj = reify(path=log_line)
        if isinstance(new_obj, BaseMockRequest):
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
