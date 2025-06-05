variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "Default region for resources"
  default     = "europe-west1"
}

variable "bucket_name" {
  type        = string
  description = "Main GCS bucket for data"
}

variable "tmp_bucket_name" {
  type        = string
  description = "Temporary / staging bucket"
}

variable "bq_dataset_name" {
  type        = string
  description = "BigQuery dataset name"
}
