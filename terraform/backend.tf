terraform {
  backend "gcs" {
    bucket = "terraform-state-shared"   # bucket donde guardas el state
    prefix = "composer"                 # carpeta común
  }
}