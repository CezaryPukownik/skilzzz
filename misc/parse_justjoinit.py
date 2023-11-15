# %%
import datetime
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
from pyspark.sql.types import DecimalType, IntegerType, TimestampType
import datetime

df = spark.read.json("s3a://skilzzz/sources/justjoinit/offers/jsonl/year=2023/month=11/day=14/231114130114.jsonl")

cast_listed_at = f.udf(lambda x: datetime.datetime.strptime(x, '%y%m%d%H%M%S'), TimestampType())
listing = df.select(
    f.md5(
        f.concat_ws('|', 
            f.col('offer_id'), 
            f.col('listed_at')
        )
    ).alias('listing_id'),
    f.col('offer_id'),
    f.col('offer_index').cast(IntegerType()),
    f.col('title'),
    f.col('company'),
    f.col('city'),
    f.col('experience'),
    f.col('operating_mode'),
    f.col('type_of_work'),
    f.col('skills'),
    f.col('salary_types'),
    cast_listed_at(f.col('listed_at')).alias('listed_at')
).filter('experience="Senior"').filter(f.col('title').contains('Data Engineer'))

#%%

skills_listing = ( 
    listing
    .select(
        f.col('listing_id'),
        f.col('offer_id'),
        f.explode('skills').alias('skills'),
        f.col('listed_at')
    )
    .select(
        f.md5(
            f.concat_ws('|', 
                f.col('listing_id'), 
                f.col('skills.skill_name')
            )
        ).alias('skill_listing_id'),
        f.col('listing_id'),
        f.col('offer_id'),
        f.col('skills.skill_name').alias('skill_name'),
        f.col('skills.skill_seniorty').alias('skill_seniority'), # typo!!! senior_I_ty
        f.col('listed_at')
    )
)

skills_listing\
    .groupBy('skill_name').agg(f.count('skill_name').alias('skills_count'))\
    .orderBy(f.col('skills_count').desc()).show()

# %%
print(listing.schema)
# %%
