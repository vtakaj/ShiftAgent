# Shift Scheduler Infrastructure

Infrastructure as Code (IaC) for the Shift Scheduler application using Pulumi and Azure.

## 🏗️ Architecture

This infrastructure deploys the following Azure resources:

- **Resource Group**: Container for all resources
- **Storage Account**: For job data and application storage
- **Container Registry**: For Docker images
- **Container Apps Environment**: For hosting the application
- **Log Analytics Workspace**: For monitoring and logging

## 📁 Project Structure

```
infrastructure/
├── __main__.py              # Main Pulumi program
├── Pulumi.yaml             # Project configuration
├── Pulumi.dev.yaml         # Development stack config
├── Pulumi.prod.yaml        # Production stack config
├── requirements.txt        # Python dependencies
├── modules/                # Reusable infrastructure modules
│   ├── resource_group.py   # Resource group module
│   ├── storage.py          # Storage account module
│   ├── container_registry.py # Container registry module
│   └── container_apps.py   # Container Apps module
├── config/                 # Configuration helpers
│   └── common.py          # Common configuration
└── scripts/               # Deployment scripts
    ├── deploy-dev.sh      # Deploy development
    ├── deploy-prod.sh     # Deploy production
    └── destroy.sh         # Destroy resources
```

## 🚀 Getting Started

### Prerequisites

1. **Install Pulumi CLI**:
   ```bash
   brew install pulumi  # macOS
   # or visit https://www.pulumi.com/docs/install/
   ```

2. **Install Azure CLI**:
   ```bash
   brew install azure-cli  # macOS
   az login
   ```

3. **Install Python dependencies**:
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   ```

4. **Set up Pulumi backend**:
   ```bash
   # Option 1: Use Pulumi Cloud (recommended)
   pulumi login
   
   # Option 2: Use local backend
   pulumi login --local
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