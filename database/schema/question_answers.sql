CREATE TABLE question_answers(
id SERIAL PRIMARY KEY,
document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
questions TEXT NOT NULL,
answer TEXT NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


SELECT * FROM question_answers;

INSERT INTO question_answers(document_id, questions, answer)
VALUES(
'202eb138-6f48-49df-b513-d378aebde0d0',
'What types of leave are included?',
'SL,EL,CL'
);
