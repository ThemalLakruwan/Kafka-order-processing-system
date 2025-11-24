"""
Retry Queue Viewer - Read and display messages from Retry Queue
Handles Avro deserialization properly
"""

from confluent_kafka import Consumer, KafkaException
from confluent_kafka.serialization import StringDeserializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
import config

class RetryViewer:
    def __init__(self):
        """Initialize Retry viewer with Avro deserialization"""
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
            lambda obj, ctx: obj
        )
        
        # Consumer configuration
        consumer_conf = {
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'retry-viewer-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        
        self.consumer = Consumer(consumer_conf)
        self.string_deserializer = StringDeserializer('utf_8')
        
        print(f"✓ Retry Viewer initialized")
        print(f"✓ Connected to Kafka: {config.KAFKA_BOOTSTRAP_SERVERS}")
    
    def view_messages(self, max_messages=10):
        """View messages from Retry topic"""
        self.consumer.subscribe([config.RETRY_TOPIC])
        
        print(f"\n{'='*80}")
        print(f"🔄 RETRY QUEUE - Messages Waiting for Retry")
        print(f"{'='*80}\n")
        
        messages_read = 0
        
        try:
            while messages_read < max_messages:
                msg = self.consumer.poll(timeout=5.0)
                
                if msg is None:
                    if messages_read == 0:
                        print("ℹ️  No messages in Retry Queue")
                    else:
                        print(f"\n✓ No more messages (read {messages_read} total)")
                    break
                
                if msg.error():
                    print(f"✗ Consumer error: {msg.error()}")
                    continue
                
                # Deserialize key and value
                order_id = self.string_deserializer(msg.key())
                order = self.avro_deserializer(
                    msg.value(),
                    SerializationContext(config.RETRY_TOPIC, MessageField.VALUE)
                )
                
                messages_read += 1
                
                # Display message details
                print(f"{'─'*80}")
                print(f"🔄 Retry Message #{messages_read}")
                print(f"{'─'*80}")
                print(f"📦 Order ID:        {order_id}")
                print(f"📦 Product:         {order.get('product', 'N/A')}")
                print(f"💵 Price:           ${order.get('price', 0):.2f}")
                print(f"📍 Partition:       {msg.partition()}")
                print(f"📍 Offset:          {msg.offset()}")
                
                # Show issue
                if order.get('price', 0) < 0:
                    print(f"⚠️  Issue:           Negative price (${order.get('price', 0):.2f})")
                    print(f"ℹ️  Status:          Waiting for retry processing")
                else:
                    print(f"⚠️  Issue:           Validation error")
                    print(f"ℹ️  Status:          Waiting for retry processing")
                
                print()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Viewer interrupted by user")
        except Exception as e:
            print(f"\n✗ Error reading Retry Queue: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.consumer.close()
        
        print(f"{'='*80}")
        print(f"✓ Retry Viewer complete - Total messages: {messages_read}")
        print(f"{'='*80}\n")

def main():
    """Main function"""
    try:
        viewer = RetryViewer()
        
        # View up to 20 messages from Retry Queue
        viewer.view_messages(max_messages=20)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
