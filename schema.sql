CREATE TABLE users (
    id INTEGER NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    cash NUMERIC NOT NULL DEFAULT 100000.00,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX username ON users (username);

CREATE TABLE transactions (
    id INTEGER NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    shares INTEGER NOT NULL,
    price REAL NOT NULL,
    date DATETIME NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (id)
);

CREATE INDEX user_id ON transactions (user_id);

CREATE TABLE stock (
    id INTEGER NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    shares_amount INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (id)
);

CREATE INDEX symbol ON stock (symbol);
