-- Template_questions

CREATE TABLE template_questions(
id SERIAL PRIMARY KEY,
template_id INT REFERENCES document_templates(id) ON DELETE CASCADE,
question TEXT NOT NULL,
input_type VARCHAR(50) DEFAULT 'text',
required BOOLEAN DEFAULT TRUE,
question_order INT
);

DELETE FROM template_questions;

ALTER TABLE template_questions ADD COLUMN section_title TEXT;
ALTER TABLE template_questions ADD COLUMN section_order INTEGER;

SELECT * FROM template_questions;