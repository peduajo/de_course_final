terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.34.0"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
}


resource "google_storage_bucket" "demo-bucket" {
  name          = var.bucket_name
  location      = var.region
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
  location      = var.region
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
  location = var.region
  delete_contents_on_destroy = true
}