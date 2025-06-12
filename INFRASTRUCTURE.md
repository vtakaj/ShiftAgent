# Infrastructure Documentation

## 🏗️ Infrastructure as Code with Pulumi

The Shift Scheduler project uses Pulumi for Infrastructure as Code (IaC) to manage Azure resources. This provides version-controlled, reproducible infrastructure deployments.

## 📁 Infrastructure Structure

```
infrastructure/
├── __main__.py              # Main Pulumi program
├── Pulumi.yaml             # Project configuration  
├── Pulumi.dev.yaml         # Development stack config
├── Pulumi.prod.yaml        # Production stack config
├── requirements.txt        # Python dependencies
├── README.md              # Infrastructure documentation
├── modules/               # Reusable infrastructure modules
│   ├── resource_group.py  # Resource group management
│   ├── storage.py         # Storage account for job data
│   ├── container_registry.py # Docker image registry
│   └── container_apps.py  # Application hosting environment
├── config/               # Configuration helpers
│   └── common.py        # Shared configuration
└── scripts/             # Deployment automation
    ├── deploy-dev.sh    # Development deployment
    ├── deploy-prod.sh   # Production deployment
    └── destroy.sh       # Resource cleanup
```

## 🏭 Azure Resources

The infrastructure creates the following Azure resources:

### Core Resources
- **Resource Group**: Container for all related resources
- **Storage Account**: For job data, logs, and application storage
- **Container Registry**: For Docker image storage and distribution
- **Container Apps Environment**: For hosting the application containers
- **Log Analytics Workspace**: For monitoring and logging

### Security & Networking
- **Managed Identities**: For secure service-to-service authentication
- **Private Endpoints**: For secure network access (production)
- **Virtual Network**: For network isolation (production)

## 🚀 Getting Started

### Prerequisites

1. **Azure CLI**: `brew install azure-cli && az login`
2. **Pulumi CLI**: `brew install pulumi`
3. **Python 3.11+**: For running the infrastructure code

### Quick Deployment

#### Development Environment
```bash
cd infrastructure
./scripts/deploy-dev.sh
```

#### Production Environment
```bash
cd infrastructure
./scripts/deploy-prod.sh
```

### Manual Deployment

```bash
cd infrastructure

# Install dependencies
pip install -r requirements.txt

# Initialize stack
pulumi stack init dev
pulumi stack select dev

# Configure environment
pulumi config set azure-native:location "East US"

# Deploy
pulumi up
```

## 🔧 Configuration

### Stack Configuration

Each environment has its own configuration:

**Development (Pulumi.dev.yaml)**:
- Location: East US
- Instance Count: 1
- SKU Size: Basic
- Environment: development

**Production (Pulumi.prod.yaml)**:
- Location: East US  
- Instance Count: 3
- SKU Size: Standard
- Environment: production

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `azure-native:location` | Azure region | East US |
| `environment` | Environment name | dev |
| `instance_count` | Container instances | 1 |
| `sku_size` | Resource tier | Basic |

## 📊 Outputs

After deployment, key outputs include:

- `resource_group_name`: Azure resource group name
- `storage_account_name`: Storage account for job data
- `container_registry_name`: Docker registry name
- `container_registry_login_server`: Registry URL
- `container_apps_environment_name`: App hosting environment

View outputs:
```bash
pulumi stack output
```

## 🔄 Integration with Application

### Container Registry Integration

1. **Build and Push Images**:
   ```bash
   # Get registry details
   REGISTRY=$(pulumi stack output container_registry_login_server)
   
   # Build and tag image
   docker build -t $REGISTRY/shift-scheduler:latest .
   
   # Push to registry
   docker push $REGISTRY/shift-scheduler:latest
   ```

2. **Configure Docker Compose**:
   ```yaml
   services:
     shift-scheduler:
       image: ${CONTAINER_REGISTRY}/shift-scheduler:latest
   ```

### Storage Integration

Configure the application to use Azure Storage:

```bash
# Get storage connection string
STORAGE_CONNECTION=$(pulumi stack output storage_connection_string)

# Set environment variable
export JOB_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION
```

### Container Apps Deployment

The Container Apps environment is ready for application deployment. Future phases will include:

1. **Application Deployment**: Deploy shift-scheduler containers
2. **Database Integration**: Connect to managed PostgreSQL
3. **Scaling Configuration**: Auto-scaling based on load
4. **Monitoring Setup**: Application insights and alerts

## 🛠️ Management Commands

### Stack Management
```bash
# List stacks
pulumi stack ls

# Switch stacks
pulumi stack select dev|prod

# View configuration
pulumi config

# Preview changes
pulumi preview

# Deploy changes
pulumi up

# View outputs
pulumi stack output
```

### Resource Management
```bash
# View all resources
pulumi stack --show-urns

# Refresh state
pulumi refresh

# Export/backup stack
pulumi stack export > backup.json
```

### Cleanup
```bash
# Destroy resources
./scripts/destroy.sh

# Or manually
pulumi destroy
pulumi stack rm <stack-name>
```

## 🔒 Security Considerations

### Development Environment
- Basic security settings for cost optimization
- Admin access enabled for simplicity
- Public network access allowed

### Production Environment
- Enhanced security configurations
- Managed identities for service authentication
- Private endpoints for secure access
- Network security groups and firewalls
- Azure Key Vault for secrets management

## 📈 Cost Optimization

### Development
- **Basic SKU** resources for minimal cost
- **Single instance** deployments
- **Local storage redundancy** (LRS)

### Production
- **Standard/Premium SKU** for performance
- **Multiple instances** for availability
- **Geo-redundant storage** (GRS) for durability
- **Auto-scaling** to optimize costs

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   az login
   pulumi login
   ```

2. **Resource Naming Conflicts**:
   - Storage accounts need globally unique names
   - Container registries need globally unique names
   - Use stack names to ensure uniqueness

3. **Permission Issues**:
   - Ensure Azure subscription has required permissions
   - Check RBAC roles for the deployment principal

### Debugging
```bash
# Verbose logging
pulumi up --verbose

# Check logs
pulumi logs

# Validate configuration
pulumi config
pulumi about
```

## 🔮 Future Enhancements

### Phase 3-8 Implementation
The current infrastructure provides the foundation for:

1. **Phase 3**: Storage Account for job data ✅
2. **Phase 4**: Container Registry ✅  
3. **Phase 5**: Container Apps Environment ✅
4. **Phase 6**: CI/CD Pipeline integration
5. **Phase 7**: Monitoring and security enhancements
6. **Phase 8**: Production optimization

### Planned Additions
- **Azure Key Vault**: Secrets management
- **Application Insights**: Application monitoring
- **Azure Database for PostgreSQL**: Managed database
- **Azure CDN**: Content delivery
- **Azure Front Door**: Load balancing and WAF

## 📚 Resources

- [Pulumi Azure Native Provider](https://www.pulumi.com/registry/packages/azure-native/)
- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Infrastructure README](infrastructure/README.md)