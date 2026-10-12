CREATE TABLE company(
    id                              SERIAL PRIMARY KEY,
    company_key                     CHAR(36) NOT NULL,
    name                            VARCHAR(255) NOT NULL,
    document_number                 CHAR(18) NOT NULL,
    email                           VARCHAR(255) NOT NULL,
    payment_day                     SMALLINT NOT NULL CHECK (payment_day BETWEEN 1 AND 28),
    fee_amount                      BIGINT NOT NULL CHECK (fee_amount > 0),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(company_key),
    UNIQUE(document_number),
    UNIQUE(email)
);

CREATE TABLE position(
    id                              SERIAL PRIMARY KEY,
    position_key                    CHAR(36) NOT NULL,
    company_id                      INTEGER NOT NULL REFERENCES company(id),
    name                            VARCHAR(255) NOT NULL,
    salary_amount                   BIGINT NOT NULL CHECK (salary_amount > 0),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(position_key),
    UNIQUE(company_id, name)
);

CREATE TABLE employee(
    id                              SERIAL PRIMARY KEY,
    employee_key                    CHAR(36) NOT NULL,
    company_id                      INTEGER NOT NULL REFERENCES company(id),
    position_id                     INTEGER NOT NULL REFERENCES position(id),
    name                            VARCHAR(255) NOT NULL,
    document_number                 CHAR(14) NOT NULL,
    email                           VARCHAR(255) NOT NULL,
    hired_at                        DATE NOT NULL,
    terminated_at                   DATE,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(employee_key),
    UNIQUE(company_id, document_number),
    CHECK (terminated_at IS NULL OR terminated_at >= hired_at)
);

CREATE TABLE account_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO account_type (enumerator) VALUES
('company'),
('employee'),
('bank'),
('settlement');

CREATE TABLE account_status(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO account_status (enumerator) VALUES
('active'),
('blocked'),
('closed');

CREATE TABLE account(
    id                              SERIAL PRIMARY KEY,
    account_key                     CHAR(36) NOT NULL,
    type_id                         INTEGER NOT NULL REFERENCES account_type(id),
    company_id                      INTEGER REFERENCES company(id),
    employee_id                     INTEGER REFERENCES employee(id),
    balance_amount                  BIGINT NOT NULL CHECK (balance_amount >= 0),
    status_id                       INTEGER NOT NULL REFERENCES account_status(id),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(account_key),
    UNIQUE(company_id),
    UNIQUE(employee_id),
    CHECK (company_id IS NULL OR employee_id IS NULL)
);

CREATE TABLE account_status_event(
    id                              SERIAL PRIMARY KEY,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    status_id                       INTEGER NOT NULL REFERENCES account_status(id),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW())
);

INSERT INTO account (account_key, type_id, balance_amount, status_id)
SELECT gen_random_uuid()::TEXT, account_type.id, 0, account_status.id
FROM account_type, account_status
WHERE account_type.enumerator = 'bank' AND account_status.enumerator = 'active';

INSERT INTO account_status_event (account_id, status_id, event_datetime)
SELECT account.id, account.status_id, NOW()
FROM account
JOIN account_type ON account_type.id = account.type_id
WHERE account_type.enumerator = 'bank';

-- Os ids são fixos porque o índice único do mês, mais abaixo, precisa
-- saber qual é o id de `canceled`, e índice parcial não aceita consulta.
CREATE TABLE payroll_status(
    id                              INTEGER PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO payroll_status (id, enumerator) VALUES
(1, 'pending'),
(2, 'processing'),
(3, 'paid'),
(4, 'canceled');

CREATE TABLE payroll(
    id                              SERIAL PRIMARY KEY,
    payroll_key                     CHAR(36) NOT NULL,
    company_id                      INTEGER NOT NULL REFERENCES company(id),
    reference_month                 DATE NOT NULL CHECK (EXTRACT(DAY FROM reference_month) = 1),
    total_amount                    BIGINT NOT NULL CHECK (total_amount > 0),
    total_fee_amount                BIGINT NOT NULL CHECK (total_fee_amount >= 0),
    settlement_account_id           INTEGER REFERENCES account(id),
    status_id                       INTEGER NOT NULL REFERENCES payroll_status(id),
    paid_at                         TIMESTAMP,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(payroll_key),
    UNIQUE(settlement_account_id)
);

-- Uma folha não cancelada por empresa e mês. A cancelada (status 4) sai
-- do índice e libera o mês para uma folha nova.
CREATE UNIQUE INDEX payroll_company_month_not_canceled
    ON payroll (company_id, reference_month)
    WHERE status_id <> 4;

CREATE TABLE payroll_status_event(
    id                              SERIAL PRIMARY KEY,
    payroll_id                      INTEGER NOT NULL REFERENCES payroll(id),
    status_id                       INTEGER NOT NULL REFERENCES payroll_status(id),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW())
);

CREATE TABLE payroll_item_status(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO payroll_item_status (enumerator) VALUES
('pending'),
('paid'),
('failed'),
('refunded');

CREATE TABLE payroll_item(
    id                              SERIAL PRIMARY KEY,
    payroll_id                      INTEGER NOT NULL REFERENCES payroll(id),
    employee_id                     INTEGER NOT NULL REFERENCES employee(id),
    gross_amount                    BIGINT NOT NULL CHECK (gross_amount > 0),
    net_amount                      BIGINT NOT NULL CHECK (net_amount > 0),
    fee_amount                      BIGINT NOT NULL CHECK (fee_amount >= 0),
    status_id                       INTEGER NOT NULL REFERENCES payroll_item_status(id),
    failure_reason                  VARCHAR(255),
    updated_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(payroll_id, employee_id)
);

CREATE INDEX payroll_item_payroll_status ON payroll_item (payroll_id, status_id);

CREATE TABLE transfer(
    id                              SERIAL PRIMARY KEY,
    transfer_key                    CHAR(36) NOT NULL,
    source_account_id               INTEGER NOT NULL REFERENCES account(id),
    destination_account_id          INTEGER REFERENCES account(id),
    amount                          BIGINT NOT NULL CHECK (amount > 0),
    fee_amount                      BIGINT NOT NULL CHECK (fee_amount >= 0),
    payroll_id                      INTEGER REFERENCES payroll(id),
    payroll_item_id                 INTEGER REFERENCES payroll_item(id),
    idempotency_key                 VARCHAR(255) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(transfer_key),
    UNIQUE(idempotency_key),
    UNIQUE(payroll_id),
    UNIQUE(payroll_item_id),
    CHECK (destination_account_id IS NULL OR destination_account_id <> source_account_id)
);

CREATE TABLE external_destination(
    id                              SERIAL PRIMARY KEY,
    transfer_id                     INTEGER NOT NULL REFERENCES transfer(id),
    bank_code                       CHAR(3) NOT NULL,
    branch_number                   CHAR(4) NOT NULL,
    account_number                  VARCHAR(20) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(transfer_id)
);

CREATE TABLE account_entry(
    id                              SERIAL PRIMARY KEY,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    transfer_id                     INTEGER REFERENCES transfer(id),
    origin                          VARCHAR(20) NOT NULL CHECK (origin IN ('transfer', 'fee', 'test_credit')),
    entry_type                      VARCHAR(10) NOT NULL CHECK (entry_type IN ('credit', 'debit')),
    amount                          BIGINT NOT NULL CHECK (amount > 0),
    balance_after                   BIGINT NOT NULL CHECK (balance_after >= 0),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW())
);