import requests
from datetime import datetime, timezone
import json
from kafka import KafkaProducer
import logging
from config import URL , PARAMS, SYMBOL
import time

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s-%(levelname)s-%(message)s',
                    handlers= [logging.FileHandler('producer.log'),logging.StreamHandler()])
logger = logging.getLogger(__name__)



class CryptoDataProducer:
    """Fetches live cryptocurrency and streams to Kafka."""
    def __init__(self, bootstrap_servers: list[str] = ['kafka:9092']):
        """"Sets up Kafka Producer."""
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                                      value_serializer=lambda p:json.dumps(p, default=str).encode('utf-8'),
                                      key_serializer=lambda p: p.encode('utf-8') if p else None,
                                      retries=3,
                                      retry_backoff_ms=1000)
        self.symbols = SYMBOL
    def fetch_crypto_data(self):
        """ Fetches live cryptocurrency data from CoinGecko API."""
        try:
            response = requests.get(URL, params=PARAMS ,timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching crypto data: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
    def run(self, raw_data: dict):
        """ Processes raw data and sends individual records to Kafka. """
        sent_count = 0
        current_time = datetime.now(timezone.utc).isoformat()
        for coin_id, data in raw_data.items():
            try:
                message = {'symbol': coin_id,
                           'price_usd': float(data['usd']),
                           'market_cap': data.get('usd_market_cap'),
                           'volume_24h': data.get('usd_24h_vol'),
                           'change_24h': data.get('usd_24h_change'),
                           'timestamp': current_time,
                           'source': 'CoinGecko'
                           }
                self.producer.send(topic='crypto_prices', key=coin_id, value=message)
                change_24h = data.get('usd_24h_change',0)
                if abs(change_24h) > 5:
                    logger.warning(f"High volatility detected for {coin_id}: {change_24h}% change in 24h")
                    alert_message = {**message, 'alert': 'high volatility','volatility_threshold': 5.0}
                    self.producer.send(topic='crypto_alerts', key=f"{coin_id}-alert", value=alert_message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error processing {coin_id}: {e}")
                continue
        self.producer.flush()
        return sent_count
    def run_streaming(self, interval_seconds: int = 60):
        """Run continuous streaming"""
        logger.info(f"Starting crypto data streaming every {interval_seconds} seconds")
        try:
            while True:
                start_time = time.time()
                raw_data = self.fetch_crypto_data()
                if raw_data:
                    sent_count = self.run(raw_data)
                    logger.info(f"Successfully sent {sent_count} crypto price updates to Kafka.")
                else:
                    logger.warning("No data received, skipping this cycle.")
                processing_time = time.time() - start_time
                sleep_time = max(0, interval_seconds - processing_time)
                if sleep_time > 0:
                    logger.info(f"Sleeping for {sleep_time} seconds before next fetch.")
                    time.sleep(sleep_time)
                else:
                    logger.warning("Processing took longer than the interval, interval time might need to be increased. Fetching next data immediately.")
        except KeyboardInterrupt:
            logger.info("Stopping crypto data streaming...")
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        finally:
            self.producer.close()
            logger.info("Kafka producer closed.")   

if __name__ == "__main__":
    producer = CryptoDataProducer()
    producer.run_streaming(interval_seconds=60)

