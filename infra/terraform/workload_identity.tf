# infrastructure/workload_identity.tf
# ======================================================================================
# ==          ULTRA-SECURE WORKLOAD IDENTITY FEDERATION (GCP/AWS/AZURE)           ==
# ======================================================================================
# Strategy: "Keyless Authentication" for Cross-Platform Synergy
# Eliminated static secrets in favor of OIDC tokens exchanged for short-lived access credentials.

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# --------------------------------------------------------------------------------------
# 1. GITHUB ACTIONS IDENTITY POOL
# --------------------------------------------------------------------------------------
# Allows GitHub Actions to impersonate Service Accounts without JSON keys.

resource "google_iam_workload_identity_pool" "github_pool" {
  provider                  = google
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions OIDC federation"
  disabled                  = false
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  provider                           = google
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  description                        = "OIDC provider for GitHub Actions"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# --------------------------------------------------------------------------------------
# 2. GITLAB CI IDENTITY POOL
# --------------------------------------------------------------------------------------
# Allows GitLab CI runners to impersonate Service Accounts without variables.

resource "google_iam_workload_identity_pool" "gitlab_pool" {
  provider                  = google
  workload_identity_pool_id = "gitlab-ci-pool"
  display_name              = "GitLab CI Pool"
  description               = "Identity pool for GitLab CI OIDC federation"
  disabled                  = false
}

resource "google_iam_workload_identity_pool_provider" "gitlab_provider" {
  provider                           = google
  workload_identity_pool_id          = google_iam_workload_identity_pool.gitlab_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "gitlab-provider"
  display_name                       = "GitLab Provider"
  description                        = "OIDC provider for GitLab CI"

  attribute_mapping = {
    "google.subject"           = "assertion.sub"
    "attribute.project_path"   = "assertion.project_path"
    "attribute.project_id"     = "assertion.project_id"
    "attribute.ref"            = "assertion.ref"
  }

  oidc {
    issuer_uri        = "https://gitlab.com"
    allowed_audiences = ["https://gitlab.com"]
  }
}

# --------------------------------------------------------------------------------------
# 3. SERVICE ACCOUNT BINDINGS (The "Connective Tissue")
# --------------------------------------------------------------------------------------

resource "google_service_account" "repo_syncer" {
  account_id   = "repo-syncer-bot"
  display_name = "Universal Repo Sync Bot"
}

# Allow GitHub Actions (specific repo) to impersonate this SA
resource "google_service_account_iam_member" "github_impersonation" {
  service_account_id = google_service_account.repo_syncer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/cogniforge/reality-kernel-v3"
}

# Allow GitLab CI (specific project) to impersonate this SA
resource "google_service_account_iam_member" "gitlab_impersonation" {
  service_account_id = google_service_account.repo_syncer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.gitlab_pool.name}/attribute.project_path/cogniforge/reality-kernel-v3"
}
