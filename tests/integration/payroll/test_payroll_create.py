from os import environ

from tests.utils import (
    MockServerUtils,
    ObjectGenerator,
    PayloadGenerator,
    RequestGenerator,
    calculation_timeout,
)


NOT_FOUND_KEY = "00000000-0000-0000-0000-000000000000"
CALCULATION_TOKEN = environ.get("CALCULATION_API_INTERNAL_TOKEN", "default_token")


def item_of(payroll: dict, employee_key: str) -> dict:
    for item in payroll["items"]:
        if item["employee_key"] == employee_key:
            return item
    raise AssertionError(f"o funcionario {employee_key} nao esta na folha")


def payroll_count(company_key: str) -> int:
    status, response = RequestGenerator.GET_payrolls(company_key)
    assert status == 200
    return len(response["data"])


def header(recorded_request: dict, name: str) -> list:
    for header_name, values in recorded_request["headers"].items():
        if header_name.lower() == name.lower():
            return values
    return []


class TestPayrollCreate:
    def test_refuses_empty_body(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.POST_payroll(company_key, {})
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        payload = PayloadGenerator.create_payroll_payload()
        payload["total_amount"] = 1

        status, response = RequestGenerator.POST_payroll(company_key, payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_month(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        for reference_month in ["2026-13", "2026-00", "2026-9", "202609", "09-2026", "2026-09-01", 202609, None]:
            payload = PayloadGenerator.create_payroll_payload()
            payload["reference_month"] = reference_month

            status, response = RequestGenerator.POST_payroll(company_key, payload)

            assert status == 400, f"aceitou o mes {reference_month!r}"
            assert response["code"] == "QIT000001"

    def test_company_not_found(self):
        status, response = RequestGenerator.POST_payroll(NOT_FOUND_KEY, PayloadGenerator.create_payroll_payload())
        assert status == 404
        assert response["code"] == "QIT001011"

    def test_creates_pending_payroll(self):
        scenario = ObjectGenerator.create_payroll_scenario(
            net_amounts=[400000, 380000], salary_amount=450000, fee_amount=150
        )
        first, second = scenario["employees"]

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 201
        assert "payroll_key" in response
        assert response["reference_month"] == "2026-09"
        assert response["status"] == "pending"
        assert response["total_amount"] == 780000
        assert response["total_fee_amount"] == 300
        assert len(response["items"]) == 2

        first_item = item_of(response, first["employee_key"])
        assert first_item["gross_amount"] == 450000
        assert first_item["net_amount"] == 400000
        assert first_item["fee_amount"] == 150
        assert first_item["status"] == "pending"

        assert item_of(response, second["employee_key"])["net_amount"] == 380000

    def test_creating_moves_no_money(self):
        scenario = ObjectGenerator.create_payroll_scenario()

        ObjectGenerator.create_payroll(scenario["company_key"])

        status, response = RequestGenerator.GET_account(scenario["company_account_key"])
        assert response["balance_amount"] == 780300

        for employee in scenario["employees"]:
            status, response = RequestGenerator.GET_account(employee["account_key"])
            assert response["balance_amount"] == 0

    def test_net_amount_can_exceed_gross(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[500000], salary_amount=450000)

        response = ObjectGenerator.create_payroll(scenario["company_key"])

        assert response["items"][0]["gross_amount"] == 450000
        assert response["items"][0]["net_amount"] == 500000
        assert response["total_amount"] == 500000

    def test_skips_terminated_employees(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000])
        active, terminated = scenario["employees"]
        ObjectGenerator.terminate_employee(terminated["employee_key"])

        response = ObjectGenerator.create_payroll(scenario["company_key"])

        assert [item["employee_key"] for item in response["items"]] == [active["employee_key"]]
        assert response["total_amount"] == 400000
        assert MockServerUtils.calculation_requests(terminated["employee_key"]) == []

    def test_fee_is_frozen_on_items(self):
        scenario = ObjectGenerator.create_payroll_scenario(fee_amount=150)
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"])["payroll_key"]

        status, _response = RequestGenerator.PUT_company(scenario["company_key"], {"fee_amount": 900})
        assert status == 202

        status, response = RequestGenerator.GET_payroll(payroll_key)
        assert response["total_fee_amount"] == 300
        assert {item["fee_amount"] for item in response["items"]} == {150}

    def test_refuses_duplicated_month(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 409
        assert response["code"] == "QIT001031"

        assert payroll_count(scenario["company_key"]) == 1

    def test_accepts_other_months(self):
        scenario = ObjectGenerator.create_payroll_scenario()

        ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")
        ObjectGenerator.create_payroll(scenario["company_key"], "2026-10")

        assert payroll_count(scenario["company_key"]) == 2

    def test_canceled_month_can_be_generated_again(self):
        scenario = ObjectGenerator.create_payroll_scenario()
        payroll_key = ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")["payroll_key"]
        ObjectGenerator.cancel_payroll(payroll_key)

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 201
        assert response["payroll_key"] != payroll_key

    def test_refuses_company_without_active_employees(self):
        company_key = ObjectGenerator.create_company()["company_key"]

        status, response = RequestGenerator.POST_payroll(company_key, PayloadGenerator.create_payroll_payload())
        assert status == 422
        assert response["code"] == "QIT001032"

    def test_refuses_company_with_only_terminated_employees(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        ObjectGenerator.terminate_employee(scenario["employees"][0]["employee_key"])

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload()
        )
        assert status == 422
        assert response["code"] == "QIT001032"

    def test_refuses_active_employee_without_account(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        without_account = ObjectGenerator.create_employee(scenario["company_key"], scenario["position_key"])
        MockServerUtils.expect_net_amount(without_account["employee_key"], 300000)

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload()
        )
        assert status == 422
        assert response["code"] == "QIT001033"

        assert payroll_count(scenario["company_key"]) == 0

    def test_refuses_active_employee_with_blocked_account(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000])
        ObjectGenerator.update_account_status(scenario["employees"][1]["account_key"], "blocked")

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload()
        )
        assert status == 422
        assert response["code"] == "QIT001033"

    def test_validates_before_calling_api(self):
        """Pedido que vai ser recusado nao gasta chamada na API de calculo."""
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        ObjectGenerator.create_employee(scenario["company_key"], scenario["position_key"])

        status, _response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload()
        )
        assert status == 422

        assert MockServerUtils.calculation_requests(scenario["employees"][0]["employee_key"]) == []

    def test_duplicated_month_does_not_call_api(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        employee_key = scenario["employees"][0]["employee_key"]
        ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")

        status, _response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 409

        assert len(MockServerUtils.calculation_requests(employee_key)) == 1


class TestPayrollCreateCalculationApi:
    
    def test_sends_the_contract(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000], salary_amount=450000)
        employee_key = scenario["employees"][0]["employee_key"]

        ObjectGenerator.create_payroll(scenario["company_key"], "2026-09")

        recorded = MockServerUtils.calculation_requests(employee_key)
        assert len(recorded) == 1
        assert recorded[0]["body"]["json"] == {
            "employee_key": employee_key,
            "reference_month": "2026-09",
            "gross_amount": 450000,
        }
        assert header(recorded[0], "INTERNAL-TOKEN") == [CALCULATION_TOKEN]

    def test_calls_once_per_active_employee(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000, 360000])

        ObjectGenerator.create_payroll(scenario["company_key"])

        for employee in scenario["employees"]:
            assert len(MockServerUtils.calculation_requests(employee["employee_key"])) == 1

    def test_api_error_status(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        employee_key = scenario["employees"][0]["employee_key"]

        for error_status in [500, 503, 400, 422]:
            MockServerUtils.expect_calculation(employee_key, status_code=error_status, body={"error": "x"})

            status, response = RequestGenerator.POST_payroll(
                scenario["company_key"], PayloadGenerator.create_payroll_payload()
            )

            assert status == 502, f"aceitou a API respondendo {error_status}"
            assert response["code"] == "QIT001034"

        assert payroll_count(scenario["company_key"]) == 0

    def test_api_without_answer_for_the_employee(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        MockServerUtils.clear_calculation(scenario["employees"][0]["employee_key"])

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload()
        )
        assert status == 502
        assert response["code"] == "QIT001034"

    def test_api_timeout(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        employee_key = scenario["employees"][0]["employee_key"]
        MockServerUtils.expect_calculation(
            employee_key, body={"net_amount": 400000}, delay_seconds=calculation_timeout() + 2
        )

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 502
        assert response["code"] == "QIT001034"
        assert payroll_count(scenario["company_key"]) == 0

        MockServerUtils.expect_net_amount(employee_key, 400000)

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 201
        assert response["total_amount"] == 400000

    def test_api_invalid_net_amount(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        employee_key = scenario["employees"][0]["employee_key"]

        for net_amount in [0, -100, 4000.5, "400000", None, True]:
            MockServerUtils.expect_calculation(employee_key, body={"net_amount": net_amount})

            status, response = RequestGenerator.POST_payroll(
                scenario["company_key"], PayloadGenerator.create_payroll_payload()
            )

            assert status == 502, f"aceitou o liquido {net_amount!r}"
            assert response["code"] == "QIT001035"

        assert payroll_count(scenario["company_key"]) == 0

    def test_api_body_without_net_amount(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        employee_key = scenario["employees"][0]["employee_key"]

        for body in [{}, {"amount": 400000}, []]:
            MockServerUtils.expect_calculation(employee_key, body=body)

            status, response = RequestGenerator.POST_payroll(
                scenario["company_key"], PayloadGenerator.create_payroll_payload()
            )

            assert status == 502, f"aceitou o corpo {body!r}"
            assert response["code"] == "QIT001035"

    def test_api_body_is_not_json(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000])
        MockServerUtils.expect_calculation(scenario["employees"][0]["employee_key"], body="net_amount=400000")

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload()
        )
        assert status == 502
        assert response["code"] == "QIT001035"

    def test_one_failure_saves_nothing(self):
        scenario = ObjectGenerator.create_payroll_scenario(net_amounts=[400000, 380000, 360000])
        failing = scenario["employees"][1]
        MockServerUtils.expect_calculation(failing["employee_key"], status_code=500)

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 502
        assert response["code"] == "QIT001034"
        assert payroll_count(scenario["company_key"]) == 0

        MockServerUtils.expect_net_amount(failing["employee_key"], 380000)

        status, response = RequestGenerator.POST_payroll(
            scenario["company_key"], PayloadGenerator.create_payroll_payload("2026-09")
        )
        assert status == 201
        assert response["total_amount"] == 1140000
        assert payroll_count(scenario["company_key"]) == 1