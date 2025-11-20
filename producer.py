"""
Kafka Producer with Avro Serialization
Produces order messages to Kafka topic
"""

import random
import time
import json
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import config

class OrderProducer:
    def __init__(self):
        """Initialize the Kafka producer with Avro serialization"""
        # Schema Registry configuration
        schema_registry_conf = {'url': config.SCHEMA_REGISTRY_URL}
        self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        
        # Load Avro schema
        with open(config.AVRO_SCHEMA_PATH, 'r') as f:
            schema_str = f.read()
        
        # Initialize Avro serializer
        self.avro_serializer = AvroSerializer(
            self.schema_registry_client,
            schema_str,
            self.order_to_dict
        )
        
        # Producer configuration
        producer_conf = {
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'order-producer'
        }
        
        self.producer = Producer(producer_conf)
        self.string_serializer = StringSerializer('utf_8')
        
        print(f"✓ Producer initialized successfully")
        print(f"✓ Connected to Kafka: {config.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"✓ Schema Registry: {config.SCHEMA_REGISTRY_URL}")
    
    @staticmethod
    def order_to_dict(order, ctx):
        """Convert order object to dictionary for Avro serialization"""
        return {
            'orderId': order['orderId'],
            'product': order['product'],
            'price': order['price']
        }
    
    def delivery_report(self, err, msg):
        """Callback for delivery reports"""
        if err is not None:
            print(f'✗ Message delivery failed: {err}')
        else:
            print(f'✓ Message delivered to {msg.topic()} [partition {msg.partition()}] at offset {msg.offset()}')
    
    def generate_order(self, order_id):
        """Generate a random order"""
        products = ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard', 
                   'Mouse', 'Headphones', 'Webcam', 'Printer', 'Router']
        
        order = {
            'orderId': str(order_id),
            'product': random.choice(products),
            'price': round(random.uniform(10.0, 1000.0), 2)
        }
        
        return order
    
    def produce_order(self, order):
        """Produce a single order message to Kafka"""
        try:
            self.producer.produce(
                topic=config.ORDER_TOPIC,
                key=self.string_serializer(order['orderId']),
                value=self.avro_serializer(
                    order,
                    SerializationContext(config.ORDER_TOPIC, MessageField.VALUE)
                ),
                on_delivery=self.delivery_report
            )
            
            # Trigger delivery report callbacks
            self.producer.poll(0)
            
        except Exception as e:
            print(f'✗ Error producing message: {e}')
    
    def run(self, num_messages=10, interval=2):
        """Produce multiple orders"""
        print(f"\n{'='*60}")
        print(f"Starting to produce {num_messages} orders...")
        print(f"{'='*60}\n")
        
        for i in range(1, num_messages + 1):
            order = self.generate_order(1000 + i)
            
            print(f"\n📦 Producing Order #{i}:")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Product: {order['product']}")
            print(f"   Price: ${order['price']:.2f}")
            
            self.produce_order(order)
            
            if i < num_messages:
                time.sleep(interval)
        
        # Wait for all messages to be delivered
        print(f"\n⏳ Flushing remaining messages...")
        self.producer.flush(config.PRODUCER_FLUSH_TIMEOUT)
        
        print(f"\n{'='*60}")
        print(f"✓ Successfully produced {num_messages} orders!")
        print(f"{'='*60}\n")

def main():
    """Main function"""
    try:
        producer = OrderProducer()
        
        # Produce 20 orders with 2 second intervals
        producer.run(num_messages=20, interval=2)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Producer interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
