BEGIN TRANSACTION;
CREATE TABLE chat_details
                 (id INTEGER PRIMARY KEY,
                  chat_session_id INTEGER,
                  timestamp TIMESTAMP,
                  user_input TEXT,
                  system_response TEXT,
                  input_tokens INTEGER,
                  output_tokens INTEGER,
                  FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(id));
