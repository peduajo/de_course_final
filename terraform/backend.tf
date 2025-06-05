terraform {
  backend "gcs" {
    bucket = "terraform-state-shared-53421532"   # bucket donde guardas el state
    prefix = "composer"                 # carpeta común
  }
}