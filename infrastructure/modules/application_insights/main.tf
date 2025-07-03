# Application Insights module for enhanced monitoring

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

# Application Insights component
resource "azurerm_application_insights" "main" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = var.log_analytics_workspace_id
  application_type    = var.application_type
  
  # Retention settings
  retention_in_days = var.retention_in_days
  
  # Sampling settings
  sampling_percentage = var.sampling_percentage

  tags = var.tags
}

# Application Insights Smart Detection rules (optional enhancements)
resource "azurerm_monitor_smart_detector_alert_rule" "failure_anomalies" {
  count = var.enable_smart_detection ? 1 : 0

  name                = "${var.name}-failure-anomalies"
  resource_group_name = var.resource_group_name
  detector_type       = "FailureAnomaliesDetector"
  scope_resource_ids  = [azurerm_application_insights.main.id]
  frequency           = "PT1M"
  severity            = "Sev3"

  action_group {
    ids = var.action_group_ids
  }

  tags = var.tags
}

# Application Insights Workbook for Container Apps monitoring
resource "azurerm_application_insights_workbook" "container_apps" {
  count = var.create_workbook ? 1 : 0

  name                = "${var.name}-container-apps-workbook"
  resource_group_name = var.resource_group_name
  location            = var.location
  display_name        = "Container Apps Monitoring - ${var.name}"
  
  data_json = jsonencode({
    version = "Notebook/1.0"
    items = [
      {
        type = 1
        content = {
          json = "# ShiftAgent Container Apps Monitoring\n\nThis workbook provides monitoring insights for ShiftAgent Container Apps environment."
        }
      },
      {
        type = 3
        content = {
          version = "KqlItem/1.0"
          query = "AppRequests\n| where TimeGenerated > ago(1h)\n| summarize RequestCount = count(), AvgResponseTime = avg(DurationMs) by bin(TimeGenerated, 5m)\n| order by TimeGenerated desc"
          size = 0
          title = "Request Count and Response Time (Last Hour)"
          timeContext = {
            durationMs = 3600000
          }
          queryType = 0
          resourceType = "microsoft.insights/components"
        }
      },
      {
        type = 3
        content = {
          version = "KqlItem/1.0"
          query = "AppExceptions\n| where TimeGenerated > ago(1h)\n| summarize ExceptionCount = count() by bin(TimeGenerated, 5m), ExceptionType = Type\n| order by TimeGenerated desc"
          size = 0
          title = "Exceptions (Last Hour)"
          timeContext = {
            durationMs = 3600000
          }
          queryType = 0
          resourceType = "microsoft.insights/components"
        }
      }
    ]
  })

  tags = var.tags
}