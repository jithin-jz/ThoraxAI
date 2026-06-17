# ThoraxAI GCP Backend Deployment Guide (using Terraform)

This folder contains the Terraform configuration to deploy the **ThoraxAI FastAPI Backend** to Google Cloud Platform (GCP) using serverless infrastructure (**Google Cloud Run**).

---

## 1. Prerequisites

Before deploying, make sure you have the following installed on your system:
1. [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install)
2. [Terraform CLI](https://developer.hashicorp.com/terraform/downloads)
3. [Docker Desktop](https://www.docker.com/products/docker-desktop/)

You will also need:
- A **GCP Project** (with billing enabled).
- A **MongoDB Atlas** account (free tier works perfectly).
- A **Redis Cache** instance (Upstash or RedisLabs free tiers work perfectly).
- A **Hugging Face** account and token.
- A **Groq API** key.

---

## 2. GCP Project Setup

1. Login to your Google Cloud account via the CLI:
   ```bash
   gcloud auth login
   ```
2. Configure your project ID:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```
3. Set up Application Default Credentials for Terraform to authenticate:
   ```bash
   gcloud auth application-default login
   ```

---

## 3. Configure Variables

1. Duplicate the `terraform.tfvars.example` file and rename it to `terraform.tfvars`:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
2. Open `terraform.tfvars` and fill in the values:
   - `project_id`: Your GCP Project ID.
   - `database_url`: The connection URI for your MongoDB Atlas cluster.
   - `redis_url`: The connection URI for your Redis instance (e.g. Upstash).
   - API keys and other environment variables.

---

## 4. Initialization & Provisioning

1. Initialize Terraform (this downloads the Google provider plugin):
   ```bash
   terraform init
   ```
2. Generate an execution plan to verify the resources Terraform will create:
   ```bash
   terraform plan
   ```
3. Apply the plan to create the infrastructure in GCP:
   ```bash
   terraform apply
   ```
   *Note: Type `yes` when prompted to confirm.*

Once the apply step completes, Terraform will output:
- `repository_url`: The URL of the GCP Artifact Registry Docker repository.
- `backend_url`: The endpoint URL where your FastAPI application will live.

---

## 5. Build and Push the Docker Container

The Cloud Run service will initially fail or wait because the container image does not exist yet in your GCP Artifact Registry. Follow these steps to build the FastAPI app and push it:

1. Configure Docker to authenticate with GCP Artifact Registry:
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```
   *(Change `us-central1` if you deployed to a different region)*

2. Navigate back to the `backend` folder:
   ```bash
   cd ../backend
   ```

3. Build the Docker image (tagging it for your GCP Artifact Registry):
   ```bash
   docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/thoraxai-backend-repo/backend:latest .
   ```
   *(Replace `YOUR_PROJECT_ID` with your actual GCP Project ID)*

4. Push the Docker image to GCP:
   ```bash
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/thoraxai-backend-repo/backend:latest
   ```

5. Force Cloud Run to deploy the newly pushed container:
   ```bash
   gcloud run deploy thoraxai-backend --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/thoraxai-backend-repo/backend:latest --region us-central1
   ```

---

## 6. How to Clean Up

To avoid incurring any charges after learning/testing, you can easily destroy all resources with a single command:
```bash
terraform destroy
```
Type `yes` when prompted. This will clean up the Cloud Run service, Secret Manager secrets, and Artifact Registry repositories.
