CREATE TABLE IF NOT EXISTS crypto_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price_usd DECIMAL(20,6) NOT NULL,
    market_cap BIGINT,
    volume_24h BIGINT,
    change_24h DECIMAL(10,6),
    timestamp TIMESTAMP NOT NULL,
    dwh_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_alerts(
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price_usd DECIMAL(20,6) NOT NULL,
    change_percentage DECIMAL(10,6) NOT NULL,
    alert_type VARCHAR(20) NOT NULL,
    dwh_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crypto ON crypto_prices (symbol, timestamp DESC);
CREATE INDEX idx_alerts ON price_alerts (symbol);
