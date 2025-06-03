from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitJobOperator,
    DataprocDeleteClusterOperator
)
from datetime import timedelta
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from utils.upload_data import upload_data

# 1. Configuración inicial (.env)
dag_folder = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(dag_folder, os.pardir))
dotenv_path = os.path.join(project_root, ".env")
if not load_dotenv(dotenv_path=dotenv_path):
    raise RuntimeError(f".env file not found: {dotenv_path}")

BUCKET_NAME = os.getenv("TF_VAR_bucket_name")           # Ej: "airplanes-bucket-dev"
PROJECT_ID  = os.getenv("TF_VAR_project_id")            # Ej: "taxy-rides-ny-459209"
REGION      = "europe-west1"
SPARK_GCS_PATH = os.getenv("GCP_PATH_SPARK_JOB_SCRIPT") # Ej: "jobs/incremental_transform.py"
LOCAL_SPARK_SCRIPT = os.path.join(project_root, "scripts", "incremental_transform.py")

# Nombre base del clúster efímero
CLUSTER_NAME = "incremental-spark-cluster-{{ ds_nodash }}"

# 2. Argumentos por defecto del DAG
default_args = {
    "start_date": datetime(2024, 1, 1),           # Desde cuándo validará runs mensuales
    "retries": 1,                        # Reintentar 1 vez en caso de fallos
    "retry_delay": timedelta(minutes=5), # Esperar 5 minutos entre reintentos
}

# 3. Definición del DAG incremental (cada mes)
with DAG(
    dag_id="incremental_monthly_load",
    default_args=default_args,
    schedule_interval="@monthly",  # Corre al inicio de cada mes
    catchup=False,                 # No backfill automático
    tags=["incremental", "monthly"]
) as dag:
    
    download_and_upload_data = PythonOperator(
        task_id="download_and_upload_data",
        python_callable=upload_data,
        op_kwargs={"mode":"increment",
                   "year": "{{ data_interval_start.year }}",
                   "month": "{{ data_interval_start.month }}"},
    )

    # 4. Subir el script PySpark incremental a GCS
    upload_inc_script = LocalFilesystemToGCSOperator(
        task_id="upload_incremental_script",
        src=LOCAL_SPARK_SCRIPT,
        dst=SPARK_GCS_PATH,
        bucket=BUCKET_NAME,
        gcp_conn_id="google_cloud_default",
    )

    # 5. Crear clúster de Dataproc (efímero) con config mínima
    create_cluster = DataprocCreateClusterOperator(
        task_id="create_dataproc_cluster",
        project_id=PROJECT_ID,
        cluster_name=CLUSTER_NAME,
        region=REGION,
        cluster_config={
            "master_config": {
                "num_instances": 1,
                "machine_type_uri": "n1-standard-2",
                "disk_config": {"boot_disk_size_gb": 100},
            },
            "worker_config": {
                "num_instances": 2,
                "machine_type_uri": "n1-standard-4",
                "disk_config": {"boot_disk_size_gb": 100},
            },
            # Suponiendo subred default esté lista; si no, agrega gce_cluster_config
        },
        delete_on_error=True,
        use_if_exists=True,
        gcp_conn_id="google_cloud_default",
    )

    # 6. Definir configuración del job PySpark usando data_interval_start
    #    Aquí pasamos año y mes como argumentos.
    PYSPARK_JOB = {
        "reference": {"project_id": PROJECT_ID},
        "placement": {"cluster_name": CLUSTER_NAME},
        "pyspark_job": {
            "main_python_file_uri": f"gs://{BUCKET_NAME}/{SPARK_GCS_PATH}",
            "args": [
                "--year", "{{ data_interval_start.year }}",
                "--month", "{{ data_interval_start.month }}"
            ]
        },
    }

    # 7. Enviar job PySpark al clúster
    submit_incremental_job = DataprocSubmitJobOperator(
        task_id="submit_incremental_job",
        project_id=PROJECT_ID,
        region=REGION,
        job=PYSPARK_JOB,
        gcp_conn_id="google_cloud_default",
        # deferrable=True  # Descomenta si tu versión de Airflow lo soporta
    )

    # 8. Eliminar clúster al completar (éxito o error)
    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_dataproc_cluster",
        project_id=PROJECT_ID,
        cluster_name=CLUSTER_NAME,
        region=REGION,
        gcp_conn_id="google_cloud_default",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # 9. Flujo de dependencias
    download_and_upload_data >> upload_inc_script \
        >> create_cluster \
        >> submit_incremental_job \
        >> delete_cluster
