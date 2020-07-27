# Sensor Log Data Pipeline

## Introduction
The goal of this project is to create a real-time data pipeline to process sensor data from bike trips in order to serve a daily 
leaderboard application in near real time. Users can use this application to see where they rank amongst other cyclists for metrics 
like average speed, average pace, distance traveled and ride duration on a given day. The pipeline also provides a place for data 
scientists and analyst to study metrics and trends of bike trips.
## Data Set
Collection of workout logs from users of EndoMondo. Data includes sequential sensor data from a users bike trip such as longitude, latitude, 
altitude, timestamp, heart rate as well user id, trip id, sport type and gender.

Sample record:<br>
{<br>
	"userId": 10921915,<br>
	"id": 396826535,<br>
	"sport": "bike",<br>
	"gender": "male",<br>
	"longitude": [24.64977040886879, 24.65014273300767, 24.650910682976246, 24.650668865069747, ...],<br>
	"latitude": [60.173348765820265, 60.173239801079035, 60.17298021353781, 60.172477969899774, ...],<br>
	"timestamp": [1408898746, 1408898754, 1408898765, 1408898778, ...],<br>
	"altitude": [41.6, 40.6, 40.6, 38.4, ...],<br>
	"heart_rate": [100, 111, 120, 119, ...]<br>
}
## Data Pipeline
![image](https://github.com/jrowland22/sensor-data-pipeline/blob/master/images/pipeline_arch.png)
### Kafka
Used to ingest data from the json file every second to simulate real-time behavior. All data is stored into 
one topic and is later consumed by the Spark application.
### Spark Structured Streaming
Processes sequential data into usable metrics for leaderboard. Many records of the data set were missing the “distance” and “speed” 
attributes that are supposed to be provided by the tracking device (Fitbit, Apple Watch, etc). Since each row included a sequential 
record of the users latitude and longitude at 3-15 seconds intervals, the haversine formula was used to compute the distance between two 
geographic points. The speed between two points could then be computed by dividing the distance by the time interval between the points. Multiple other useful attributes related to a trip are added such as: average speed, max speed, average heart rate, max heart rate, total distance, duration and average pace.
After transformations and aggregations are applied, our data is sent to Cassandra in the following format:
![image](https://github.com/jrowland22/sensor-data-pipeline/blob/master/images/spark_sample.png)
### Cassandra
Stores processed data from Spark and serves the flask application. In order to have efficient queries, each leaderboard has a corresponding 
table to query. Tables are partitioned by date and have clustering order based on the leaderboard metric they store. For example, 
the “leaders_by_distance” table uses "distance" as the clustering key to sort data in descending order.
### Flask
Leaderboards are displayed and updated every 10 seconds. Users can switch between leaderboards and also see archived leaderboards from previous dates.<br>
<img src = "https://github.com/jrowland22/sensor-data-pipeline/blob/master/images/demo.gif" width = "750" height = "363"/>

## Running
1. Install python packages
```
pip install kafka-python
```
2. Start cassandra
```
apache-cassandra-3.11.6/bin/cassandra
```
3. Start flask
```
python3 flaskr/leaderboard.py
```
4. Start zookeeper
```
kafka_2.12-2.4.0/bin/zookeeper-server-start.sh kafka_2.12-2.4.0/config/zookeeper.properties
```
5. Start kafka
```
kafka_2.12-2.4.0/bin/kafka-server-start.sh kafka_2.12-2.4.0/config/server.properties
```
6. Create topic in kafka
```
kafka_2.12-2.4.0/bin/kafka-topics.sh kafka-topics --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic sensor
```
7. Start spark and include spark-kafka and spark-cassandra-connector
```
bin/spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.0,datastax:spark-cassandra-connector:2.4.0-s_2.11 \
spark/sensor_stream.py
```
8. Start kafka producer
```
python3 kafka/producer.py
```
