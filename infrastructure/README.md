# Terraform Infrastructure for Shift Scheduler

This directory contains the Terraform infrastructure code for the Shift Scheduler application.

## Architecture

The infrastructure includes:
- **Resource Group**: Main container for all resources with CAF naming
- **Storage Account**: For job data and logs with blob containers
- **Container Registry**: For Docker images with environment-specific security
- **Log Analytics Workspace**: For centralized logging
- **Container Apps Environment**: For hosting applications

## Directory Structure

```
infrastructure/
├── main.tf              # Main infrastructure configuration
├── variables.tf         # Input variable definitions
├── outputs.tf          # Output value definitions
├── versions.tf         # Provider and Terraform version constraints
├── environments/       # Environment-specific configurations
│   ├── dev.tfvars     # Development environment
│   └── prod.tfvars    # Production environment
└── modules/           # Reusable Terraform modules
    ├── resource_group/    # Resource Group module
    ├── storage/          # Storage Account module
    ├── log_analytics/    # Log Analytics Workspace module
    ├── container_registry/ # Container Registry module
    └── container_apps/   # Container Apps Environment module
```

## Usage

### Prerequisites

1. Install Terraform >= 1.5
2. Install Azure CLI and authenticate: `az login`
3. Set up appropriate Azure subscription

### Development Environment

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan -var-file="environments/dev.tfvars"

# Apply deployment
terraform apply -var-file="environments/dev.tfvars"
```

### Production Environment

```bash
# Plan deployment
terraform plan -var-file="environments/prod.tfvars"

# Apply deployment
terraform apply -var-file="environments/prod.tfvars"
```

### Clean Up

```bash
# Destroy infrastructure
terraform destroy -var-file="environments/dev.tfvars"
```

## Environment Configurations

### Development (`dev.tfvars`)
- Basic Container Registry SKU
- Admin user enabled
- 7-day image retention
- 30-day log retention
- No zone redundancy

### Production (`prod.tfvars`)
- Standard Container Registry SKU
- Admin user disabled (security)
- 30-day image retention
- 90-day log retention
- Zone redundancy enabled

## Outputs

The infrastructure exports these key outputs:
- Resource group information
- Storage account details and connection strings
- Container registry login details
- Container Apps environment information
- Log Analytics workspace details


## Security Features

- HTTPS-only storage access
- TLS 1.2 minimum
- Private container access
- Environment-based security policies
- Admin user controls
- Vulnerability scanning (Standard/Premium SKUs)

## Backend Configuration

The project uses environment-specific backend configurations for Terraform state storage:

### Setup
1. Run `./setup-remote-state.sh` to create the Azure Storage Account
2. Use environment-specific backend files during initialization:

```bash
# Development environment
terraform init -backend-config=backends/dev.backend.hcl

# Production environment
terraform init -backend-config=backends/prod.backend.hcl
```

### State File Locations
- Development: `dev/shift-scheduler.tfstate`
- Production: `prod/shift-scheduler.tfstate`

This ensures complete isolation between environments.
