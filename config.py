"""
Configuration file for Kafka system
"""

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
SCHEMA_REGISTRY_URL = 'http://localhost:8081'

# Topics
ORDER_TOPIC = 'orders'
DLQ_TOPIC = 'orders-dlq'
RETRY_TOPIC = 'orders-retry'

# Consumer Configuration
CONSUMER_GROUP_ID = 'order-consumer-group'
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Producer Configuration
PRODUCER_FLUSH_TIMEOUT = 10

# Avro Schema Path
AVRO_SCHEMA_PATH = 'schemas/order.avsc'
