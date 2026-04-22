-- StateCase Assistant Database Schema

-- User sessions with persistent state
CREATE TABLE IF NOT EXISTS sc_sessions (
    id              SERIAL PRIMARY KEY,
    session_id      VARCHAR(200) UNIQUE NOT NULL,
    user_industry   VARCHAR(100),
    current_intent  VARCHAR(200),
    state           VARCHAR(50)  DEFAULT 'idle',
    last_retrieved  JSONB,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sc_sessions_session_id
ON sc_sessions(session_id);

-- Full conversation history per session
CREATE TABLE IF NOT EXISTS sc_messages (
    id          SERIAL PRIMARY KEY,
    session_id  VARCHAR(200) NOT NULL,
    role        VARCHAR(20)  NOT NULL,
    content     TEXT         NOT NULL,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sc_messages_session
ON sc_messages(session_id);

-- Notion tickets created for unanswered questions
CREATE TABLE IF NOT EXISTS sc_tickets (
    id                SERIAL PRIMARY KEY,
    session_id        VARCHAR(200),
    notion_ticket_id  VARCHAR(200),
    question          TEXT,
    attempted_sources JSONB,
    summary           TEXT,
    priority          VARCHAR(20)  DEFAULT 'Medium',
    status            VARCHAR(50)  DEFAULT 'Open',
    assigned_owner    VARCHAR(200) DEFAULT 'Support Team',
    created_at        TIMESTAMP    DEFAULT NOW(),
    updated_at        TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sc_tickets_session
ON sc_tickets(session_id);