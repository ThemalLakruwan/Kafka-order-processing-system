"""
Kafka Consumer with Avro Deserialization, Retry Logic, DLQ, and Real-time Aggregation
Consumes order messages and calculates running average of prices
"""

import time
import json
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from confluent_kafka.serialization import StringDeserializer, StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer, AvroSerializer
import config

class OrderConsumer:
    def __init__(self):
        """Initialize the Kafka consumer with Avro deserialization"""
        # Schema Registry configuration
        schema_registry_conf = {'url': config.SCHEMA_REGISTRY_URL}
        self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        
        # Load Avro schema
        with open(config.AVRO_SCHEMA_PATH, 'r') as f:
            schema_str = f.read()
        
        # Initialize Avro deserializer
        self.avro_deserializer = AvroDeserializer(
            self.schema_registry_client,
            schema_str,
            self.dict_to_order
        )
        
        # Consumer configuration
        consumer_conf = {
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': config.CONSUMER_GROUP_ID,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        
        self.consumer = Consumer(consumer_conf)
        
        # Producer for retry and DLQ
        producer_conf = {
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'order-consumer-producer'
        }
        self.producer = Producer(producer_conf)
        
        # Initialize serializers for retry/DLQ
        self.avro_serializer = AvroSerializer(
            self.schema_registry_client,
            schema_str,
            self.order_to_dict
        )
        self.string_serializer = StringSerializer('utf_8')
        self.string_deserializer = StringDeserializer('utf_8')
        
        # Aggregation state
        self.total_price = 0.0
        self.total_orders = 0
        self.running_average = 0.0
        
        # Retry tracking
        self.retry_counts = {}
        
        print(f"✓ Consumer initialized successfully")
        print(f"✓ Connected to Kafka: {config.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"✓ Consumer Group: {config.CONSUMER_GROUP_ID}")
    
    @staticmethod
    def dict_to_order(obj, ctx):
        """Convert dictionary to order object after Avro deserialization"""
        return obj
    
    @staticmethod
    def order_to_dict(order, ctx):
        """Convert order object to dictionary for Avro serialization"""
        return {
            'orderId': order['orderId'],
            'product': order['product'],
            'price': order['price']
        }
    
    def update_aggregation(self, price):
        """Update running average of prices"""
        self.total_orders += 1
        self.total_price += price
        self.running_average = self.total_price / self.total_orders
        
        print(f"\n📊 AGGREGATION UPDATE:")
        print(f"   Total Orders Processed: {self.total_orders}")
        print(f"   Total Price Sum: ${self.total_price:.2f}")
        print(f"   Running Average Price: ${self.running_average:.2f}")
    
    def send_to_retry(self, order, error_msg):
        """Send failed message to retry topic"""
        order_id = order['orderId']
        retry_count = self.retry_counts.get(order_id, 0) + 1
        self.retry_counts[order_id] = retry_count
        
        print(f"\n⚠️  RETRY ATTEMPT {retry_count}/{config.MAX_RETRIES}")
        print(f"   Order ID: {order_id}")
        print(f"   Reason: {error_msg}")
        
        try:
            self.producer.produce(
                topic=config.RETRY_TOPIC,
                key=self.string_serializer(order_id),
                value=self.avro_serializer(
                    order,
                    SerializationContext(config.RETRY_TOPIC, MessageField.VALUE)
                )
            )
            self.producer.flush()
            print(f"   ✓ Sent to retry topic: {config.RETRY_TOPIC}")
        except Exception as e:
            print(f"   ✗ Failed to send to retry topic: {e}")
    
    def send_to_dlq(self, order, error_msg):
        """Send permanently failed message to Dead Letter Queue"""
        order_id = order['orderId']
        
        print(f"\n💀 DEAD LETTER QUEUE")
        print(f"   Order ID: {order_id}")
        print(f"   Reason: {error_msg}")
        print(f"   Max retries ({config.MAX_RETRIES}) exceeded")
        
        # Create DLQ message with error metadata
        dlq_message = {
            'orderId': order['orderId'],
            'product': order['product'],
            'price': order['price']
        }
        
        try:
            self.producer.produce(
                topic=config.DLQ_TOPIC,
                key=self.string_serializer(order_id),
                value=self.avro_serializer(
                    dlq_message,
                    SerializationContext(config.DLQ_TOPIC, MessageField.VALUE)
                )
            )
            self.producer.flush()
            print(f"   ✓ Sent to DLQ topic: {config.DLQ_TOPIC}")
            
            # Clean up retry count
            if order_id in self.retry_counts:
                del self.retry_counts[order_id]
                
        except Exception as e:
            print(f"   ✗ Failed to send to DLQ: {e}")
    
    def process_order(self, order):
        """
        Process an order message
        Validates price and processes the order
        """
        order_id = order['orderId']
        
        # Validate price - negative prices are invalid
        if order['price'] < 0:
            raise ValueError(f"Invalid price: ${order['price']:.2f} - price cannot be negative")
        
        # Successfully process the order
        print(f"\n✓ ORDER PROCESSED SUCCESSFULLY")
        print(f"   Order ID: {order_id}")
        print(f"   Product: {order['product']}")
        print(f"   Price: ${order['price']:.2f}")
        
        # Update aggregation
        self.update_aggregation(order['price'])
    
    def handle_message(self, msg, topic):
        """Handle a single message with retry and DLQ logic"""
        try:
            # Deserialize message
            order_id = self.string_deserializer(msg.key()) if msg.key() else None
            order = self.avro_deserializer(
                msg.value(),
                SerializationContext(topic, MessageField.VALUE)
            )
            
            print(f"\n{'='*60}")
            print(f"📨 Received Order from topic: {topic}")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Product: {order['product']}")
            print(f"   Price: ${order['price']:.2f}")
            
            # Check current retry count
            order_id = order['orderId']
            current_retry_count = self.retry_counts.get(order_id, 0)
            if current_retry_count > 0:
                print(f"   Retry attempt: {current_retry_count}/{config.MAX_RETRIES}")
            
            # Process the order
            self.process_order(order)
            
            # Success - clear retry count if exists
            if order_id in self.retry_counts:
                del self.retry_counts[order_id]
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ ERROR PROCESSING ORDER: {error_msg}")
            
            # Handle retry logic
            order_id = order['orderId'] if 'order' in locals() else 'unknown'
            retry_count = self.retry_counts.get(order_id, 0)
            
            if retry_count < config.MAX_RETRIES:
                # Send to retry topic
                self.send_to_retry(order, error_msg)
                return False
            else:
                # Max retries exceeded, send to DLQ
                self.send_to_dlq(order, error_msg)
                return False
    
    def run(self):
        """Start consuming messages"""
        # Subscribe to both main and retry topics
        topics = [config.ORDER_TOPIC, config.RETRY_TOPIC]
        self.consumer.subscribe(topics)
        
        print(f"\n{'='*60}")
        print(f"🚀 Consumer started!")
        print(f"   Subscribed to topics: {', '.join(topics)}")
        print(f"   DLQ topic: {config.DLQ_TOPIC}")
        print(f"   Max retries: {config.MAX_RETRIES}")
        print(f"{'='*60}\n")
        print(f"Waiting for messages... (Press Ctrl+C to stop)\n")
        
        try:
            while True:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        # Topic doesn't exist yet, wait and continue
                        print(f"⏳ Waiting for topic '{msg.error().name()}' to be created...")
                        time.sleep(2)
                        continue
                    else:
                        print(f"⚠️  Kafka error: {msg.error()}")
                        continue
                
                # Handle the message
                success = self.handle_message(msg, msg.topic())
                
                # Always commit offset after handling (whether success or failure)
                # This ensures we don't reprocess the same message from the original topic
                # Failed messages are already sent to retry/DLQ topics
                self.consumer.commit(asynchronous=False)
                
        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print(f"⚠️  Consumer interrupted by user")
            print(f"\n📊 FINAL STATISTICS:")
            print(f"   Total Orders Processed: {self.total_orders}")
            print(f"   Total Price Sum: ${self.total_price:.2f}")
            print(f"   Final Running Average: ${self.running_average:.2f}")
            print(f"{'='*60}\n")
        
        finally:
            self.consumer.close()
            print(f"✓ Consumer closed gracefully\n")

def main():
    """Main function"""
    try:
        consumer = OrderConsumer()
        consumer.run()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
