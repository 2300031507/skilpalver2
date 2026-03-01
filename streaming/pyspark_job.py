"""
PySpark Structured Streaming job that:
  1. Reads attendance, LMS, and coding events from Kafka
  2. Aggregates per (university_id, student_id, course_id)
  3. Writes merged feature vectors to MongoDB student_features

Designed for 1 lakh+ students by:
  - Grouping by university_id first (partition-friendly)
  - Using watermarks to bound late-data memory
  - Writing with foreachBatch for upsert semantics
"""

from pyspark.sql import SparkSession, DataFrame, functions as F
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType, IntegerType
from backend.settings import KafkaTopics, MongoCollections


# ── Spark session ───────────────────────────────────────────

def create_spark(app_name: str = "StudentFeaturePipeline") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.mongodb.output.uri", "mongodb://localhost:27017/academic_feature_store")
        .config("spark.sql.shuffle.partitions", "64")   # tune for cluster size
        .getOrCreate()
    )


def read_kafka_stream(spark: SparkSession, topic: str):
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 50_000)          # back-pressure cap
        .load()
    )


# ── Schemas ─────────────────────────────────────────────────

ATTENDANCE_SCHEMA = StructType([
    StructField("university_id", StringType()),
    StructField("student_id", StringType()),
    StructField("course_id", StringType()),
    StructField("present", BooleanType()),
    StructField("date", TimestampType()),
])

LMS_SCHEMA = StructType([
    StructField("university_id", StringType()),
    StructField("student_id", StringType()),
    StructField("course_id", StringType()),
    StructField("action", StringType()),
    StructField("duration_seconds", IntegerType()),
    StructField("timestamp", TimestampType()),
])

CODING_SCHEMA = StructType([
    StructField("university_id", StringType()),
    StructField("student_id", StringType()),
    StructField("course_id", StringType()),
    StructField("platform", StringType()),
    StructField("problems_attempted", IntegerType()),
    StructField("problems_solved", IntegerType()),
    StructField("daily_active_days", IntegerType()),
    StructField("timestamp", TimestampType()),
])


# ── Parse helpers ───────────────────────────────────────────

def parse_json(df: DataFrame, schema: StructType) -> DataFrame:
    return (
        df.selectExpr("CAST(value AS STRING) as json")
        .select(F.from_json("json", schema).alias("data"))
        .select("data.*")
    )


# ── Feature computation ────────────────────────────────────

GROUP_KEYS = ["university_id", "student_id", "course_id"]


def compute_attendance_features(df: DataFrame) -> DataFrame:
    return (
        df.withWatermark("date", "1 day")
        .groupBy(*GROUP_KEYS)
        .agg(
            (F.sum(F.when(F.col("present"), 1).otherwise(0)) / F.count("*"))
            .alias("attendance_percent"),
            F.count("*").alias("total_sessions"),
            F.max("date").alias("last_attendance_at"),
        )
    )


def compute_lms_features(df: DataFrame) -> DataFrame:
    return (
        df.withWatermark("timestamp", "1 day")
        .groupBy(*GROUP_KEYS)
        .agg(
            F.sum("duration_seconds").alias("total_lms_seconds"),
            F.countDistinct("action").alias("distinct_lms_actions"),
            F.count("*").alias("total_lms_events"),
            F.max("timestamp").alias("last_lms_at"),
        )
    )


def compute_coding_features(df: DataFrame) -> DataFrame:
    return (
        df.withWatermark("timestamp", "1 day")
        .groupBy(*GROUP_KEYS)
        .agg(
            F.sum("problems_solved").alias("total_problems_solved"),
            F.sum("problems_attempted").alias("total_problems_attempted"),
            F.max("daily_active_days").alias("max_streak_days"),
            F.countDistinct("platform").alias("platforms_used"),
            F.max("timestamp").alias("last_coding_at"),
        )
    )


# ── MongoDB upsert writer ──────────────────────────────────

def upsert_to_mongo(batch_df: DataFrame, batch_id: int):
    """foreachBatch sink — does upsert into student_features."""
    if batch_df.isEmpty():
        return
    (
        batch_df.write.format("mongodb")
        .mode("append")
        .option("collection", MongoCollections.STUDENT_FEATURES)
        .option("replaceDocument", "true")
        .save()
    )


def write_features(features_df: DataFrame, checkpoint: str):
    return (
        features_df.writeStream
        .outputMode("update")
        .foreachBatch(upsert_to_mongo)
        .option("checkpointLocation", checkpoint)
        .trigger(processingTime="30 seconds")
        .start()
    )


# ── Main pipeline ──────────────────────────────────────────

def main():
    spark = create_spark()

    # Attendance stream
    att_raw = read_kafka_stream(spark, KafkaTopics.ATTENDANCE)
    att_parsed = parse_json(att_raw, ATTENDANCE_SCHEMA)
    att_features = compute_attendance_features(att_parsed)
    att_query = write_features(att_features, "/tmp/checkpoints/attendance_features")

    # LMS stream
    lms_raw = read_kafka_stream(spark, KafkaTopics.LMS_ACTIVITY)
    lms_parsed = parse_json(lms_raw, LMS_SCHEMA)
    lms_features = compute_lms_features(lms_parsed)
    lms_query = write_features(lms_features, "/tmp/checkpoints/lms_features")

    # Coding stream
    cod_raw = read_kafka_stream(spark, KafkaTopics.CODING_ACTIVITY)
    cod_parsed = parse_json(cod_raw, CODING_SCHEMA)
    cod_features = compute_coding_features(cod_parsed)
    cod_query = write_features(cod_features, "/tmp/checkpoints/coding_features")

    # Wait for all streams
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()

