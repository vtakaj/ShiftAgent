# Infrastructure Migration Guide

## Region Change: East US to Japan East

When changing the Azure region from East US to Japan East, resource names will change due to the naming convention using region abbreviations:

- **Old**: `rg-vtakaj-shiftsch-core-dev-eus-001` (East US = "eus")
- **New**: `rg-vtakaj-shiftsch-core-dev-je-001` (Japan East = "je")

### Migration Options

#### Option 1: Clean Deployment (Recommended for Dev)
```bash
# Destroy existing infrastructure
pulumi destroy --stack dev

# Deploy with new region
pulumi up --stack dev
```

#### Option 2: Create New Stack
```bash
# Create new stack for Japan East
pulumi stack init japan-dev

# Deploy to new stack
pulumi up --stack japan-dev

# After validation, destroy old stack
pulumi destroy --stack dev
pulumi stack rm dev
```

#### Option 3: Manual Resource Renaming (Advanced)
Use `pulumi state` commands to rename resources, but this is complex and error-prone.

### Post-Migration Steps

1. **Update DNS/endpoints** if applications reference old resource names
2. **Update CI/CD pipelines** to use new stack name if applicable
3. **Verify all services** are running correctly in Japan East
4. **Update monitoring/alerts** to point to new resources

### Rollback Plan

If issues occur, you can quickly rollback by:
1. Switching Pulumi config back to "East US"
2. Running `pulumi up` to recreate resources in East US
3. The old resource names will be restored

### Cost Considerations

- **Temporary**: During migration, you may have resources in both regions
- **Data Transfer**: Moving data between regions may incur costs
- **Downtime**: Plan for brief downtime during DNS/endpoint updates