#!/usr/bin/env python
# coding: utf-8

from pyspark.sql import SparkSession

from pyspark.sql.functions import split, trim, col, broadcast
from pyspark.sql import functions as F
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--year', type=int, help='Year parameter')
parser.add_argument('--month', type=int, help='Month parameter')
parser.add_argument('--bucket', type=str, help='Bucket input parameter')
parser.add_argument('--tmp_bucket', type=str, help='Bucket input parameter')
parser.add_argument('--bq_dataset', type=str, help='BQ dataset output parameter')

args = parser.parse_args()

spark = SparkSession.builder \
    .appName('dev') \
    .getOrCreate()


spark.conf.set('temporaryGcsBucket', args.tmp_bucket)
    
df_fact_flights = spark.read.csv(f"gs://{args.bucket}/raw/flights/{args.year}/{args.month:02d}.csv",
                                  header=True,
                                  inferSchema=True)


df_airlanes = spark.read.csv(f"gs://{args.bucket}/raw/airlines.csv",
                             header=True,
                             inferSchema=True)


df_airlanes = df_airlanes.withColumnRenamed("Code", "airlane_id")\
                         .withColumnRenamed("Description", "airlane_name")


df_airlanes = df_airlanes.alias('airlanes')
df_fact_flights = df_fact_flights.alias('flights')


df_fact_flights = df_fact_flights.join(broadcast(df_airlanes),
                                       col('flights.Reporting_Airline') == col('airlanes.airlane_id'),
                                       how='left')


df_airports = spark.read.csv(f"gs://{args.bucket}/raw/airports.csv",
                             header=True,
                             inferSchema=True)


df_airports = (df_airports
       .withColumnRenamed("Code", "airport_id") \
       .withColumn("Airport_name",
                   trim(split(col("Description"), ":").getItem(1)))   # trim quita espacios
)


df_fact_flights_joined = (df_fact_flights
          .join(
              broadcast(df_airports).alias('orig'),
              col("flights.OriginAirportID") == col("orig.airport_id"),
              "left")

          .join(
              broadcast(df_airports).alias("dest"), 
              col("flights.DestAirportID") == col("dest.airport_id"),
              "left")
)

df_fact_flights_joined = (df_fact_flights_joined
  .withColumn("Origin_AirportName", col("orig.Airport_name"))
  .withColumn("Dest_AirportName",  col("dest.Airport_name"))
  .drop('Airport_name')
  .drop('airport_id') 
  .drop('airlane_id')
  .drop('Description')
)

fact_flights_table = df_fact_flights_joined.select('Year','Quarter','Month',"FlightDate", "Flight_Number_Reporting_Airline",
                                                   "Tail_Number", "airlane_name", "Origin_AirportName", "Dest_AirportName", "DepDelayMinutes", "ArrDelayMinutes")


timeseries_agg_airlane = (
    fact_flights_table.groupBy(["FlightDate", "Year", "Month", "Quarter", "airlane_name"])
      .agg(
          F.count("*").alias("n_flights"),
          F.sum("ArrDelayMinutes").alias("total_mins_delay_arr"),
          F.sum("DepDelayMinutes").alias("total_mins_delay_dep")
      )
)

timeseries_agg_orig_airport = (
    fact_flights_table.groupBy(["FlightDate", "Year", "Month", "Quarter", "Origin_AirportName"])
      .agg(
          F.count("*").alias("n_flights"),
          F.sum("ArrDelayMinutes").alias("total_mins_delay_arr"),
          F.sum("DepDelayMinutes").alias("total_mins_delay_dep")
      )
)

timeseries_agg_orig_airport.show()

timeseries_agg_dest_airport = (
    fact_flights_table.groupBy(["FlightDate", "Year", "Month", "Quarter", "Dest_AirportName"])
      .agg(
          F.count("*").alias("n_flights"),
          F.sum("ArrDelayMinutes").alias("total_mins_delay_arr"),
          F.sum("DepDelayMinutes").alias("total_mins_delay_dep")
      )
)

timeseries_agg_airlane.show()

timeseries_agg_airlane.write.format('bigquery') \
    .option('table', f"{args.bq_dataset}.timeseries_agg_airlane") \
    .save(mode='append')

timeseries_agg_orig_airport.show()

timeseries_agg_orig_airport.write.format('bigquery') \
    .option('table', f"{args.bq_dataset}.timeseries_agg_orig_airport") \
    .save(mode='append')


timeseries_agg_dest_airport.show()

timeseries_agg_dest_airport.write.format('bigquery') \
    .option('table', f"{args.bq_dataset}.timeseries_agg_dest_airport") \
    .save(mode='append')

