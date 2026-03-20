-- Document_sections 
CREATE TABLE document_sections (
id SERIAL PRIMARY KEY,
document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
section_title VARCHAR(255) NOT NULL,
section_content TEXT,
section_order INT,
status VARCHAR(50) DEFAULT 'draft',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM document_sections;

DELETE FROM document_sections;

ALTER TABLE document_sections
ADD COLUMN is_completed BOOLEAN DEFAULT FALSE;

SELECT section_title, section_content
FROM document_sections;

SELECT section_title, section_content
FROM document_sections
WHERE document_id='2004f5db-9f7b-4bc5-8178-b61c164f7232';

SELECT * FROM document_sections
WHERE document_id='2004f5db-9f7b-4bc5-8178-b61c164f7232';


SELECT section_title, section_content
FROM document_sections
WHERE document_id = '0728d04c-2901-412d-a729-6cd1dc43e133'
ORDER BY section_title;



