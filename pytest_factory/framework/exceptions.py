from typing import List, Optional

from pytest_factory.framework.logger import LOGGER
from pytest_factory.mock_request_types import BaseMockRequest


class PytestFactoryException(Exception):
    """
    generic exception for exceptions that occur within the framework. please use only if none
    of the other exceptions apply to your error
    """

    def __init__(self, log_msgs: List[str]):
        """
        :param log_msgs: str or list of strings for messages to send to LOGGER;
        """

        if isinstance(log_msgs, str):
            log_msgs = [log_msgs]
        self.log_msgs = log_msgs
        for log_msg in log_msgs:
            if isinstance(log_msgs, str):
                LOGGER.error(msg=log_msg)


class FixtureNotFoundException(PytestFactoryException):
    """
    exception for when Store cannot find the expected fixture; this can indicate either a test code error in
    setting up the fixtures OR an error in component under test not forming the request correctly
    """

    def __init__(self, req_obj: BaseMockRequest, desc: Optional[str] = None):
        log_msg = f"could not find fixture match for request signature: {req_obj}!"
        super().__init__(log_msgs=[log_msg, desc])


class FixtureNotCalledException(PytestFactoryException):
    def __init__(self, uncalled_fixtures: dict, desc: Optional[str] = None):
        log_msg = f"the following fixtures were NOT used in this test! if that is not a test failure condition, " \
                  f"you must set FAIL_UNCALLED_FIXTURES to False (the default setting): {uncalled_fixtures}"
        super().__init__(log_msgs=[log_msg, desc])
