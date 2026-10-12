from uuid import uuid4

from tests.utils import DbUtils, PayloadGenerator, RequestGenerator


def extract_keys(response: dict) -> list:
    company_keys = []
    for company in response["data"]:
        company_keys.append(company["company_key"])
    return company_keys


class TestCompanies:
    def test_empty_list(self):
        DbUtils.rollback()

        status, response = RequestGenerator.GET_companies()
        assert status == 200
        assert response["data"] == []
        assert response["is_last_page"] is True

    def test_get_pages(self):
        DbUtils.rollback()

        for _empresa in range(3):
            payload = PayloadGenerator.create_company_payload()
            status, response = RequestGenerator.POST_company(payload)
            assert status == 201

        status, response = RequestGenerator.GET_companies()
        assert status == 200
        assert len(response["data"]) == 3
        assert response["is_last_page"] is True

        status, response = RequestGenerator.GET_companies({"limit": 2})
        assert status == 200
        assert len(response["data"]) == 2
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_companies({"limit": 2, "page": 1})
        assert status == 200
        assert len(response["data"]) == 1
        assert response["is_last_page"] is True

    def test_list_item_has_the_same_fields_as_get(self):
        unique_name = f"Empresa {uuid4().hex}"

        payload = PayloadGenerator.create_company_payload(name=unique_name)
        status, response = RequestGenerator.POST_company(payload)
        assert status == 201
        created_key = response["company_key"]

        status, single = RequestGenerator.GET_company(created_key)
        assert status == 200

        status, response = RequestGenerator.GET_companies({"name": unique_name})
        assert status == 200
        assert response["data"] == [single]

    def test_wrong_params(self):
        for params in [{"page": -3}, {"limit": 500}, {"limit": 101}, {"name": ""}]:
            status, response = RequestGenerator.GET_companies(params)

            assert status == 400, f"aceitou os parametros {params}"
            assert response["code"] == "QIT000001"

    def test_accepts_limit_of_one_hundred(self):
        status, _response = RequestGenerator.GET_companies({"limit": 100})
        assert status == 200

    def test_refuses_unknown_query_param(self):
        status, response = RequestGenerator.GET_companies({"nmae": "Padaria"})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_filters_by_partial_name_ignoring_case(self):
        unique_part = f"Ferragens{uuid4().hex[:8]}"

        payload = PayloadGenerator.create_company_payload(name=f"Casa {unique_part} LTDA")
        status, response = RequestGenerator.POST_company(payload)
        assert status == 201
        matching_key = response["company_key"]

        payload = PayloadGenerator.create_company_payload(name="Mercado Central LTDA")
        status, response = RequestGenerator.POST_company(payload)
        assert status == 201

        status, response = RequestGenerator.GET_companies({"name": unique_part.upper()})
        assert status == 200
        assert extract_keys(response) == [matching_key]

    def test_filter_without_match_returns_empty_page(self):
        status, response = RequestGenerator.GET_companies({"name": f"Inexistente{uuid4().hex}"})
        assert status == 200
        assert response["data"] == []
        assert response["is_last_page"] is True

    def test_lists_newest_first_and_pages_do_not_overlap(self):
        batch_name = f"Lote{uuid4().hex[:8]}"

        created_keys = []
        for _empresa in range(3):
            payload = PayloadGenerator.create_company_payload(name=batch_name)
            status, response = RequestGenerator.POST_company(payload)
            assert status == 201
            created_keys.append(response["company_key"])

        created_keys.reverse()

        status, response = RequestGenerator.GET_companies({"name": batch_name, "limit": 2})
        assert status == 200
        assert extract_keys(response) == created_keys[:2]
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_companies(
            {"name": batch_name, "limit": 2, "page": 1}
        )
        assert status == 200
        assert extract_keys(response) == created_keys[2:]
        assert response["is_last_page"] is True
