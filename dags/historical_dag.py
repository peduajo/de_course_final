from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitJobOperator,
    DataprocDeleteClusterOperator,
)
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.utils.trigger_rule import TriggerRule

from datetime import timedelta
from utils.upload_data import upload_data
import os 
from dotenv import load_dotenv

# 1. Configuración inicial (.env)
dag_folder = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(dag_folder, os.pardir))
dotenv_path = os.path.join(project_root, ".env")

#opcional ya que pasaremos variables de entorno a composer si lo subimos
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

default_args = {
    "start_date": days_ago(1),
}

BUCKET_NAME = os.getenv("TF_VAR_bucket_name")
PROJECT_ID = os.getenv("TF_VAR_project_id")
REGION      = os.getenv("REGION")
SPARK_SCRIPT_GCS = os.getenv("GCP_PATH_SPARK_JOB_SCRIPT")
SUBNETWORK_URI = f"projects/{PROJECT_ID}/regions/{REGION}/subnetworks/default"
CLUSTER_NAME = "spark-cluster-{{ ds_nodash }}"

IN_COMPOSER = os.getenv("GCS_BUCKET") is not None

if IN_COMPOSER:
    DAG_BUCKET = os.environ["GCS_BUCKET"]            # dado por Composer
    MAIN_PY_URI = f"gs://{DAG_BUCKET}/dags/jobs/transform.py"
else:
    MAIN_PY_URI = os.path.join(project_root, "dags", "jobs", "transform.py")

PYSPARK_JOB = {
    "reference": { "project_id": PROJECT_ID},
    "placement": { "cluster_name": CLUSTER_NAME},
    "pyspark_job": {
        "main_python_file_uri": os.path.join("gs://", BUCKET_NAME, SPARK_SCRIPT_GCS),
        "args": [
                "--bucket", BUCKET_NAME,
                "--tmp_bucket", os.getenv("TF_VAR_tmp_bucket_name"),
                "--bq_dataset", os.getenv("TF_VAR_bq_dataset_name")
            ]
    },
}

with DAG(
    dag_id="historical_full_load_2020_2023",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:
    create_cluster = DataprocCreateClusterOperator(
        task_id="create_ephemeral_cluster",
        project_id=PROJECT_ID,
        cluster_name=CLUSTER_NAME,
        region=REGION,
        cluster_config={
            "master_config": {"num_instances": 1,
                              "machine_type_uri": "n1-standard-2",
                              "disk_config": {"boot_disk_size_gb": 100}},
            "worker_config": {"num_instances": 4,
                              "machine_type_uri": "n1-standard-4",
                              "disk_config": {"boot_disk_size_gb": 100}},
            "gce_cluster_config": {
                "subnetwork_uri": SUBNETWORK_URI,
            }
        },
        delete_on_error=True,
        use_if_exists=True,
        gcp_conn_id="google_cloud_default",
    )

    download_and_upload_data = PythonOperator(
        task_id="download_and_upload_data",
        python_callable=upload_data,
    )

    upload_script_job_task = LocalFilesystemToGCSOperator(
        task_id="upload_script_job",
        src=MAIN_PY_URI,         # Ruta absoluta calculada
        dst=SPARK_SCRIPT_GCS,   # En el bucket, crea 'data/mi_archivo.csv'
        bucket=BUCKET_NAME,
        gcp_conn_id="google_cloud_default"
    )

    submit_pyspark = DataprocSubmitJobOperator(
        task_id="submit_pyspark_to_dataproc",
        project_id=PROJECT_ID,
        region=REGION,
        job=PYSPARK_JOB,
    )

    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_ephemeral_cluster",
        project_id=PROJECT_ID,
        cluster_name=CLUSTER_NAME,
        region=REGION,
        gcp_conn_id="google_cloud_default",
        trigger_rule=TriggerRule.ALL_DONE,
    )
    
    create_cluster >> download_and_upload_data >> upload_script_job_task >> submit_pyspark >> delete_cluster