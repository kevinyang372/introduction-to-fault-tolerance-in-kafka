from kafka import KafkaProducer
import random
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'], acks="all")

iid = 0
available_keys = [b"foo_1", b"foo_2", b"foo_3", b"foo_4", b"foo_5"]

while True:
    use_key = random.choice(available_keys)  # Choose a random key.

    # Message to deliver.
    msg = f"{time.time()}: message {iid} with key {use_key.decode('utf-8')} from producer!"
    confirmation = producer.send('foo', value=str.encode(msg), key=use_key)

    try:
        confirmation.get()
        print(f"Successfully produced {msg}!")
    except Exception:
        print(f"Failed to deliver {msg}")

    iid += 1
    time.sleep(1)
