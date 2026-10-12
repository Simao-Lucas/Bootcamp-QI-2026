from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import PayrollController
from utils.schema_handler import SchemaHandler

DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class PayrollResource:
    @SchemaHandler.validate("post_payroll.json")
    def on_post(self, company_key: str, payload: dict) -> JSONResponse:
        controller = PayrollController()
        payroll = controller.create(company_key, payload)

        return JSONResponse(
            content=jsonable_encoder(payroll),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_by_key(self, payroll_key: str) -> JSONResponse:
        controller = PayrollController()
        payroll = controller.get_by_key(payroll_key)

        return JSONResponse(
            content=jsonable_encoder(payroll),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate_query_params("get_payrolls.json")
    def on_get_list(self, company_key: str, request: Request) -> JSONResponse:
        controller = PayrollController()

        query_params = request.query_params

        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))

        filters = {
            "status": query_params.get("status"),
        }

        offset = page * limit
        payrolls_page = controller.get_list(company_key, limit, offset, filters)

        page_envelope = {
            "data": payrolls_page["payrolls_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": payrolls_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )

    def on_put_pay(self, payroll_key: str) -> JSONResponse:
        controller = PayrollController()

        return self._accepted(controller.pay(payroll_key))

    def on_put_retry(self, payroll_key: str) -> JSONResponse:
        controller = PayrollController()

        return self._accepted(controller.retry(payroll_key))

    def on_put_refund(self, payroll_key: str) -> JSONResponse:
        controller = PayrollController()

        return self._accepted(controller.refund(payroll_key))

    def on_put_cancel(self, payroll_key: str) -> JSONResponse:
        controller = PayrollController()

        return self._accepted(controller.cancel(payroll_key))

    def on_post_test_process(self, payroll_key: str) -> JSONResponse:
        controller = PayrollController()
        result = controller.process(payroll_key)

        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=http_status.HTTP_200_OK,
        )

    def _accepted(self, result: dict) -> JSONResponse:
        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=http_status.HTTP_202_ACCEPTED,
        )
