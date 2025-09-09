from sqlalchemy import create_engine, text
from kafka import KafkaConsumer
import json
from config import PG_URL
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler("consumer.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)


class CryptoDataConsumer:
    def __init__(self, bootstrap_servers: list[str] = ['kafka:9092'], topics: list[str] = ['crypto_prices', 'crypto_alerts']):
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda c: json.loads(c.decode('utf-8')),
            key_deserializer=lambda c: c.decode('utf-8') if c else None,
            group_id='crypto-data-processor',
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        self.db_connection = None
        self.connect_db()

    def connect_db(self):
        try:
            self.db_connection = create_engine(PG_URL)
            self.db_connection.connect()
            logger.info("PostgreSQL database connection established.")
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL database: {e}")

    def store_price_data(self, data: dict[str, any]):
        try:
            with self.db_connection.begin() as conn:
                query = text("""
                    INSERT INTO crypto_prices(symbol, price_usd, market_cap, volume_24h, change_24h, timestamp)
                    VALUES (:symbol, :price_usd, :market_cap, :volume_24h, :change_24h, :timestamp)
                """)
                conn.execute(query, data)
                logger.info(f"Inserted price data for {data['symbol']} into database.")
                return True
        except Exception as e:
            logger.error(f"Error inserting price data into database: {e}")
            return False

    def store_alert_data(self, data: dict[str, any]):
        try:
            with self.db_connection.begin() as conn:
                query = text("""
                    INSERT INTO crypto_alerts(symbol, price_usd, change_percentage, alert_type)
                    VALUES (:symbol, :price_usd, :change_percentage, :alert_type)
                """)
                conn.execute(query, data)
                logger.info(f"Inserted alert data for {data['symbol']} into database.")
                return True
        except Exception as e:
            logger.error(f"Error inserting alert data into database: {e}")
            return False

    def run(self, message: dict[str, any]):
        try:
            required_fields = ['symbol', 'price_usd', 'timestamp']
            if not all(field in message for field in required_fields):
                logger.warning(f"Missing required fields in message: {message.keys()}")
                return False
            success = self.store_price_data(message)
            if success:
                change_24h = message.get('change_24h', 0)
                if change_24h and abs(change_24h) > 10:
                    logger.info(f"SIGNIFICANT MOVE: {message['symbol']}")
            return success
        except Exception as e:
            logger.error(f"Error processing crypto price: {e}")
            return False

    def process_crypto_alert(self, message: dict[str, any]):
        try:
            required_fields = ["symbol", "price_usd"]
            if not all(field in message for field in required_fields):
                logger.warning(f"Skipping invalid alert, missing fields: {message}")
                return False
            success = self.store_alert_data(message)
            if success:
                change_24h = message.get("change_24h", 0)
                alert_type = message.get("alert_type", "unknown")
                if abs(change_24h) > 20:
                    logger.error(
                        f"ALERT: {message['symbol']} - "
                        f"Type: {alert_type} - "
                        f"Price: ${message['price_usd']:.2f} - "
                        f"Change: {change_24h:.2f}%"
                    )
                else:
                    logger.warning(
                        f"ALERT: {message['symbol']} - "
                        f"Type: {alert_type} - "
                        f"Price: ${message['price_usd']:.2f} - "
                        f"Change: {change_24h:.2f}%"
                    )
            return success
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            return False

    def get_latest_prices(self, limit: int = 10):
        try:
            with self.db_connection.connect() as conn:
                query = text("""
                    SELECT symbol, price_usd, change_24h, timestamp
                    FROM (
                        SELECT symbol, price_usd, change_24h, timestamp,
                               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
                        FROM crypto_prices
                    ) AS t
                    WHERE rn = 1
                    LIMIT :limit;
                """)
                result = conn.execute(query, {"limit": limit}).fetchall()
                return result
        except Exception as e:
            logger.error(f"Error fetching latest prices: {e}")
            return []

    def run_consumer(self):
        logger.info("Starting crypto data consumer.")
        try:
            for message in self.consumer:
                topic = message.topic
                key = message.key
                value = message.value
                logger.info(f"Received from topic={topic} | key={key} | value={json.dumps(value, indent=2)}")
                if topic == 'crypto-prices':
                    success = self.run(value)
                elif topic == 'crypto-alerts':
                    success = self.process_crypto_alert(value)
                else:
                    logger.warning(f"Unknown topic: {topic}, skipping...")
                    continue
                if not success:
                    logger.error(f"Failed to process message with key={key} from topic={topic}")
                if success and message.offset % 10 == 0:
                    latest_prices = self.get_latest_prices(3)
                    logger.info("Latest Prices Snapshot:")
                    for row in latest_prices:
                        logger.info(
                            f"Symbol: {row['symbol']} | "
                            f"Price: ${row['price_usd']:.2f} | "
                            f"Change 24h: {row['change_24h']:.2f}% | "
                            f"Timestamp: {row['timestamp']}"
                        )
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
        finally:
            self.consumer.close()
            if self.db_connection:
                self.db_connection.dispose()
            logger.info("Consumer closed.")


if __name__ == "__main__":
    consumer = CryptoDataConsumer()
    consumer.run_consumer()
