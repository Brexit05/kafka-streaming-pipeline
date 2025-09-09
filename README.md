Crypto Streaming Pipeline

An end-to-end real-time data pipeline that ingests live cryptocurrency prices, streams them with Kafka, and stores processed data into a PostgreSQL database using Docker containers.

This project demonstrates how to build a scalable streaming data engineering pipeline, integrating producers, consumers, and persistent storage.

Architecture
         ┌────────────┐       ┌───────────────┐       ┌─────────────┐
         │ CoinGecko  │ ----> │ Kafka Producer │ ----> │   Kafka     │
         │   API      │       │   (Python)    │       │   Broker    │
         └────────────┘       └───────────────┘       └─────────────┘
                                                        │
                                                        ▼
                                            ┌────────────────────┐
                                            │   Kafka Consumer   │
                                            │   (Python)         │
                                            └────────────────────┘
                                                        │
                                                        ▼
                                            ┌────────────────────┐
                                            │   PostgreSQL DB    │
                                            │ (crypto_prices,    │
                                            │  crypto_alerts)    │
                                            └────────────────────┘

Tech Stack

Python → Kafka Producer & Consumer

Kafka → Real-time event streaming

Zookeeper → Kafka coordination

PostgreSQL → Storage for processed data

Docker + Docker Compose → Container orchestration

SQLAlchemy → Database interaction

Workflow

Producer (producer.py)

Fetches live cryptocurrency prices from the CoinGecko API.

Publishes records to two Kafka topics:

crypto_prices → regular price updates.

crypto_alerts → alerts for coins with >5% volatility in 24h.

Kafka Broker

Handles event streaming between producer and consumer.

Consumer (consumer.py)

Subscribes to crypto_prices and crypto_alerts.

Inserts data into PostgreSQL tables:

crypto_prices (symbol, price, market cap, volume, change %, timestamp).

crypto_alerts (symbol, price, change %, alert type).

Database

PostgreSQL container persists the data.

Tables created via init.sql.

📂 Project Structure
kafka-streaming-project/
│── docker-compose.yaml       # Service definitions (Kafka, Zookeeper, Postgres, Producer, Consumer)
│── producer.py               # Kafka producer script
│── consumer.py               # Kafka consumer script
│── config.py                 # Config variables (URLs, DB, API params)
│── init.sql                  # Initializes PostgreSQL schema
│── requirements.txt          # Python dependencies
│── README.md                 # Project documentation
└── .env                      # environment variables

How to Run
1. Clone the repository
git clone https://github.com/Brexit05/kafka-streaming-pipeline.git
cd kafka-streaming-project

2. Start Docker containers
docker-compose up -d

3. Check running services
docker ps

4. Follow producer logs
docker logs -f kafka-streaming-project-producer-1

5. Follow consumer logs
docker logs -f kafka-streaming-project-consumer-1

6. Access PostgreSQL
docker exec -it crypto_postgres psql -U crypto_user -d crypto_db

Example Query

(Get the 5 most recent crypto price updates)

SELECT symbol, price_usd, change_24h, timestamp
FROM crypto_prices
ORDER BY timestamp DESC
LIMIT 5;

Key Learnings

How to containerize a Kafka + Zookeeper + Postgres + Python workflow.

Setting up Kafka producers & consumers in Python.

Managing real-time + persistent storage in a structured database.

Handling schema consistency between stream and batch layers.


Next Steps
Add data visualization with Power BI or Grafana.

Extend to a batch + stream hybrid pipeline (Airflow + Kafka).


Deploy to a cloud environment (AWS/GCP/Azure).
