from typing import Any

from pytest_factory.outbound_response_double import BaseMockRequest


def entrypoint(self, req_obj: BaseMockRequest) -> str:
    # TODO parse req_obj to identify factory
    factory_name = "TBD"
    return factory_name
