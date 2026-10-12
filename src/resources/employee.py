from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import EmployeeController
from utils.schema_handler import SchemaHandler

DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class EmployeeResource:

    @SchemaHandler.validate("post_employee.json")
    def on_post(self, company_key: str, payload: dict) -> JSONResponse:
        controller = EmployeeController()
        employee = controller.create(company_key, payload)

        return JSONResponse(
            content=jsonable_encoder(employee),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_by_key(self, employee_key: str) -> JSONResponse:
        controller = EmployeeController()
        employee = controller.get_by_key(employee_key)

        return JSONResponse(
            content=jsonable_encoder(employee),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate("put_employee.json")
    def on_put_by_key(self, employee_key: str, payload: dict) -> JSONResponse:
        controller = EmployeeController()
        employee = controller.update(employee_key, payload)

        return JSONResponse(
            content=jsonable_encoder(employee),
            status_code=http_status.HTTP_202_ACCEPTED,
        )

    @SchemaHandler.validate_query_params("get_employees.json")
    def on_get_list(self, company_key: str, request: Request) -> JSONResponse:
        controller = EmployeeController()

        query_params = request.query_params

        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))

        # O schema garantiu que `active`, se veio, e "true" ou "false".
        # Vira booleano aqui porque e vocabulario da query string; quem
        # nao mandou fica com None, e a lista traz ativos e desligados.
        active = None
        if "active" in query_params:
            active = query_params["active"] == "true"

        filters = {
            "name": query_params.get("name"),
            "active": active,
        }

        offset = page * limit
        employees_page = controller.get_list(company_key, limit, offset, filters)

        page_envelope = {
            "data": employees_page["employees_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": employees_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )
