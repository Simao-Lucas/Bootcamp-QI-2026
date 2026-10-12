from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


NOT_FOUND_COMPANY_KEY = "00000000-0000-0000-0000-000000000000"
POSITION_FIELDS = {"position_key", "name", "salary_amount"}


def extract_keys(response: dict) -> list:
    position_keys = []
    for position in response["data"]:
        position_keys.append(position["position_key"])
    return position_keys


class TestPositions:
    def test_empty_list(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.GET_positions(company_key)
        assert status == 200
        assert response["data"] == []
        assert response["is_last_page"] is True

    def test_list_item_fields(self):
        company_key = ObjectGenerator.create_company()["company_key"]
        payload = PayloadGenerator.create_position_payload(name="Confeiteiro", salary_amount=320050)

        status, response = RequestGenerator.POST_position(company_key, payload)
        assert status == 201
        created_key = response["position_key"]

        status, response = RequestGenerator.GET_positions(company_key)
        assert status == 200
        assert response["data"] == [
            {"position_key": created_key, "name": "Confeiteiro", "salary_amount": 320050}
        ]
        assert set(response["data"][0].keys()) == POSITION_FIELDS

    def test_lists_only_positions_of_the_company(self):
        primeira_empresa = ObjectGenerator.create_company()["company_key"]
        segunda_empresa = ObjectGenerator.create_company()["company_key"]

        cargo_da_primeira = ObjectGenerator.create_position(primeira_empresa, name="Caixa")
        cargo_da_segunda = ObjectGenerator.create_position(segunda_empresa, name="Caixa")

        status, response = RequestGenerator.GET_positions(primeira_empresa)
        assert status == 200
        assert extract_keys(response) == [cargo_da_primeira["position_key"]]

        status, response = RequestGenerator.GET_positions(segunda_empresa)
        assert status == 200
        assert extract_keys(response) == [cargo_da_segunda["position_key"]]

    def test_get_pages(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for nome in ["Caixa", "Padeiro", "Gerente"]:
            ObjectGenerator.create_position(company_key, name=nome)

        status, response = RequestGenerator.GET_positions(company_key)
        assert status == 200
        assert len(response["data"]) == 3
        assert response["is_last_page"] is True

        status, response = RequestGenerator.GET_positions(company_key, {"limit": 2})
        assert status == 200
        assert len(response["data"]) == 2
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_positions(company_key, {"limit": 2, "page": 1})
        assert status == 200
        assert len(response["data"]) == 1
        assert response["is_last_page"] is True

    def test_lists_newest_first_and_pages_do_not_overlap(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        created_keys = []
        for nome in ["Caixa", "Padeiro", "Gerente"]:
            created_keys.append(ObjectGenerator.create_position(company_key, name=nome)["position_key"])

        created_keys.reverse()

        status, response = RequestGenerator.GET_positions(company_key, {"limit": 2})
        assert status == 200
        assert extract_keys(response) == created_keys[:2]
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_positions(company_key, {"limit": 2, "page": 1})
        assert status == 200
        assert extract_keys(response) == created_keys[2:]
        assert response["is_last_page"] is True

    def test_company_not_found(self):
        status, response = RequestGenerator.GET_positions(NOT_FOUND_COMPANY_KEY)
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_wrong_params(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for params in [{"page": -3}, {"limit": 500}, {"limit": 101}]:
            status, response = RequestGenerator.GET_positions(company_key, params)

            assert status == 400, f"aceitou os parametros {params}"
            assert response["code"] == "QIT000001"

    def test_refuses_unknown_query_param(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.GET_positions(company_key, {"nome": "Caixa"})
        assert status == 400
        assert response["code"] == "QIT000001"
