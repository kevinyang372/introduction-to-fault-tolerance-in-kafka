from kafka import KafkaConsumer

consumer = KafkaConsumer('foo')
for msg in consumer:
    print(f"Consumed message from partition {msg.partition}: {msg.value.decode('utf-8')}")
