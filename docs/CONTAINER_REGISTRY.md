# Azure Container Registry Setup

This document provides comprehensive guidance for using the Azure Container Registry (ACR) with the Shift Scheduler application.

## 🏗️ Overview

The Azure Container Registry stores and manages Docker container images for the Shift Scheduler application. It provides:

- **Secure image storage** with authentication and access control
- **Image retention policies** to manage storage costs
- **Vulnerability scanning** for security compliance
- **Multi-environment support** (development, production)
- **Integration with CI/CD pipelines**

## 📋 Features

### Security Features
- **Environment-based access control** (admin users disabled in production)
- **Repository-scoped tokens** for fine-grained access
- **Private network access** in production environments
- **Encryption at rest** (Premium SKU)
- **Vulnerability scanning** (Standard/Premium SKUs)

### Management Features
- **Automatic image retention** policies
- **Zone redundancy** for high availability (Standard/Premium)
- **Build and push automation** scripts
- **Multi-platform support** (linux/amd64, linux/arm64)

## 🚀 Quick Start

### Prerequisites

1. **Azure CLI**: `brew install azure-cli && az login`
2. **Docker**: Install Docker Desktop or Docker Engine
3. **Terraform**: Infrastructure must be deployed first
4. **Access permissions**: Contributor or AcrPush role on the registry

### Build and Push Your First Image

```bash
# Navigate to infrastructure scripts
cd infrastructure/scripts

# Build and push to development registry
./build-and-push.sh -s dev -t latest

# Build and push to production registry
./build-and-push.sh -s prod -t v1.0.0
```

## 🛠️ Registry Configuration

### SKU Comparison

| Feature | Basic | Standard | Premium |
|---------|-------|----------|---------|
| Storage | 10 GB | 100 GB | 500 GB |
| Vulnerability Scanning | ❌ | ✅ | ✅ |
| Zone Redundancy | ❌ | ✅ | ✅ |
| Private Link | ❌ | ❌ | ✅ |
| Customer-managed keys | ❌ | ❌ | ✅ |
| Repository-scoped tokens | ❌ | ✅ | ✅ |
| Retention policies | ❌ | ✅ | ✅ |

### Environment-Specific Settings

#### Development Environment
- **SKU**: Basic (cost-optimized)
- **Admin user**: Enabled (for simplicity)
- **Public access**: Enabled
- **Retention**: 7 days
- **Vulnerability scanning**: Disabled (Basic SKU limitation)

#### Production Environment
- **SKU**: Standard or Premium
- **Admin user**: Disabled (security best practice)
- **Public access**: Disabled (private network only)
- **Retention**: 30 days
- **Vulnerability scanning**: Enabled
- **Zone redundancy**: Enabled

## 📦 Building Images

### Using the Build Script

```bash
# Basic build
./infrastructure/scripts/build-image.sh

# Build with specific tag
./infrastructure/scripts/build-image.sh -t v1.0.0

# Build for specific stack
./infrastructure/scripts/build-image.sh -s prod -t v1.0.0

# Build without cache
./infrastructure/scripts/build-image.sh --no-cache -t rebuild

# Build for multiple platforms
./infrastructure/scripts/build-image.sh -p linux/amd64,linux/arm64 -t multi-arch
```

### Build Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --image-name` | Image name | `shift-scheduler` |
| `-t, --tag` | Image tag | `latest` |
| `-f, --dockerfile` | Dockerfile path | `Dockerfile` |
| `-c, --context` | Build context | Project root |
| `-s, --stack` | Environment | Auto-detect |
| `-p, --platform` | Target platform | `linux/amd64` |
| `--no-cache` | Build without cache | false |
| `--quiet` | Suppress output | false |

### Manual Build

```bash
# Build locally
docker build -t shift-scheduler:latest .

# Build for production
docker build -t shift-scheduler:v1.0.0 --platform linux/amd64 .

# Multi-stage build optimization
docker build --target production -t shift-scheduler:v1.0.0 .
```

## 🚢 Pushing Images

### Using the Push Script

```bash
# Push to development registry
./infrastructure/scripts/push-image.sh -s dev -t latest

# Push to production registry
./infrastructure/scripts/push-image.sh -s prod -t v1.0.0

# Push to specific registry
./infrastructure/scripts/push-image.sh -r myregistry.azurecr.io -t v1.0.0

# Dry run (show what would be pushed)
./infrastructure/scripts/push-image.sh --dry-run -s prod -t v1.0.0
```

### Push Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --image-name` | Local image name | `shift-scheduler` |
| `-t, --tag` | Image tag | `latest` |
| `-s, --stack` | Environment | Auto-detect |
| `-r, --registry` | Registry URL | From stack |
| `--force-login` | Force re-login | false |
| `--dry-run` | Show actions only | false |

### Manual Push

```bash
# Get registry details from Terraform
cd infrastructure
REGISTRY=$(terraform output -raw container_registry_login_server)

# Login to registry
az acr login --name $REGISTRY

# Tag and push
docker tag shift-scheduler:latest $REGISTRY/shift-scheduler:latest
docker push $REGISTRY/shift-scheduler:latest
```

## 🔐 Authentication

### Authentication Methods

1. **Azure CLI** (Development - Recommended)
   ```bash
   az login
   az acr login --name <registry-name>
   ```

2. **Service Principal** (CI/CD - Recommended)
   ```bash
   export AZURE_CLIENT_ID="<client-id>"
   export AZURE_CLIENT_SECRET="<client-secret>"
   export AZURE_TENANT_ID="<tenant-id>"

   az login --service-principal --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
   az acr login --name <registry-name>
   ```

3. **Admin Credentials** (Development Only)
   ```bash
   # Get credentials from Terraform
   USERNAME=$(terraform output -raw container_registry_admin_username)
   PASSWORD=$(terraform output -raw container_registry_admin_password)

   echo $PASSWORD | docker login <registry-url> --username $USERNAME --password-stdin
   ```

4. **Repository-Scoped Tokens** (Fine-grained Access)
   ```bash
   # Create scope map (via Terraform or Azure CLI)
   az acr scope-map create --name read-only --registry <registry-name> --repository repo1 content/read

   # Create token
   az acr token create --name ci-token --registry <registry-name> --scope-map read-only
   ```

### Setting Up CI/CD Authentication

#### GitHub Actions
```yaml
env:
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}

steps:
  - name: Login to Azure
    run: |
      az login --service-principal \
        --username $AZURE_CLIENT_ID \
        --password $AZURE_CLIENT_SECRET \
        --tenant $AZURE_TENANT_ID

  - name: Build and Push
    run: |
      ./infrastructure/scripts/build-and-push.sh -s prod -t ${{ github.sha }}
```

#### Azure DevOps
```yaml
variables:
  - group: azure-credentials

steps:
  - task: AzureCLI@2
    inputs:
      azureSubscription: 'Azure Connection'
      scriptType: 'bash'
      scriptLocation: 'inlineScript'
      inlineScript: |
        ./infrastructure/scripts/build-and-push.sh -s prod -t $(Build.SourceVersion)
```

## 🛡️ Security Best Practices

### Access Control

1. **Use Service Principals for CI/CD**
   - Create dedicated service principals for automated systems
   - Grant minimal required permissions (AcrPush for pushing, AcrPull for pulling)
   - Rotate credentials regularly

2. **Disable Admin Users in Production**
   - Admin users provide full access to the registry
   - Use repository-scoped tokens or managed identities instead
   - Only enable admin users in development environments

3. **Use Private Networks in Production**
   - Configure private endpoints for production registries
   - Restrict public network access
   - Use Azure Virtual Networks for secure communication

### Image Security

1. **Enable Vulnerability Scanning**
   - Automatically enabled on Standard/Premium SKUs
   - Review scan results regularly
   - Block deployments of vulnerable images

2. **Use Multi-stage Builds**
   - Minimize final image size
   - Exclude build tools and dependencies from production images
   - Use distroless or minimal base images

3. **Sign Images** (Advanced)
   ```bash
   # Using Docker Content Trust
   export DOCKER_CONTENT_TRUST=1
   docker push $REGISTRY/shift-scheduler:signed
   ```

## 🔄 Image Retention Policies

### Automatic Cleanup

Retention policies automatically delete old images based on:
- **Age**: Delete images older than N days
- **Count**: Keep only the latest N images per repository

### Current Settings

- **Development**: 7 days retention
- **Production**: 30 days retention
- **Basic SKU**: No retention policies (manual cleanup required)

### Manual Cleanup

```bash
# List repositories
az acr repository list --name <registry-name>

# List tags for a repository
az acr repository show-tags --name <registry-name> --repository shift-scheduler

# Delete specific tag
az acr repository delete --name <registry-name> --image shift-scheduler:old-tag

# Delete all tags older than 30 days
az acr repository show-tags --name <registry-name> --repository shift-scheduler \
  --orderby time_desc --query "[?timestamp < '2024-01-01'].name" -o tsv | \
  xargs -I {} az acr repository delete --name <registry-name> --image shift-scheduler:{} --yes
```

## 📊 Monitoring and Logging

### Registry Metrics

Monitor these key metrics:
- **Storage usage**: Track repository sizes
- **Pull/push operations**: Monitor usage patterns
- **Authentication failures**: Security monitoring
- **Vulnerability scan results**: Security compliance

### Azure Monitor Integration

```bash
# Enable diagnostic settings
az monitor diagnostic-settings create \
  --name acr-diagnostics \
  --resource <registry-id> \
  --logs '[{"category":"ContainerRegistryRepositoryEvents","enabled":true}]' \
  --workspace <log-analytics-workspace-id>
```

### Query Examples

```kusto
# Recent push operations
ContainerRegistryRepositoryEvents
| where OperationName == "Push"
| where TimeGenerated > ago(24h)
| project TimeGenerated, Repository, Tag, Actor

# Failed authentication attempts
ContainerRegistryLoginEvents
| where Status != "Success"
| where TimeGenerated > ago(24h)
| project TimeGenerated, ClientIP, UserAgent, ErrorMessage
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptoms**: `unauthorized: authentication required`

**Solutions**:
```bash
# Check if logged in
az account show

# Re-login
az login
az acr login --name <registry-name>

# Check credentials
docker system info | grep -A5 "Registry Mirrors"
```

#### 2. Image Not Found

**Symptoms**: `repository does not exist or may require 'docker login'`

**Solutions**:
```bash
# List repositories
az acr repository list --name <registry-name>

# Check exact image name and tag
az acr repository show-tags --name <registry-name> --repository shift-scheduler

# Verify registry URL
cd infrastructure && terraform output -raw container_registry_login_server
```

#### 3. Push Failures

**Symptoms**: `denied: requested access to the resource is denied`

**Solutions**:
```bash
# Check permissions
az role assignment list --assignee $(az account show --query user.name -o tsv) --all

# Verify registry exists
az acr show --name <registry-name>

# Check quota limits
az acr show-usage --name <registry-name>
```

#### 4. Network Connectivity

**Symptoms**: `dial tcp: lookup <registry>.azurecr.io: no such host`

**Solutions**:
```bash
# Test connectivity
nslookup <registry>.azurecr.io
telnet <registry>.azurecr.io 443

# Check private endpoint configuration (production)
az network private-endpoint list --query "[?privateLinkServiceConnections[0].privateLinkServiceId contains('<registry-id>')]"
```

### Debug Commands

```bash
# Registry information
az acr show --name <registry-name> --output table

# Recent operations
az acr repository show-logs --name <registry-name> --image shift-scheduler:latest

# Webhook status
az acr webhook list --registry <registry-name> --output table

# Replication status (Premium SKU)
az acr replication list --registry <registry-name> --output table
```

## 🔮 Advanced Features

### Multi-Region Replication (Premium SKU)

```bash
# Add replication to additional regions
az acr replication create \
  --registry <registry-name> \
  --location westus2

# List replications
az acr replication list --registry <registry-name> --output table
```

### Webhooks for CI/CD Integration

```bash
# Create webhook for deployments
az acr webhook create \
  --registry <registry-name> \
  --name deployment-webhook \
  --uri https://your-ci-cd-endpoint.com/webhook \
  --actions push \
  --scope shift-scheduler:latest
```

### Content Trust and Image Signing

```bash
# Enable content trust
export DOCKER_CONTENT_TRUST=1

# Generate signing keys
docker trust key generate developer

# Sign and push
docker trust sign <registry>/shift-scheduler:v1.0.0
```

## 📚 Additional Resources

### Azure Documentation
- [Azure Container Registry Documentation](https://docs.microsoft.com/en-us/azure/container-registry/)
- [ACR Best Practices](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-best-practices)
- [ACR Authentication](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-authentication)

### Docker Documentation
- [Docker Build Reference](https://docs.docker.com/engine/reference/commandline/build/)
- [Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Content Trust](https://docs.docker.com/engine/security/trust/)

### Security Resources
- [Container Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/container-security)
- [Azure Security Baseline for ACR](https://docs.microsoft.com/en-us/security/benchmark/azure/baselines/container-registry-security-baseline)

## 🤝 Contributing

When making changes to the registry configuration:

1. **Test in development first**: Always test changes in the dev stack
2. **Update documentation**: Keep this guide current with any changes
3. **Follow security practices**: Don't commit credentials or sensitive information
4. **Test build/push scripts**: Ensure automation works correctly
5. **Monitor after deployment**: Check metrics and logs for issues

## 📞 Support

For issues with the Azure Container Registry setup:

1. **Check this documentation** for troubleshooting steps
2. **Review Terraform outputs** for configuration details
3. **Check Azure portal** for registry status and metrics
4. **Contact the infrastructure team** for access or configuration issues
