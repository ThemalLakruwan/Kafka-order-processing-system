# Kafka Order Processing System

A complete Kafka-based system that produces and consumes order messages with Avro serialization, featuring real-time price aggregation, retry logic, and Dead Letter Queue (DLQ) for failed messages.

## 🎯 Features

✅ **Avro Serialization** - Messages are serialized using Avro schema for efficient data transfer  
✅ **Real-time Aggregation** - Running average of order prices calculated in real-time  
✅ **Retry Logic** - Automatic retry mechanism for temporary failures (configurable max retries)  
✅ **Dead Letter Queue** - Permanently failed messages sent to DLQ after max retries  
✅ **Docker-based Setup** - Easy deployment with Docker Compose  
✅ **Schema Registry** - Centralized schema management with Confluent Schema Registry  

## 📋 Prerequisites

Before running this system, ensure you have the following installed:

- **Docker Desktop** (version 20.10 or later)
- **Docker Compose** (version 1.29 or later)
- **Python** (version 3.8 or later)
- **pip** (Python package manager)

## 📁 Project Structure

```
BigDataCode/
├── schemas/
│   └── order.avsc          # Avro schema definition
├── docker-compose.yml       # Kafka infrastructure setup
├── config.py               # Configuration file
├── producer.py             # Kafka producer
├── consumer.py             # Kafka consumer with retry & DLQ
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Setup Instructions

### Step 1: Clone/Navigate to Project Directory

```powershell
cd "d:\Ruhuna FoE\Semester 08\BigData\Assignment\BigDataCode"
```

### Step 2: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### Step 3: Start Kafka Infrastructure

Start Zookeeper, Kafka, and Schema Registry using Docker Compose:

```powershell
docker-compose up -d
```

**Verify services are running:**

```powershell
docker-compose ps
```

You should see three containers running:
- `zookeeper` (port 2181)
- `kafka` (port 9092)
- `schema-registry` (port 8081)

### Step 4: Wait for Services to Initialize

Wait about 30-60 seconds for all services to fully initialize.

## 🎬 Running the Demo

### Terminal 1: Start the Consumer

Open a terminal and run:

```powershell
python consumer.py
```

**Expected Output:**
```
✓ Consumer initialized successfully
✓ Connected to Kafka: localhost:9092
✓ Consumer Group: order-consumer-group
============================================================
🚀 Consumer started!
   Subscribed to topics: orders, orders-retry
   DLQ topic: orders-dlq
   Max retries: 3
============================================================
Waiting for messages... (Press Ctrl+C to stop)
```

### Terminal 2: Start the Producer

Open another terminal and run:

```powershell
python producer.py
```

**Expected Output:**
```
✓ Producer initialized successfully
✓ Connected to Kafka: localhost:9092
✓ Schema Registry: http://localhost:8081
============================================================
Starting to produce 20 orders...
============================================================

📦 Producing Order #1:
   Order ID: 1001
   Product: Laptop
   Price: $756.32
✓ Message delivered to orders [partition 0] at offset 0
...
```

### Observing the System in Action

**In the Consumer Terminal, you'll see:**

1. **Successful Processing:**
```
============================================================
📨 Received Order from topic: orders
   Order ID: 1001
   Product: Laptop
   Price: $756.32

✓ ORDER PROCESSED SUCCESSFULLY
   Order ID: 1001
   Product: Laptop
   Price: $756.32

📊 AGGREGATION UPDATE:
   Total Orders Processed: 1
   Total Price Sum: $756.32
   Running Average Price: $756.32
```

2. **Retry Logic (when failure occurs):**
```
✗ ERROR PROCESSING ORDER: Simulated processing error (random failure)

⚠️  RETRY ATTEMPT 1/3
   Order ID: 1005
   Reason: Simulated processing error
   ✓ Sent to retry topic: orders-retry
```

3. **Dead Letter Queue (after max retries):**
```
💀 DEAD LETTER QUEUE
   Order ID: 1008
   Reason: Simulated processing error
   Max retries (3) exceeded
   ✓ Sent to DLQ topic: orders-dlq
```

## 📊 System Architecture

```
┌─────────────┐
│  Producer   │
│ (producer.py)│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Kafka Topic       │
│     "orders"        │
└──────┬──────────────┘
       │
       ▼
┌─────────────┐
│  Consumer   │◄──── Retry Topic
│ (consumer.py)│     "orders-retry"
└──────┬──────┘
       │
       ├─── Success ──► Aggregation (Running Average)
       │
       └─── Failure ──► DLQ Topic
                       "orders-dlq"
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
SCHEMA_REGISTRY_URL = 'http://localhost:8081'

# Topics
ORDER_TOPIC = 'orders'
DLQ_TOPIC = 'orders-dlq'
RETRY_TOPIC = 'orders-retry'

# Consumer Configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
```

## 📝 Avro Schema (order.avsc)

```json
{
  "type": "record",
  "name": "Order",
  "namespace": "com.bigdata.orders",
  "fields": [
    {
      "name": "orderId",
      "type": "string",
      "doc": "Unique identifier for the order"
    },
    {
      "name": "product",
      "type": "string",
      "doc": "Name of the purchased item"
    },
    {
      "name": "price",
      "type": "float",
      "doc": "Price of the product"
    }
  ]
}
```

## 🧪 Testing Different Scenarios

### Test 1: Normal Operation
- Run producer and consumer
- Observe successful message processing and running average calculation

### Test 2: Retry Logic
- Messages have a 10% simulated failure rate
- Watch for retry attempts in consumer output
- Observe messages being sent to retry topic

### Test 3: Dead Letter Queue
- After 3 failed retry attempts, messages go to DLQ
- Check DLQ topic for permanently failed messages

### Test 4: View Messages in Topics

**View orders topic:**
```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders --from-beginning --max-messages 5
```

**View DLQ topic:**
```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders-dlq --from-beginning
```

**View retry topic:**
```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders-retry --from-beginning
```

## 🛑 Stopping the System

### Stop Consumer
Press `Ctrl+C` in the consumer terminal to see final statistics:
```
============================================================
⚠️  Consumer interrupted by user

📊 FINAL STATISTICS:
   Total Orders Processed: 18
   Total Price Sum: $9234.56
   Final Running Average: $512.92
============================================================
```

### Stop Kafka Infrastructure
```powershell
docker-compose down
```

### Stop and Remove Volumes (clean slate)
```powershell
docker-compose down -v
```

## 🐛 Troubleshooting

### Issue: "Connection refused" error

**Solution:** Ensure Docker services are running
```powershell
docker-compose ps
docker-compose up -d
```

### Issue: Schema Registry not available

**Solution:** Wait longer for services to initialize (60 seconds) or restart:
```powershell
docker-compose restart schema-registry
```

### Issue: "No module named 'confluent_kafka'"

**Solution:** Install Python dependencies
```powershell
pip install -r requirements.txt
```

### Issue: Port already in use

**Solution:** Stop conflicting services or change ports in docker-compose.yml

## 📈 Key Metrics Tracked

1. **Total Orders Processed** - Count of successfully processed orders
2. **Total Price Sum** - Cumulative sum of all order prices
3. **Running Average Price** - Real-time average price calculation
4. **Retry Attempts** - Number of retry attempts per failed message
5. **DLQ Messages** - Count of permanently failed messages

## 🎓 Learning Outcomes

This system demonstrates:
- ✅ Kafka producer and consumer implementation
- ✅ Avro schema definition and serialization
- ✅ Schema Registry integration
- ✅ Real-time stream processing and aggregation
- ✅ Error handling with retry logic
- ✅ Dead Letter Queue pattern implementation
- ✅ Docker containerization for distributed systems

## 📚 Technologies Used

- **Apache Kafka** - Distributed streaming platform
- **Apache Avro** - Data serialization system
- **Confluent Schema Registry** - Schema management
- **Python** - Programming language
- **Docker & Docker Compose** - Containerization
- **confluent-kafka-python** - Kafka client library

## 👨‍💻 Development Notes

- Producer sends 20 messages with 2-second intervals
- Consumer has 10% simulated failure rate for demonstration
- Retry delay is 2 seconds (configurable)
- Maximum 3 retry attempts before sending to DLQ

## 📝 Assignment Requirements Checklist

✅ Kafka-based system with producer and consumer  
✅ Avro serialization for all messages  
✅ Real-time aggregation (running average of prices)  
✅ Retry logic for temporary failures  
✅ Dead Letter Queue (DLQ) for permanently failed messages  
✅ Live demonstration capability  
✅ Git repository with complete code  
✅ Comprehensive documentation  

## 🔗 Additional Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Avro Documentation](https://avro.apache.org/docs/current/)
- [Confluent Python Client](https://docs.confluent.io/kafka-clients/python/current/overview.html)

---

**Author:** Big Data Assignment  
**Date:** November 2025  
**Version:** 1.0
