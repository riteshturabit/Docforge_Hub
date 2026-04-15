CREATE TABLE company_context (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_location VARCHAR(255),
    company_size VARCHAR(50),
    company_stage VARCHAR(50),
    product_type VARCHAR(100),
    target_customers TEXT,
    company_mission TEXT,
    company_vision TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DELETE FROM company_context;

SELECT COUNT(*) FROM company_context;
DELETE FROM company_context;