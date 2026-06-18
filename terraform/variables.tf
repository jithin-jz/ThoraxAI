variable "project_id" {
  description = "The GCP Project ID where resources will be deployed"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources in"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "thoraxai-backend"
}

# Backend Environment Variables (Stored in Secret Manager)
variable "database_url" {
  description = "The MongoDB connection string (e.g. MongoDB Atlas)"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "The master MongoDB database name"
  type        = string
  default     = "ai_xray_master"
}

variable "debug" {
  description = "Enable backend debug logging"
  type        = bool
  default     = false
}

variable "redis_url" {
  description = "The Redis connection string (e.g. Upstash Redis)"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "The secret key for JWT token generation"
  type        = string
  sensitive   = true
}

variable "base_domain" {
  description = "The base domain for multi-tenant routing (e.g. localhost or yourdomain.com)"
  type        = string
  default     = "localhost"
}

variable "tenant_url_scheme" {
  description = "Scheme used when building tenant URLs"
  type        = string
  default     = "http"
}

variable "tenant_url_port" {
  description = "Port used when building tenant URLs"
  type        = string
  default     = "5173"
}

variable "hf_token" {
  description = "Hugging Face API Token for model/dataset access"
  type        = string
  sensitive   = true
}

variable "hf_dataset_repo" {
  description = "Hugging Face dataset repository"
  type        = string
  default     = "jithinjz/xray-chest-pneumonia"
}

variable "hf_model_repo" {
  description = "Hugging Face model repository"
  type        = string
  default     = "jithinjz/xray-models"
}

variable "groq_api_key" {
  description = "Groq LLM API Key"
  type        = string
  sensitive   = true
}

variable "smtp_host" {
  description = "SMTP host used for OTP and password reset email"
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP port used for OTP and password reset email"
  type        = number
  default     = 587
}

variable "smtp_user" {
  description = "SMTP username or sender email used for OTP delivery"
  type        = string
  sensitive   = true
}

variable "smtp_password" {
  description = "SMTP app password used for OTP delivery"
  type        = string
  sensitive   = true
}

variable "groq_model" {
  description = "Groq LLM model name"
  type        = string
  default     = "llama-3.3-70b-versatile"
}
