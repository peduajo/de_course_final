import requests
from google.cloud import storage
from io import BytesIO
import zipfile
import os

import multiprocessing

client = storage.Client()

bucket_name = os.getenv("TF_VAR_bucket_name")
bucket = client.bucket(bucket_name)

def upload_big_table(year, month):
    url = f"https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
    # Descarga el ZIP
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error al descargar: {response.status_code}")

    # Extrae el .csv del ZIP en memoria
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        for file_name in z.namelist():
            if file_name.endswith(".csv"):
                with z.open(file_name) as f:
                    blob = bucket.blob(f"raw/flights/{year}/{month:02d}.csv")
                    blob.upload_from_file(f, rewind=True)
                    print(f"Subido: gs://{bucket_name}/raw/{year}/{month:02d}.csv")

def upload_lookup_table(url, bucket_path):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error al descargar: {response.status_code}")

    blob = bucket.blob(bucket_path)
    blob.upload_from_file(BytesIO(response.content), rewind=True)
    print(f"Subido: gs://{bucket_name}/{bucket_path}")

def worker(year, month):
    upload_big_table(year, month)

def upload_data(mode="all", year=None, month=None):
    if mode =="all":
        with multiprocessing.Pool(processes=16) as pool:
            pool.starmap(worker, [(year, month) for year in range(2020, 2024) for month in range(1, 13)])

        url_lookup_table_airlane = "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_haVdhR_PNeeVRef"
        url_lookup_table_airport = "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVecbeg_VQ"

        upload_lookup_table(url_lookup_table_airlane, "raw/airlines.csv")
        upload_lookup_table(url_lookup_table_airport, "raw/airports.csv")
    
    else:
        print(f"Subiendo mes {year}-{month}")
        upload_big_table(year, int(month))