from tests.utils import ObjectGenerator, RequestGenerator


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"


def extract_months(response: dict) -> list:
    months = []
    for payroll in response["data"]:
        months.append(payroll["reference_month"])
    return months


class TestPayrolls:

    def test_empty_list(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.GET_payrolls(company_key)
        assert status == 200
        assert response["data"] == []
        assert response["is_last_page"] is True

    def test_lists_newest_first(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        for month in ["2026-07", "2026-08", "2026-09"]:
            ObjectGenerator.create_payroll(scenario["company_key"], month)

        status, response = RequestGenerator.GET_payrolls(scenario["company_key"])
        assert status == 200
        assert extract_months(response) == ["2026-09", "2026-08", "2026-07"]

    def test_get_pages(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        for month in ["2026-07", "2026-08", "2026-09"]:
            ObjectGenerator.create_payroll(scenario["company_key"], month)

        status, response = RequestGenerator.GET_payrolls(scenario["company_key"], {"limit": 2})
        assert status == 200
        assert extract_months(response) == ["2026-09", "2026-08"]
        assert response["is_last_page"] is False

        status, response = RequestGenerator.GET_payrolls(scenario["company_key"], {"limit": 2, "page": 1})
        assert status == 200
        assert extract_months(response) == ["2026-07"]
        assert response["is_last_page"] is True

    def test_filters_by_status(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        canceled_key = ObjectGenerator.create_payroll(scenario["company_key"], "2026-07")["payroll_key"]
        ObjectGenerator.cancel_payroll(canceled_key)
        ObjectGenerator.create_payroll(scenario["company_key"], "2026-08")

        status, response = RequestGenerator.GET_payrolls(scenario["company_key"], {"status": "canceled"})
        assert status == 200
        assert extract_months(response) == ["2026-07"]

        status, response = RequestGenerator.GET_payrolls(scenario["company_key"], {"status": "pending"})
        assert status == 200
        assert extract_months(response) == ["2026-08"]

        status, response = RequestGenerator.GET_payrolls(scenario["company_key"], {"status": "paid"})
        assert status == 200
        assert response["data"] == []

    def test_filters_processing(self):
        payroll = ObjectGenerator.create_processing_payroll()

        status, response = RequestGenerator.GET_payrolls(payroll["company_key"], {"status": "processing"})
        assert status == 200
        assert [item["payroll_key"] for item in response["data"]] == [payroll["payroll_key"]]

    def test_lists_only_payrolls_of_the_company(self):
        first = ObjectGenerator.create_payroll_scenario()
        second = ObjectGenerator.create_payroll_scenario()
        ObjectGenerator.create_payroll(first["company_key"], "2026-09")
        ObjectGenerator.create_payroll(second["company_key"], "2026-10")

        status, response = RequestGenerator.GET_payrolls(first["company_key"])
        assert status == 200
        assert extract_months(response) == ["2026-09"]

    def test_wrong_params(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for params in [{"status": "frozen"}, {"status": "PAID"}, {"page": -3}, {"limit": 101}]:
            status, response = RequestGenerator.GET_payrolls(company_key, params)

            assert status == 400, f"aceitou os parametros {params}"
            assert response["code"] == "QIT000001"

    def test_refuses_unknown_query_param(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.GET_payrolls(company_key, {"mes": "2026-09"})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_company_not_found(self):
        status, response = RequestGenerator.GET_payrolls(NOT_FOUND_KEY)
        assert status == 404
        assert response["code"] == "QIT001011"
