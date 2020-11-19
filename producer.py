from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'])
iid = 0

while True:
    producer.send('foo', str.encode(f"{time.time()}: message {iid} from producer!"))
    iid += 1
    time.sleep(1)