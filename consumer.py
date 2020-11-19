from kafka import KafkaConsumer

consumer = KafkaConsumer('foo')
for msg in consumer:
    print(f"Consumed message from producer: {msg}")