terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ── Enable GCP APIs ────────────────────────────────────────────────────────
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",                  # Cloud Run
    "artifactregistry.googleapis.com",     # Artifact Registry
    "secretmanager.googleapis.com",        # Secret Manager
    "iam.googleapis.com",                  # Identity & Access Management
    "storage.googleapis.com",              # Cloud Storage
    "cloudresourcemanager.googleapis.com", # Cloud Resource Manager
    "firebase.googleapis.com",             # Firebase Management API
    "firebasehosting.googleapis.com"       # Firebase Hosting API
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# ── Artifact Registry ──────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "backend_repo" {
  depends_on    = [google_project_service.apis]
  location      = var.region
  repository_id = "${var.app_name}-repo"
  description   = "Docker repository for ThoraxAI Backend"
  format        = "DOCKER"
}

# ── Secret Manager (Store Sensitive Environment Variables) ──────────────────
# Helper local map to iterate over sensitive secrets
locals {
  secrets = {
    "DATABASE_URL"   = var.database_url
    "REDIS_URL"      = var.redis_url
    "JWT_SECRET_KEY" = var.jwt_secret_key
    "HF_TOKEN"       = var.hf_token
    "GROQ_API_KEY"   = var.groq_api_key
    "SMTP_USER"      = var.smtp_user
    "SMTP_PASSWORD"  = var.smtp_password
  }
}

resource "google_secret_manager_secret" "secret" {
  for_each   = local.secrets
  depends_on = [google_project_service.apis]
  secret_id  = "${var.app_name}-${lower(each.key)}"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secret_version" {
  for_each    = local.secrets
  secret      = google_secret_manager_secret.secret[each.key].id
  secret_data = each.value
}

# ── IAM (Cloud Run Service Account) ─────────────────────────────────────────
resource "google_service_account" "cloud_run_sa" {
  depends_on   = [google_project_service.apis]
  account_id   = "${var.app_name}-run-sa"
  display_name = "Service Account for ThoraxAI Cloud Run Backend"
}

# Grant Cloud Run service account permission to access secrets
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  for_each  = local.secrets
  secret_id = google_secret_manager_secret.secret[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# ── Cloud Run Service ───────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = var.app_name
  location = var.region
  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.secret_version,
    google_secret_manager_secret_iam_member.secret_accessor
  ]

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    service_account       = google_service_account.cloud_run_sa.email
    timeout               = "300s"

    # PyTorch analysis is memory-heavy and should not run many requests per instance.
    max_instance_request_concurrency = 1

    containers {
      # We reference a bootstrap image or the registry image.
      # For initial deployment before push, we can use a standard public placeholder image (like alpine or nginx)
      # or default to the artifact registry path which you will push to.
      # Here we use the Artifact Registry path. Note: You must build and push your image to run it.
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/backend:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      ports {
        container_port = 8000
      }

      # Non-sensitive Env Variables (Passed directly)
      env {
        name  = "DB_NAME"
        value = var.db_name
      }
      env {
        name  = "DEBUG"
        value = tostring(var.debug)
      }
      env {
        name  = "BASE_DOMAIN"
        value = var.base_domain
      }
      env {
        name  = "TENANT_URL_SCHEME"
        value = var.tenant_url_scheme
      }
      env {
        name  = "TENANT_URL_PORT"
        value = var.tenant_url_port
      }
      env {
        name  = "ORIGIN"
        value = "https://${var.base_domain}"
      }
      env {
        name  = "RP_ID"
        value = var.base_domain
      }
      env {
        name  = "HF_DATASET_REPO"
        value = var.hf_dataset_repo
      }
      env {
        name  = "HF_MODEL_REPO"
        value = var.hf_model_repo
      }
      env {
        name  = "GROQ_MODEL"
        value = var.groq_model
      }
      env {
        name  = "SMTP_HOST"
        value = var.smtp_host
      }
      env {
        name  = "SMTP_PORT"
        value = tostring(var.smtp_port)
      }

      # Sensitive Env Variables (Pulled from Secret Manager)
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["DATABASE_URL"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "REDIS_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["REDIS_URL"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["JWT_SECRET_KEY"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "HF_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["HF_TOKEN"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GROQ_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["GROQ_API_KEY"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SMTP_USER"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["SMTP_USER"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SMTP_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret["SMTP_PASSWORD"].secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "uploads-volume"
        mount_path = "/app/uploads"
      }
    }

    volumes {
      name = "uploads-volume"
      gcs {
        bucket    = google_storage_bucket.uploads.name
        read_only = false
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# ── IAM (Allow Unauthenticated Public Traffic to Cloud Run) ────────────────
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Storage Bucket for Scan Uploads ────────────────────────────────────────
resource "google_storage_bucket" "uploads" {
  name          = "${var.project_id}-scans-uploads"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "gcs_accessor" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# ── Firebase Project Setup ──────────────────────────────────────────────────
resource "google_firebase_project" "default" {
  provider   = google-beta
  project    = var.project_id
  depends_on = [google_project_service.apis]
}

resource "google_firebase_hosting_site" "default" {
  provider   = google-beta
  project    = var.project_id
  site_id    = var.project_id
  depends_on = [google_firebase_project.default]
}
