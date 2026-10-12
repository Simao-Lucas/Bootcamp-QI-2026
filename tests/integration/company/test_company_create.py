from tests.utils import PayloadGenerator, RandomGenerator, RequestGenerator


class TestCompanyCreate:
    def test_refuses_empty_body(self):
        payload = {}
        status, response = RequestGenerator.POST_company(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_refuses_missing_field(self):
        for campo in ["name", "document_number", "email", "payment_day", "fee_amount"]:
            payload = PayloadGenerator.create_company_payload()
            del payload[campo]

            status, response = RequestGenerator.POST_company(payload)

            assert status == 400, f"aceitou a empresa sem o campo '{campo}'"
            assert response["code"] == "QIT000001"

    def test_schema_refuses_unknown_field(self):
        payload = PayloadGenerator.create_company_payload()
        payload["campo_que_nao_existe"] = 1

        status, response = RequestGenerator.POST_company(payload)
        assert status == 400
        assert response["code"] == "QIT000001"

    def test_schema_refuses_malformed_fields(self):
        campos_tortos = [
            ("name", ""),
            ("email", "isto-nao-e-um-email"),
            ("document_number", "11222333000181"),
            ("document_number", "529.982.247-25"),
            ("payment_day", "5"),
            ("payment_day", 5.5),
        ]

        for campo, valor_torto in campos_tortos:
            payload = PayloadGenerator.create_company_payload()
            payload[campo] = valor_torto

            status, response = RequestGenerator.POST_company(payload)

            assert status == 400, f"o campo '{campo}' aceitou o valor {valor_torto!r}"
            assert response["code"] == "QIT000001"

    def test_refuses_payment_day_out_of_range(self):
        for payment_day in [0, 29, 31, -1]:
            payload = PayloadGenerator.create_company_payload(payment_day=payment_day)

            status, response = RequestGenerator.POST_company(payload)

            assert status == 400, f"aceitou o dia de pagamento {payment_day}"
            assert response["code"] == "QIT000001"

    def test_accepts_payment_day_limits(self):
        for payment_day in [1, 28]:
            payload = PayloadGenerator.create_company_payload(payment_day=payment_day)

            status, _response = RequestGenerator.POST_company(payload)

            assert status == 201, f"recusou o dia de pagamento {payment_day}"

    def test_refuses_malformed_fee_amount(self):
        for fee_amount in ["150", 1.5, None, 0, -1]:
            payload = PayloadGenerator.create_company_payload()
            payload["fee_amount"] = fee_amount

            status, response = RequestGenerator.POST_company(payload)

            assert status == 400, f"aceitou a taxa {fee_amount!r}"
            assert response["code"] == "QIT000001"

    def test_accepts_minimum_fee_amount(self):
        payload = PayloadGenerator.create_company_payload(fee_amount=1)

        status, _response = RequestGenerator.POST_company(payload)
        assert status == 201

    def test_creates_company(self):
        payload = PayloadGenerator.create_company_payload()

        status, response = RequestGenerator.POST_company(payload)
        assert status == 201

        _key = response["company_key"]

        status, response = RequestGenerator.GET_company(_key)
        assert status == 200
        assert response["company_key"] == _key
        assert response["name"] == payload["name"]
        assert response["document_number"] == payload["document_number"]
        assert response["email"] == payload["email"]
        assert response["payment_day"] == payload["payment_day"]
        assert response["fee_amount"] == payload["fee_amount"]

    def test_each_company_has_its_own_fee(self):
        status, primeira = RequestGenerator.POST_company(PayloadGenerator.create_company_payload(fee_amount=100))
        assert status == 201

        status, segunda = RequestGenerator.POST_company(PayloadGenerator.create_company_payload(fee_amount=250))
        assert status == 201

        status, response = RequestGenerator.GET_company(primeira["company_key"])
        assert response["fee_amount"] == 100

        status, response = RequestGenerator.GET_company(segunda["company_key"])
        assert response["fee_amount"] == 250

    def test_each_company_gets_its_own_key(self):
        status, primeira = RequestGenerator.POST_company(PayloadGenerator.create_company_payload())
        assert status == 201

        status, segunda = RequestGenerator.POST_company(PayloadGenerator.create_company_payload())
        assert status == 201

        assert primeira["company_key"] != segunda["company_key"]

    def test_refuses_invalid_document_number(self):
        payload = PayloadGenerator.create_company_payload(document_number="11.222.333/0001-82")

        status, response = RequestGenerator.POST_company(payload)

        assert status == 422
        assert response["code"] == "QIT001008"

    def test_refuses_document_number_with_all_digits_equal(self):
        payload = PayloadGenerator.create_company_payload(document_number="00.000.000/0000-00")

        status, response = RequestGenerator.POST_company(payload)

        assert status == 422
        assert response["code"] == "QIT001008"

    def test_refuses_duplicated_document_number(self):
        primeira = PayloadGenerator.create_company_payload()
        status, _response = RequestGenerator.POST_company(primeira)
        assert status == 201

        segunda = PayloadGenerator.create_company_payload(document_number=primeira["document_number"])

        status, response = RequestGenerator.POST_company(segunda)

        assert status == 409
        assert response["code"] == "QIT001009"

    def test_refuses_duplicated_email(self):
        primeira = PayloadGenerator.create_company_payload()
        status, _response = RequestGenerator.POST_company(primeira)
        assert status == 201

        segunda = PayloadGenerator.create_company_payload(email=primeira["email"])

        status, response = RequestGenerator.POST_company(segunda)

        assert status == 409
        assert response["code"] == "QIT001010"

    def test_valid_document_numbers_are_accepted(self):
        for _ in range(10):
            document_number = RandomGenerator.generate_cnpj()
            payload = PayloadGenerator.create_company_payload(document_number=document_number)

            status, response = RequestGenerator.POST_company(payload)

            assert status == 201, f"recusou o CNPJ valido {document_number}: {response}"
