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

#resource "google_dataproc_cluster" "spark_cluster" {
#  name    = "spark-cluster"
#  region  = var.location          # usa solo la región, p. ej. "europe-west4"
#  project = var.project_id

#  cluster_config {

#    master_config {
#      num_instances = 1
#      machine_type  = "n1-standard-2"
#      disk_config   { boot_disk_size_gb = 100 }
#    }

#    worker_config {
#      num_instances = 2
#      machine_type  = "n1-standard-4"
#      disk_config   { boot_disk_size_gb = 100 }
#    }

#    gce_cluster_config {
#      service_account = var.service_account_email
#    }

#    endpoint_config {
#        enable_http_port_access = "true"
#    }

#    software_config {
#      image_version       = "2.2-debian12"
#      optional_components = ["JUPYTER"]

      # ← AQUÍ usa override_properties, no properties
#      override_properties = {
#        "spark:spark.executor.memory" = "2g"
#      }
#    }
#  }
#}

resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = var.bq_dataset_name
  location = var.location
  delete_contents_on_destroy = true
}