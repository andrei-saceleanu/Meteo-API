CREATE TABLE IF NOT EXISTS Tari (
    id SERIAL PRIMARY KEY,
    nume VARCHAR(100) UNIQUE NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Orase (
    id SERIAL PRIMARY KEY,
    idTara INT,
    nume VARCHAR(100) NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    UNIQUE (idTara, nume),
    FOREIGN KEY (idTara) REFERENCES Tari (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Temperaturi (
    id SERIAL PRIMARY KEY,
    valoare REAL NOT NULL,
    timestamp timestamp DEFAULT CURRENT_TIMESTAMP,
    idOras INT,
    UNIQUE (timestamp, idOras),
    FOREIGN KEY (idOras) REFERENCES Orase (id) ON DELETE CASCADE
);