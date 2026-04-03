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

UPDATE document_sections
SET section_content = REGEXP_REPLACE(
    REGEXP_REPLACE(
        REGEXP_REPLACE(section_content, '\*{1,3}([^*]+)\*{1,3}', '\1', 'g'),
        '#{1,6}\s*', '', 'g'
    ),
    '_{1,3}([^_]+)_{1,3}', '\1', 'g'
);

ALTER TABLE document_sections ADD COLUMN IF NOT EXISTS version VARCHAR(10) DEFAULT 'v1.0';
ALTER TABLE document_sections ADD COLUMN IF NOT EXISTS is_latest BOOLEAN DEFAULT TRUE;
ALTER TABLE document_sections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

SELECT COUNT(*) as sections FROM document_sections;
