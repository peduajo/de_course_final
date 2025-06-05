terraform {
  backend "gcs" {
    bucket = "terraform-state-shared"          # crea este bucket una vez
    prefix = "composer/${terraform.workspace}" # dev → …/dev/…, prod → …/prod/…
  }
}
