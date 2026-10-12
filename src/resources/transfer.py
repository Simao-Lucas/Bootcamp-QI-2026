from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import TransferController
from utils.schema_handler import SchemaHandler


class TransferResource:
    @SchemaHandler.validate("post_transfer.json")
    def on_post(self, payload: dict) -> JSONResponse:
        controller = TransferController()
        result = controller.create(payload)

        return self._creation_response(result)

    @SchemaHandler.validate("post_external_transfer.json")
    def on_post_external(self, payload: dict) -> JSONResponse:
        controller = TransferController()
        result = controller.create_external(payload)

        return self._creation_response(result)

    def on_get_by_key(self, transfer_key: str) -> JSONResponse:
        controller = TransferController()
        transfer = controller.get_by_key(transfer_key)

        return JSONResponse(
            content=jsonable_encoder(transfer),
            status_code=http_status.HTTP_200_OK,
        )

    def _creation_response(self, result: dict) -> JSONResponse:
        status_code = http_status.HTTP_201_CREATED
        if not result["is_new"]:
            status_code = http_status.HTTP_200_OK

        return JSONResponse(
            content=jsonable_encoder(result["transfer_dto"]),
            status_code=status_code,
        )
