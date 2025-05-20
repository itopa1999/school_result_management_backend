from drf_standardized_errors.formatter import (
    ExceptionFormatter as BaseExceptionFormatter,
)
from drf_standardized_errors.types import ErrorResponse


class ExceptionFormatter(BaseExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        error = error_response.errors[0]

        return {"error": error.detail, "field": error.attr}
