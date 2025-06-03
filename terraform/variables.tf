variable "location" {
    description = "Project location in GCP"
    default = "europe-west1"
}

variable "region" {
    description = "Project region in GCP"
    default = "europe-west4-a"  
}

variable "gcp_credentials" {
    description = "Path to GCP credentials file"
    default = "/home/eduardo/airflow/gcp_credentials.json"  
}

variable "service_account_email" {
    description = "Service account email"
    default = "final-orchestator@taxy-rides-ny-459209.iam.gserviceaccount.com"  
}

variable "project_id" {
    description = "Project ID in GCP"
}

variable "bucket_name" {
    description = "Bucket name in GCP"
}

variable "tmp_bucket_name" {
    description = "TMP Bucket name in GCP"
}

variable "bq_dataset_name" {
    description = "Dataset name in BigQuery"
}