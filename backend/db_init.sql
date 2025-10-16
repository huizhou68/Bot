CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    passcode TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    passcode TEXT REFERENCES users(passcode),
    user_message TEXT,
    bot_response TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (passcode) VALUES ('PASS001'), ('PASS002'), ('PASS003');