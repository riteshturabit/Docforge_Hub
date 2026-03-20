-- Documents
CREATE TABLE documents(
id UUID PRIMARY KEY,
template_id INT REFERENCES document_templates(id) ON DELETE CASCADE,
title VARCHAR(255) NOT NULL,
version VARCHAR(255) DEFAULT 'v1.0',
created_by VARCHAR(255),
status VARCHAR(50) DEFAULT 'draft',
tags TEXT[],
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM documents LIMIT 1;
ALTER TABLE documents ADD COLUMN company_id INT REFERENCES company_context(id);

ALTER TABLE documents ADD COLUMN notion_page_id TEXT;

SELECT * FROM documents;
SELECT * FROM documents ORDER BY created_at DESC;

SELECT id, template_id, company_id, created_at
FROM documents
ORDER BY created_at DESC;

DELETE FROM documents;
SELECT title, version FROM documents WHERE id='1513da0e-149e-4028-985d-d65f06b2661a';

SELECT 
            dt.name AS Name,
            d.version,
            dt.document_type_id,
            t.name AS type
       FROM documents d
       JOIN document_templates dt ON d.template_id = dt.id
       JOIN document_types t ON dt.document_type_id = t.id


SELECT 
    d.id,
    d.version,
    dt.industry,
    dty.name AS doc_type,
    dep.name AS department
FROM documents d
JOIN document_templates dt ON d.template_id = dt.id
JOIN document_types dty ON dt.document_type_id = dty.id
JOIN departments dep ON dt.department_id = dep.id
WHERE d.id = '5470c216-550b-405b-ae0c-f779d0dc2e0b';
