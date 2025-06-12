# Infrastructure Deployment

This directory contains Pulumi Infrastructure as Code for deploying the Shift Scheduler application to Azure.

## Setup Required Secrets

### GitHub Repository Secrets

1. **PULUMI_ACCESS_TOKEN**: Pulumi access token for state management
   - Go to [Pulumi Console](https://app.pulumi.com/) → Settings → Access Tokens
   - Create new token and add to GitHub repository secrets

2. **AZURE_CREDENTIALS**: Azure service principal credentials
   ```bash
   # Create service principal
   az ad sp create-for-rbac --name "shift-scheduler-github" \
     --role contributor \
     --scopes /subscriptions/{subscription-id} \
     --sdk-auth
   ```
   - Copy the JSON output and add to GitHub repository secrets

### Environment Configuration

Create environment protection rules in GitHub:
- **development**: Auto-deploy from main branch
- **production**: Require manual approval

## Deployment Workflows

### Infrastructure Deployment (`.github/workflows/infrastructure.yml`)

**Automatic:**
- **PR**: Runs `pulumi preview` and comments on PR
- **Main branch push**: Deploys to dev environment

**Manual:**
```
Actions → Infrastructure Deployment → Run workflow
- Stack: dev/prod
- Action: preview/up/destroy
```

### Application Deployment (`.github/workflows/application.yml`)

**Automatic:**
- **Main branch push**: 
  1. Runs tests and linting
  2. Builds multi-arch Docker image
  3. Pushes to GitHub Container Registry
  4. Deploys to dev environment

**Manual:**
```
Actions → Application Deployment → Run workflow
- Environment: dev/prod
```

## Resource Naming Convention

Following Microsoft Cloud Adoption Framework (CAF):

| Resource Type | Naming Pattern | Example |
|---------------|----------------|---------|
| Resource Group | `rg-{org}-{project}-{workload}-{env}-{location}-{instance}` | `rg-org-shift-scheduler-core-dev-eastus-001` |
| Storage Account | `st{org}{project}{env}{location}{instance}` | `storgshiftschedulerdeveus001` |
| Container Registry | `cr{org}{project}{env}{location}{instance}` | `crorgshiftschedulerdeveus001` |
| Container Apps Env | `cae-{org}-{project}-{workload}-{env}-{location}-{instance}` | `cae-org-shift-scheduler-core-dev-eastus-001` |
| Log Analytics | `log-{org}-{project}-{workload}-{env}-{location}-{instance}` | `log-org-shift-scheduler-core-dev-eastus-001` |

## Local Development (without pip)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Pulumi dependencies
cd infrastructure
uv sync --frozen

# Preview changes
uv run pulumi preview --stack dev

# Deploy changes  
uv run pulumi up --stack dev
```

### 🏃‍♂️ Quick Deployment

#### Development Environment

```bash
cd infrastructure

# Initialize development stack
pulumi stack init dev
pulumi stack select dev

# Deploy infrastructure
pulumi up
```

#### Production Environment

```bash
cd infrastructure

# Initialize production stack
pulumi stack init prod
pulumi stack select prod

# Deploy infrastructure
pulumi up
```

## 🔧 Configuration

### Stack Configuration

Each stack has its own configuration file:

- `Pulumi.dev.yaml`: Development configuration
- `Pulumi.prod.yaml`: Production configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `azure-native:location` | Azure region | East US |
| `environment` | Environment name | dev |
| `instance_count` | Number of instances | 1 |
| `sku_size` | Resource SKU size | Basic |

### Setting Configuration Values

```bash
# Set Azure location
pulumi config set azure-native:location "West US 2"

# Set environment-specific values
pulumi config set environment production
pulumi config set instance_count 3
pulumi config set sku_size Standard
```

## 📊 Outputs

After deployment, the following outputs are available:

```bash
# View all outputs
pulumi stack output

# Get specific output
pulumi stack output resource_group_name
pulumi stack output container_registry_login_server
```

Key outputs:
- `resource_group_name`: Name of the resource group
- `storage_account_name`: Name of the storage account
- `container_registry_name`: Name of the container registry
- `container_registry_login_server`: Registry login server URL
- `container_apps_environment_name`: Container Apps environment name

## 🛠️ Management Commands

### Stack Management

```bash
# List all stacks
pulumi stack ls

# Switch between stacks
pulumi stack select dev
pulumi stack select prod

# View stack outputs
pulumi stack output

# View stack configuration
pulumi config

# Preview changes
pulumi preview

# Deploy changes
pulumi up

# Rollback to previous deployment
pulumi stack history
pulumi cancel  # if deployment is in progress
```

### Resource Management

```bash
# View resources in current stack
pulumi stack --show-urns

# Export stack state
pulumi stack export > stack-backup.json

# Import stack state
pulumi stack import < stack-backup.json

# Refresh stack state
pulumi refresh
```

## 🔒 Security Best Practices

1. **Use Managed Identities**: Enable managed identities for container apps
2. **Network Security**: Configure virtual networks and subnets
3. **Access Control**: Use Azure RBAC for resource access
4. **Secrets Management**: Use Azure Key Vault for secrets
5. **Monitoring**: Enable Azure Monitor and alerts

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   az login
   pulumi config set azure-native:clientId <client-id>
   pulumi config set azure-native:clientSecret <client-secret> --secret
   pulumi config set azure-native:tenantId <tenant-id>
   ```

2. **Resource Naming Conflicts**:
   - Storage account names must be globally unique
   - Container registry names must be globally unique
   - Use stack name in resource naming

3. **Permission Issues**:
   - Ensure Azure subscription has required permissions
   - Check RBAC assignments for the deployment principal

### Debugging

```bash
# Enable verbose logging
pulumi up --verbose

# View detailed logs
pulumi logs

# Check stack status
pulumi stack --show-urns
```

## 🧹 Cleanup

To destroy all resources:

```bash
# Destroy current stack resources
pulumi destroy

# Remove stack completely
pulumi stack rm <stack-name>
```

## 📚 Additional Resources

- [Pulumi Azure Native Provider](https://www.pulumi.com/registry/packages/azure-native/)
- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Pulumi Best Practices](https://www.pulumi.com/docs/guides/best-practices/)