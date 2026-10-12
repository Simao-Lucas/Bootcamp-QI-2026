from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import AccountController
from utils.schema_handler import SchemaHandler

DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class AccountResource:

    def on_post_company_account(self, company_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.create_company_account(company_key)

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_post_employee_account(self, employee_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.create_employee_account(employee_key)

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_by_key(self, account_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.get_by_key(account_key)

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate("put_account.json")
    def on_put_by_key(self, account_key: str, payload: dict) -> JSONResponse:
        controller = AccountController()
        account = controller.update_status(account_key, payload["status"])

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_202_ACCEPTED,
        )

    @SchemaHandler.validate("post_test_credit.json")
    def on_post_test_credit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = AccountController()
        account = controller.credit_for_test(account_key, payload["amount"])

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_account_statement.json")
    def on_get_statement(self, account_key: str, request: Request) -> JSONResponse:
        controller = AccountController()

        query_params = request.query_params

        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))

        filters = {
            "date_from": query_params.get("date_from"),
            "date_to": query_params.get("date_to"),
        }

        offset = page * limit
        statement_page = controller.get_statement(account_key, limit, offset, filters)

        page_envelope = {
            "data": statement_page["entries_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": statement_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )
