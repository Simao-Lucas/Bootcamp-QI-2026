from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import CompanyController
from utils.schema_handler import SchemaHandler

DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class CompanyResource:

    @SchemaHandler.validate("post_company.json")
    def on_post(self, payload: dict) -> JSONResponse:
        # Se o código chegou até aqui, o payload JÁ foi conferido contra
        # o src/schemas/post_company.json. O resource não checa nada:
        # ele só chama a regra de negócio.
        controller = CompanyController()
        company = controller.create(payload)

        return JSONResponse(
            content=jsonable_encoder(company),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_by_key(self, company_key: str) -> JSONResponse:
        controller = CompanyController()
        company = controller.get_by_key(company_key)

        return JSONResponse(
            content=jsonable_encoder(company),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate("put_company.json")
    def on_put_by_key(self, company_key: str, payload: dict) -> JSONResponse:
        controller = CompanyController()
        company = controller.update_fee_amount(company_key, payload["fee_amount"])

        return JSONResponse(
            content=jsonable_encoder(company),
            status_code=http_status.HTTP_202_ACCEPTED,
        )

    @SchemaHandler.validate_query_params("get_companies.json")
    def on_get_list(self, request: Request) -> JSONResponse:
        """A pagina pedida, com os filtros que vierem na query string.

        O decorator ja conferiu tudo contra o src/schemas/get_companies.json
        antes desta primeira linha rodar — mesmo mecanismo que confere o
        corpo do POST, mesmo tipo de arquivo. Por isso os `int()` abaixo
        nao tem try: o schema garantiu que so chega digito.
        """
        controller = CompanyController()

        query_params = request.query_params

        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))

        # Os filtros viajam juntos num dicionario em vez de argumentos
        # soltos: cada filtro novo passa a custar uma linha aqui, e
        # nenhuma assinatura nova nas camadas de baixo.
        filters = {
            "name": query_params.get("name"),
        }

        offset = page * limit
        companies_page = controller.get_list(limit, offset, filters)

        # A paginação é assunto do endereço (?limit=&page=), não da
        # empresa: por isso quem monta o envelope da página é o
        # resource, e não o DTO.
        #
        # É a exceção ao "um método daqui cabe em três linhas", e é
        # deliberada: o envelope fala de limit e page, que são
        # vocabulário de HTTP. Empurrá-lo pro controller obrigaria a
        # regra de negócio a saber o que é uma página.
        page_envelope = {
            "data": companies_page["companies_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": companies_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )
