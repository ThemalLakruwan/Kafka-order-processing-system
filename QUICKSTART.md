# Quick Start Guide

## 🚀 Fast Setup & Demo (5 minutes)

### 1. Install Dependencies (1 minute)
```powershell
pip install -r requirements.txt
```

### 2. Start Kafka (1 minute)
```powershell
docker-compose up -d
```

Wait 60 seconds for services to initialize.

### 3. Open Two Terminals

**Terminal 1 - Start Consumer:**
```powershell
python consumer.py
```

**Terminal 2 - Start Producer:**
```powershell
python producer.py
```

### 4. Watch the Magic! 🎬

You'll see:
- ✅ Orders being produced and consumed
- 📊 Running average price updates
- ⚠️ Retry attempts for failed messages
- 💀 DLQ for permanently failed messages

### 5. Stop Everything

**Stop Consumer:** Press `Ctrl+C` in Terminal 1

**Stop Producer:** Wait for completion or press `Ctrl+C`

**Stop Kafka:**
```powershell
docker-compose down
```

---

## 📊 What You'll Observe

### Producer Terminal Output:
```
✓ Producer initialized successfully
📦 Producing Order #1:
   Order ID: 1001
   Product: Laptop
   Price: $756.32
✓ Message delivered to orders [partition 0] at offset 0
```

### Consumer Terminal Output:
```
📨 Received Order from topic: orders
   Order ID: 1001
   Product: Laptop
   Price: $756.32

✓ ORDER PROCESSED SUCCESSFULLY

📊 AGGREGATION UPDATE:
   Total Orders Processed: 1
   Running Average Price: $756.32
```

### When Failures Occur:
```
⚠️  RETRY ATTEMPT 1/3
   Order ID: 1005
   ✓ Sent to retry topic: orders-retry
```

### When Max Retries Exceeded:
```
💀 DEAD LETTER QUEUE
   Order ID: 1008
   Max retries (3) exceeded
   ✓ Sent to DLQ topic: orders-dlq
```

---

## 🧪 Quick Tests

### Test 1: View All Topics
```powershell
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Test 2: View DLQ Messages
```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders-dlq --from-beginning
```

### Test 3: Check Service Health
```powershell
docker-compose ps
```

---

## ⚡ Troubleshooting (30 seconds)

**Problem: Connection refused**
```powershell
docker-compose restart
```

**Problem: Module not found**
```powershell
pip install confluent-kafka[avro] requests
```

**Problem: Services not starting**
```powershell
docker-compose down -v
docker-compose up -d
```

---

## 📝 Demo Checklist

- [ ] Docker Desktop running
- [ ] Python dependencies installed
- [ ] Kafka services started (docker-compose up -d)
- [ ] Waited 60 seconds for initialization
- [ ] Consumer running in Terminal 1
- [ ] Producer running in Terminal 2
- [ ] Observed successful processing
- [ ] Observed retry logic
- [ ] Observed DLQ messages
- [ ] Checked final statistics

---

## 🎯 Key Features to Demonstrate

1. ✅ **Avro Serialization** - Binary format, Schema Registry
2. ✅ **Real-time Aggregation** - Running average updates
3. ✅ **Retry Logic** - Up to 3 attempts
4. ✅ **Dead Letter Queue** - Permanent failure handling
5. ✅ **Fault Tolerance** - System continues despite failures

---

**Ready to Demo! 🎉**

For full documentation, see `README.md` and `IMPLEMENTATION.md`
