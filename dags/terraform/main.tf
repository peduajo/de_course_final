terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.34.0"
    }
  }
}

provider "google" {
  credentials = file(var.gcp_credentials)
  project     = var.project_id
  region      = var.location
}


resource "google_storage_bucket" "demo-bucket" {
  name          = var.bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_storage_bucket" "tmp-bucket" {
  name          = var.tmp_bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = var.bq_dataset_name
  location = var.location
  delete_contents_on_destroy = true
}