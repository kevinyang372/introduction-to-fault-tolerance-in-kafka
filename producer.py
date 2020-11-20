from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'], acks="all")
iid = 0

while True:
    # message to deliver
    msg = f"{time.time()}: message {iid} from producer!"
    producer.send('foo', str.encode(msg))

    print(f"Produced {msg}")
    
    iid += 1
    time.sleep(1)