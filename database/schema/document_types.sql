-- Document_types

CREATE TABLE document_types(
id SERIAL PRIMARY KEY,
name VARCHAR(50) UNIQUE NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO document_types (name) VALUES
('Policy'),
('SOP'),
('Documentation'),
('Plan'),
('Report');

SELECT * FROM document_types;
