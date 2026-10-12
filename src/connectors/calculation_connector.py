import requests

from connectors.rest_connector import BaseConnectorResponse, RestConnector
from constants import CALCULATION_API_INTERNAL_TOKEN, CALCULATION_API_TIMEOUT, CALCULATION_API_URL
from errors import CalculationApiUnavailable


class CalculationConnector(RestConnector):

    def __init__(self) -> None:
        super().__init__(
            class_name=__name__,
            base_url=CALCULATION_API_URL,
            timeout=CALCULATION_API_TIMEOUT,
            internal_token=CALCULATION_API_INTERNAL_TOKEN,
        )

    def calculate_salary(self, employee_key: str, reference_month: str, gross_amount: int) -> BaseConnectorResponse:
        payload = {
            "employee_key": employee_key,
            "reference_month": reference_month,
            "gross_amount": gross_amount,
        }

        try:
            return self.send(endpoint="/salary_calculation", method="POST", payload=payload)
        except requests.RequestException as error:
            self.logger.warning(f"A API de cálculo não respondeu: {type(error).__name__}")
            raise CalculationApiUnavailable(f"no response ({type(error).__name__})")
