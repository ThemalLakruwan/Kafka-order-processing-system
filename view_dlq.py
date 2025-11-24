"""
DLQ Viewer - Read and display messages from Dead Letter Queue
Handles Avro deserialization properly
"""

from confluent_kafka import Consumer, KafkaException
from confluent_kafka.serialization import StringDeserializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
import config

class DLQViewer:
    def __init__(self):
        """Initialize DLQ viewer with Avro deserialization"""
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
            lambda obj, ctx: obj  # Return the deserialized object as-is
        )
        
        # Consumer configuration
        consumer_conf = {
            'bootstrap.servers': config.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'dlq-viewer-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        
        self.consumer = Consumer(consumer_conf)
        self.string_deserializer = StringDeserializer('utf_8')
        
        print(f"✓ DLQ Viewer initialized")
        print(f"✓ Connected to Kafka: {config.KAFKA_BOOTSTRAP_SERVERS}")
    
    def view_messages(self, max_messages=10):
        """View messages from DLQ topic"""
        self.consumer.subscribe([config.DLQ_TOPIC])
        
        print(f"\n{'='*80}")
        print(f"💀 DEAD LETTER QUEUE - Failed Messages")
        print(f"{'='*80}\n")
        
        messages_read = 0
        
        try:
            while messages_read < max_messages:
                msg = self.consumer.poll(timeout=5.0)
                
                if msg is None:
                    if messages_read == 0:
                        print("ℹ️  No messages in DLQ")
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
                    SerializationContext(config.DLQ_TOPIC, MessageField.VALUE)
                )
                
                messages_read += 1
                
                # Display message details
                print(f"{'─'*80}")
                print(f"💀 DLQ Message #{messages_read}")
                print(f"{'─'*80}")
                print(f"📦 Order ID:        {order_id}")
                print(f"📦 Product:         {order.get('product', 'N/A')}")
                print(f"💵 Price:           ${order.get('price', 0):.2f}")
                print(f"📍 Partition:       {msg.partition()}")
                print(f"📍 Offset:          {msg.offset()}")
                
                # Determine failure reason
                if order.get('price', 0) < 0:
                    print(f"❌ Failure Reason:  Negative price (${order.get('price', 0):.2f})")
                    print(f"ℹ️  Status:          Permanently failed after {config.MAX_RETRIES} retry attempts")
                else:
                    print(f"❌ Failure Reason:  Unknown validation error")
                    print(f"ℹ️  Status:          Permanently failed after {config.MAX_RETRIES} retry attempts")
                
                print()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Viewer interrupted by user")
        except Exception as e:
            print(f"\n✗ Error reading DLQ: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.consumer.close()
        
        print(f"{'='*80}")
        print(f"✓ DLQ Viewer complete - Total messages: {messages_read}")
        print(f"{'='*80}\n")

def main():
    """Main function"""
    try:
        viewer = DLQViewer()
        
        # View up to 20 messages from DLQ
        viewer.view_messages(max_messages=20)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
