from typing import List, Optional

from pytest_factory.logger import get_logger
from pytest_factory.outbound_response_double import BaseMockRequest

logger = get_logger(__name__)


class PytestFactoryException(Exception):
    """
    generic exception for exceptions that occur within the framework. please use only if none
    of the other exceptions apply to your error
    """

    def __init__(self, log_msgs: List[str]):
        """
        :param log_msgs: str or list of strings for messages to send to logger;
        """

        if isinstance(log_msgs, str):
            log_msgs = [log_msgs]
        self.log_msgs = log_msgs
        for log_msg in log_msgs:
            if isinstance(log_msg, str):
                logger.error(msg=log_msg)

    def __str__(self):
        return str(self.log_msgs)


class MissingHandlerException(PytestFactoryException):
    def __init__(self):
        log_msg = 'this test case is missing a mock_request or similar factory! no RequestHandler defined to test!'
        super().__init__(log_msgs=[log_msg])


class MissingTestDoubleException(PytestFactoryException):
    """
    exception for when Store cannot find the expected test double; this can indicate either a test code error in
    setting up the factories OR an error in component under test not forming the request correctly
    """

    def __init__(self, req_obj: BaseMockRequest, desc: Optional[str] = None):
        log_msg = f"could not find test double match for request signature: {req_obj}!"
        super().__init__(log_msgs=[log_msg, desc])


class UnCalledTestDoubleException(PytestFactoryException):
    def __init__(self, uncalled_test_doubles: dict, desc: Optional[str] = None):
        log_msg = f"the following test doubles were NOT used in this test! if that is not a test failure condition, " \
                  f"you must set FAIL_UNCALLED_TEST_DOUBLES to False (the default setting): {uncalled_test_doubles}"
        super().__init__(log_msgs=[log_msg, desc])
