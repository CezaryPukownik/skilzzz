# %%
import os
aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']


from pyspark.sql import SparkSession
from pyspark.conf import SparkConf


# Create a Spark session with your AWS Credentials

conf = (
    SparkConf()
    .setAppName("MY_APP") # replace with your desired name
    .set("spark.jars.packages", "io.delta:delta-core_2.12:2.3.0,org.apache.hadoop:hadoop-aws:3.3.2")
    .set("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .set("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .set("spark.hadoop.fs.s3a.access.key", aws_access_key_id)
    .set("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key)
    .set("spark.sql.shuffle.partitions", "4") # default is 200 partitions which is too many for local
    .setMaster("local[*]") # replace the * with your desired number of cores. * for use all.
)

spark = SparkSession.builder.config(conf=conf).getOrCreate()

#%%

#%%#%%#%%

import pyspark.sql.functions as f
from pyspark.sql.types import DecimalType
df = spark.read.json("s3a://stxnext-sandbox-cp/justjoinit/json/")
offers = df.dropDuplicates(['slug']).select(
    f.col('slug'),
    f.col('title'),
    f.col('experienceLevel').alias('experience_level'),
    f.col("companyName").alias("company_name"),
    f.col("city"),
    f.col("employmentTypes").alias("employment_types"),
    f.col("requiredSkills").alias("required_skills"),
    f.col("workplaceType").alias('workplace_type'),
    f.col("publishedAt").alias("published_at")
)

#%%
(
   offers
    .select(
        '*',
        f.explode('required_skills').alias('skill')
    )
    .groupBy('skill').agg(
        f.sum(f.when(f.col('experience_level')=="senior", f.lit(1)).otherwise(f.lit(0))).alias('nb_senior_orders'),
        f.sum(f.when(f.col('experience_level')=="mid", f.lit(1)).otherwise(f.lit(0))).alias('nb_mid_orders'),
        f.sum(f.when(f.col('experience_level')=="junior", f.lit(1)).otherwise(f.lit(0))).alias('nb_junior_orders'),
        f.count('slug').alias('nb_total_orders'),
    )
    .orderBy(f.col('nb_senior_orders').desc())
).show()
# %%
