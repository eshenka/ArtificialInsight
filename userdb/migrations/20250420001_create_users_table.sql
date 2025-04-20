CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(256) NOT NULL,
    language VARCHAR(50) NOT NULL DEFAULT 'en',
    llm_preference VARCHAR(100),
    description TEXT,
    num_requests INTEGER NOT NULL DEFAULT 0
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_token ON users(token);
