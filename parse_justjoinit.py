# %%
from pyspark.sql import SparkSession
spark = SparkSession.builder \
                    .appName("skillz-justjoinit") \
                    .getOrCreate()


import pyspark.sql.functions as f
from pyspark.sql.types import DecimalType
df = spark.read.json("data/json")
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
