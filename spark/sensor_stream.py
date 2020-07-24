from pyspark import SparkContext, SparkConf
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from pyspark.sql import SparkSession
from pyspark.sql.types import * 
from pyspark.sql import functions as F
import os
import math


# kafka configuration
kafka_topic = "sensor"
kafka_cluster = "<private_ip>:9092"

# cassandra configuration
cassandra_host = "<private_ip>"
cass_keyspace = "rides"
cass_tables = ["leaders_by_duration","leaders_by_distance","leaders_by_avgpace","leaders_by_avgspeed"]


# saves micro batches to different cassandra tables using foreachBatch operation
def save_to_cassandra(df,epoch_id):
    for leaderboard_table in cass_tables:
        df.write \
            .format("org.apache.spark.sql.cassandra")\
            .mode("append")\
            .options(table=leaderboard_table, keyspace=cass_keyspace)\
            .save()

# converts seconds to time format HH:mm:ss
def conv_from_sec(s):
    h = s // (60*60)
    s %= (60*60)
    m = s // 60
    s %= 60
    ans = '%02i:%02i:%02i' % (h,m,s)
    return ans

#register udf
conv_sec_udf = F.udf(conv_from_sec, StringType())

if __name__ == "__main__":
    spark = SparkSession \
        .builder \
        .master("local[*]") \
        .appName("FitRecDS") \
        .config('spark.cassandra.connection.host', cassandra_host) \
        .getOrCreate()
    spark.sparkContext.setLogLevel('WARN')

    dsraw = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_cluster) \
        .option("subscribe", kafka_topic) \
        .option("startingOffsets", "earliest") \
        .load() \
        .selectExpr("CAST(value AS STRING)")

    schema = StructType()\
        .add("speed", ArrayType(FloatType()))\
        .add("altitude", ArrayType(FloatType()))\
        .add("gender", StringType())\
        .add("heart_rate", ArrayType(IntegerType()))\
        .add("id", IntegerType())\
        .add("url", StringType())\
        .add("userId", IntegerType())\
        .add("timestamp", ArrayType(IntegerType()))\
        .add("longitude", ArrayType(FloatType()))\
        .add("latitude", ArrayType(FloatType()))\
        .add("sport", StringType())

    # fitting data to schema
    df = dsraw.select(F.from_json("value",schema).alias("data")).select("data.*")

    # creates offset and adds columns latitude2, longitude2 and time2 to each row which is required to calculate speed and distance
    d = df.withColumn("arr_size", F.size("latitude"))\
        .withColumn("lat2", F.expr("slice(latitude,1,arr_size-1)"))\
        .withColumn("long2", F.expr("slice(longitude,1,arr_size-1)"))\
        .withColumn("time2", F.expr("slice(timestamp,1,arr_size-1)"))\
        .withColumn("null_col", F.array([F.lit(None)]))\
        .withColumn("lat2", F.concat(F.col("null_col"),F.col("lat2")))\
        .withColumn("long2", F.concat(F.col("null_col"),F.col("long2")))\
        .withColumn("time2", F.concat(F.col("null_col"),F.col("time2")))

    # explodes all array columns
    d1 = d.withColumn("new", F.arrays_zip("heart_rate","timestamp","latitude","longitude","lat2","long2","time2"))\
            .withColumn("new", F.explode("new"))\
            .select("userId","id",
                    F.col("new.heart_rate").alias("heart_rate"),
                    F.col("new.timestamp").alias("timestamp"),
                    F.col("new.latitude").alias("lat"),
                    F.col("new.longitude").alias("long"),
                    F.col("new.lat2").alias("lat2"),
                    F.col("new.long2").alias("long2"),
                    F.col("new.time2").alias("time2"))

    # haversine formula, calculates distance and speed between two points
    d2 = d1.withColumn("distance", 3956 *(2 * F.asin(F.sqrt(F.sin((F.radians("lat") - F.radians("lat2"))/2)**2 
                                    + F.cos(F.radians("lat")) * F.cos(F.radians("lat2")) * F.sin((F.radians("long")
                                    - F.radians("long2"))/2)**2))))\
           .withColumn("speed", F.col("distance")/((F.col("timestamp") - F.col("time2"))/3600)) 

    d2 = d2.fillna({"speed":"0"})

    # aggregations that compute metrics related to an individual bike trip
    query = d2.groupBy("id","userid").agg(
                F.round(F.mean("speed"),2).alias("avgspeed"),
                F.round(F.max("speed"),2).alias("max_speed"),
                F.round(F.mean("heart_rate")).cast("integer").alias("avg_heart_rate"),
                F.max("heart_rate").alias("max_heart_rate"),
                F.round(F.sum("distance"),2).alias("distance"),
                conv_sec_udf(F.last("timestamp") - F.first("timestamp")).alias("duration"),
                conv_sec_udf((F.last("timestamp") - F.first("timestamp"))/F.sum("distance")).alias("avgpace"),
                F.current_date().alias("leaderboard_date"))

    # filter out trips less than 5 miles and greater than 100 miles
    query_filter = query.filter((query["distance"] >= 5)&(query["distance"] < 100))
    
    # processes new records every 10 seconds and writes micro batches to cassandra 
    query_filter.writeStream\
        .trigger(processingTime = '10 seconds')\
        .outputMode('complete')\
        .foreachBatch(save_to_cassandra)\
        .start()\
        .awaitTermination()
    
    


