from typing import Any

from pytest_factory.logger import get_logger
from pytest_factory.outbound_response_double import BaseMockRequest

logger = get_logger(__name__)


class PytestFactoryException(Exception):
    """
    generic exception for exceptions that occur within the framework. please use only if none
    of the other exceptions apply to your error.
    must be raised to halt the test
    NOTE __init__() will ALSO log out the exception description (i.e. self.log_msg) so you don't need to do it as a
    separate action!
    """

    def __init__(self, log_error: bool = True, *args, **kwargs):
        """
        :param log_msg: str message to send to logger;
        :param log_error: bool, if True (default) sends log_msg to logger.error, else logger.warning;
        note this does NOT determine if exception is raised or not! that must be decided by the user
        """

        if log_error:
            self.log_msg = self.get_error_msg(*args, **kwargs)
            logger.error(msg=self.log_msg)
        else:
            self.log_msg = self.get_warning_msg(*args, **kwargs)
            logger.warning(msg=self.log_msg)

    def get_warning_msg(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def get_error_msg(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def __str__(self):
        return self.log_msg


class MissingHandlerException(PytestFactoryException):
    def get_error_msg(self) -> str:
        return 'this test case is missing a mock_request or similar factory! no RequestHandler defined to test!'


class MissingTestDoubleException(PytestFactoryException):
    """
    exception for when Store cannot find the expected test double; this can indicate either a test code error in
    setting up the factories OR an error in component under test not forming the request correctly
    """

    def get_error_msg(self, req_obj: BaseMockRequest) -> str:
        return f"could not find test double match for request signature: {req_obj}!"


class UnCalledTestDoubleException(PytestFactoryException):
    def get_error_msg(self, uncalled_test_doubles: dict) -> str:
        return f"the following test doubles were NOT used in this test: {uncalled_test_doubles}"

    def get_warning_msg(self, uncalled_test_doubles: dict):
        warning_msg = " if this is not expected, set assert_no_missing_calls to True"
        return self.get_error_msg(uncalled_test_doubles=uncalled_test_doubles) + warning_msg


class OverCalledTestDoubleException(PytestFactoryException):
    def get_error_msg(self, mock_responses: list, req_obj: Any) -> str:
        return f'expected only {len(mock_responses)} calls to {req_obj}!'

    def get_warning_msg(self, mock_responses: list, req_obj: Any) -> str:
        warning_msg = f" will repeat last response: {mock_responses[-1][1]}"
        return self.get_error_msg(mock_responses=mock_responses, req_obj=req_obj) + warning_msg
