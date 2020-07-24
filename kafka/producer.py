from kafka import KafkaProducer
import time
import json

file = 'data/b2.json'

producer = KafkaProducer(
    bootstrap_servers=['<private_ip>:9092'],
    value_serializer=lambda m: json.dumps(m).encode('ascii'))

with open(file) as j:
    json_data = json.load(j)
    for i in range(0,len(json_data)):
        producer.send('sensor',json_data[i])
        time.sleep(1)

