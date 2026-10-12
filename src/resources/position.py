from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import PositionController
from utils.schema_handler import SchemaHandler

DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class PositionResource:
    @SchemaHandler.validate("post_position.json")
    def on_post(self, company_key: str, payload: dict) -> JSONResponse:
        controller = PositionController()
        position = controller.create(company_key, payload)

        return JSONResponse(
            content=jsonable_encoder(position),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_positions.json")
    def on_get_list(self, company_key: str, request: Request) -> JSONResponse:
        controller = PositionController()

        query_params = request.query_params

        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))

        offset = page * limit
        positions_page = controller.get_list(company_key, limit, offset)

        page_envelope = {
            "data": positions_page["positions_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": positions_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )
