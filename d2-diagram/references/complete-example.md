# Complete Example: Azure Infrastructure Diagram

```d2
direction: right

classes: {
  monitoring: {
    style: { stroke: "#0072C6"; stroke-width: 2 }
  }
  secret-read: {
    style: { stroke: "#D79B00"; stroke-width: 2; stroke-dash: 5 }
  }
  data: {
    style: { stroke: "#6C8EBF"; stroke-width: 2; animated: true }
  }
}

# -- Shared Resources --
rg-shared-resources-neu: "rg-shared-resources-neu" {
  style: { fill: "#F0F0F0"; stroke: "#999999"; border-radius: 8 }

  key-vault: "Key Vault" {
    shape: image
    icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/security/10245-icon-service-Key-Vaults.png
  }

  log-analytics: "Log Analytics" {
    shape: image
    icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/monitor/00009-icon-service-Log-Analytics-Workspaces.png
  }

  app-config: "App Configuration" {
    shape: image
    icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/integration/10219-icon-service-App-Configuration.png
  }
}

# -- IT Resources --
rg-it-resources-neu: "rg-it-resources-neu" {
  style: { fill: "#F5F9FF"; stroke: "#B0C4DE"; border-radius: 8 }

  support-func: "Support Function App" {
    shape: image
    icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/iot/10029-icon-service-Function-Apps.png
  }

  support-insights: "App Insights (Support)" {
    shape: image
    icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/monitor/00012-icon-service-Application-Insights.png
  }

  support-storage: "Storage Account" {
    shape: image
    icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/storage/10086-icon-service-Storage-Accounts.png
  }
}

# -- Connections --

# Monitoring
rg-it-resources-neu.support-func -> rg-it-resources-neu.support-insights: "telemetry" {
  class: monitoring
}
rg-it-resources-neu.support-insights -> rg-shared-resources-neu.log-analytics: "logs" {
  class: monitoring
}

# Secrets (hidden sub-resource: secret on Key Vault)
rg-it-resources-neu.support-func -> rg-shared-resources-neu.key-vault: "secret: zendesk-api-key" {
  class: secret-read
}

# Data flow (hidden sub-resource: blob-container on Storage)
rg-it-resources-neu.support-func -> rg-it-resources-neu.support-storage: "blob-container: exports" {
  class: data
}

# Configuration
rg-it-resources-neu.support-func -> rg-shared-resources-neu.app-config: "reads config"
```

Render with:
```bash
d2 --layout=elk --theme=1 infrastructure.d2 infrastructure.svg
```
