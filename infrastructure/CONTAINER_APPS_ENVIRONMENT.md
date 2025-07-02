# Azure Container Apps Environment - Implementation Guide

This document describes the Azure Container Apps environment implementation for ShiftAgent, including logging, monitoring, and optional VNet integration.

## Overview

The Container Apps environment provides a fully managed serverless platform for deploying containerized applications with built-in monitoring, logging, and optional network isolation.

## Architecture Components

### Core Infrastructure
- **Log Analytics Workspace**: Centralized logging and monitoring
- **Application Insights**: Application performance monitoring and telemetry
- **Container Apps Environment**: Managed compute environment for containers
- **Container Registry**: Secure container image storage

### Optional Components
- **Virtual Network**: Network isolation and security
- **Private DNS Zone**: Custom domain resolution for private endpoints
- **Network Security Groups**: Traffic filtering and security rules

## Features Implemented

### ✅ Log Analytics Workspace
- **Purpose**: Centralized log collection and analysis
- **Retention**: Configurable (30 days dev, 90 days prod)
- **Integration**: Automatic integration with Container Apps Environment
- **Cost**: Pay-per-GB ingested

### ✅ Container Apps Environment
- **Purpose**: Managed platform for containerized applications
- **Features**:
  - Auto-scaling based on HTTP traffic and CPU/memory
  - Zero-scale capabilities
  - Built-in load balancing
  - Support for multiple revisions
  - Blue-green deployments

### ✅ Application Insights
- **Purpose**: Application performance monitoring (APM)
- **Features**:
  - Request tracking and performance metrics
  - Exception monitoring and alerting
  - Smart detection for anomaly detection
  - Custom monitoring workbooks
  - Sampling configuration for cost optimization

### ✅ Enhanced Monitoring & Logging
- **Diagnostic Settings**: Comprehensive logging for Container Apps
- **Log Categories**:
  - `ContainerAppConsoleLogs`: Application console output
  - `ContainerAppSystemLogs`: System-level events
- **Metrics**: All metrics with configurable retention
- **Workbooks**: Pre-configured monitoring dashboards

### ✅ Optional VNet Integration
- **Purpose**: Network isolation and security
- **Benefits**:
  - Private IP addresses for Container Apps
  - Network traffic control via NSGs
  - Integration with existing network infrastructure
  - Support for hybrid connectivity

### ✅ Workload Profiles
- **Purpose**: Different compute configurations for various workloads
- **Types**: Consumption (default) and Dedicated
- **Use Cases**: 
  - Consumption: Cost-effective, auto-scaling
  - Dedicated: Predictable performance, isolation

## Environment Configurations

### Development Environment
```hcl
# Basic setup without VNet integration
enable_vnet_integration = false
zone_redundant = false
log_retention_days = 30
application_insights_retention_days = 90
diagnostic_retention_days = 30
```

### Production Environment
```hcl
# Enhanced setup with VNet integration and high availability
enable_vnet_integration = true
zone_redundant = true
log_retention_days = 90
application_insights_retention_days = 180
diagnostic_retention_days = 90

# VNet configuration
vnet_address_space = ["10.1.0.0/16"]
container_apps_subnet_address_prefixes = ["10.1.1.0/24"]
enable_private_dns = true
internal_load_balancer_enabled = true

# Workload profiles for scaling
container_apps_workload_profiles = [
  {
    name                  = "general-purpose"
    workload_profile_type = "D4"
    minimum_count         = 1
    maximum_count         = 10
  }
]
```

## Security Features

### Network Security
- **NSG Rules**: HTTP/HTTPS traffic allowed, customizable
- **Private DNS**: Custom domain resolution for private communication
- **Internal Load Balancer**: Private endpoint access when VNet integrated

### Access Control
- **Azure RBAC**: Role-based access control for resources
- **Managed Identity**: Secure authentication without credentials
- **Private Endpoints**: Secure communication within VNet

### Monitoring Security
- **Smart Detection**: Automatic anomaly detection and alerting
- **Log Retention**: Configurable retention policies
- **Sensitive Data**: Secure handling of connection strings and keys

## Cost Optimization

### Application Insights
- **Sampling**: Configurable telemetry sampling (75% in prod)
- **Retention**: Environment-specific retention policies
- **Smart Detection**: Focus on critical alerts only

### Container Apps
- **Consumption Plan**: Pay-per-use pricing in dev
- **Dedicated Plans**: Predictable costs in production
- **Auto-scaling**: Automatic scaling to zero when idle

### Log Analytics
- **Retention**: Shorter retention in dev (30 days vs 90 days)
- **Log Categories**: Only essential log categories enabled
- **Metric Retention**: Configurable retention policies

## Deployment

### Prerequisites
- Azure CLI authenticated (`az login`)
- Terraform >= 1.5
- Appropriate Azure permissions

### Commands
```bash
# Development deployment
cd infrastructure
terraform init -backend-config=backends/dev.backend.hcl
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"

# Production deployment
terraform init -backend-config=backends/prod.backend.hcl
terraform plan -var-file="environments/prod.tfvars"
terraform apply -var-file="environments/prod.tfvars"

# Using deployment scripts
./scripts/deploy-dev.sh
./scripts/deploy-prod.sh
```

### Validation
```bash
# Validate configuration
./scripts/validate.sh

# Check deployment
terraform output
az containerapp env list --query "[].{Name:name,ResourceGroup:resourceGroup,Location:location}"
```

## Monitoring and Alerting

### Available Metrics
- **Request Metrics**: Count, duration, success rate
- **Resource Metrics**: CPU, memory, replica count
- **Network Metrics**: Ingress/egress traffic
- **Container Metrics**: Restart count, exit codes

### Monitoring Workbook
Pre-configured workbook includes:
- Request count and response time trends
- Exception tracking and analysis
- Resource utilization charts
- Container health status

### Smart Detection Rules
- **Failure Anomalies**: Automatic detection of unusual error rates
- **Performance Degradation**: Detection of slow response times
- **Custom Alerts**: Configurable alert rules

## Troubleshooting

### Common Issues
1. **VNet Integration**: Ensure subnet delegation is properly configured
2. **Zone Redundancy**: Only available with VNet integration
3. **Workload Profiles**: Requires sufficient quota in the region
4. **DNS Resolution**: Verify private DNS configuration for custom domains

### Diagnostic Tools
```bash
# Check Container Apps environment status
az containerapp env show --name <env-name> --resource-group <rg-name>

# View logs
az containerapp logs show --name <app-name> --resource-group <rg-name>

# Check networking
az network vnet subnet show --name <subnet-name> --vnet-name <vnet-name> --resource-group <rg-name>
```

### Log Queries (Kusto/KQL)
```kusto
// Container App Console Logs
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| order by TimeGenerated desc

// Exception Analysis
AppExceptions
| where TimeGenerated > ago(24h)
| summarize count() by Type, bin(TimeGenerated, 1h)
| order by TimeGenerated desc

// Performance Metrics
AppRequests
| where TimeGenerated > ago(1h)
| summarize avg(DurationMs), count() by bin(TimeGenerated, 5m)
| order by TimeGenerated desc
```

## Next Steps

### Phase 6 Considerations
- **Container App Deployment**: Deploy ShiftAgent API containers
- **Custom Domains**: Configure custom domain names
- **SSL Certificates**: Set up managed SSL certificates
- **CI/CD Integration**: Connect with GitHub Actions
- **Health Probes**: Configure application health checks

### Advanced Features
- **Dapr Integration**: Microservices communication
- **KEDA Scaling**: Custom auto-scaling rules
- **Service Mesh**: Advanced traffic management
- **GitOps**: Infrastructure as Code automation

## Support

For issues or questions:
1. Check the [Azure Container Apps documentation](https://docs.microsoft.com/azure/container-apps/)
2. Review Terraform plan output for validation errors
3. Use `./scripts/validate.sh` for configuration validation
4. Check Azure portal for resource status and logs