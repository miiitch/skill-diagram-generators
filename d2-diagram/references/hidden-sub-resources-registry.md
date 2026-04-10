# Hidden Sub-Resources Registry (Single Source of Truth)

When a sub-resource is listed here, do NOT create a standalone node. Instead, represent it as a styled connection to the parent resource.

## Parent Theme Colors

| Parent Resource         | Color     |
|-------------------------|-----------|
| Key Vault               | `#D79B00` |
| Service Bus             | `#9673A6` |
| Event Hub               | `#E67E22` |
| Storage Account         | `#6C8EBF` |
| Function App            | `#82B366` |
| Networking              | `#0078D4` |
| Private Endpoint        | `#9B59B6` |
| Monitoring              | `#0072C6` |

## Registry Entries

Each entry specifies: sub-resource type, parent, connection label format, and D2 style.

### Key Vault sub-resources

```d2
# secret
workload -> key-vault: "secret: my-secret-name" {
  style: { stroke: "#D79B00"; stroke-width: 2; stroke-dash: 5 }
}

# key
workload -> key-vault: "key: my-key-name" {
  style: { stroke: "#D79B00"; stroke-width: 2; stroke-dash: 0 }
}

# certificate
workload -> key-vault: "certificate: my-cert-name" {
  style: { stroke: "#D79B00"; stroke-width: 2; stroke-dash: 3 }
}
```

### Service Bus sub-resources

```d2
# queue
workload -> service-bus: "queue: my-queue" {
  style: { stroke: "#9673A6"; stroke-width: 2; stroke-dash: 0 }
}

# topic
workload -> service-bus: "topic: my-topic" {
  style: { stroke: "#9673A6"; stroke-width: 2; stroke-dash: 5 }
}

# subscription (on a topic)
workload -> service-bus: "subscription: my-sub" {
  style: { stroke: "#9673A6"; stroke-width: 2; stroke-dash: 3 }
}

# authorization-rule
workload -> service-bus: "authorization-rule: my-rule" {
  style: { stroke: "#9673A6"; stroke-width: 2; stroke-dash: 8 }
}
```

### Storage Account sub-resources

```d2
# blob-container
workload -> storage: "blob-container: my-container" {
  style: { stroke: "#6C8EBF"; stroke-width: 2; stroke-dash: 0 }
}

# file-share
workload -> storage: "file-share: my-share" {
  style: { stroke: "#6C8EBF"; stroke-width: 2; stroke-dash: 5 }
}

# table
workload -> storage: "table: my-table" {
  style: { stroke: "#6C8EBF"; stroke-width: 2; stroke-dash: 3 }
}

# storage-queue
workload -> storage: "storage-queue: my-queue" {
  style: { stroke: "#6C8EBF"; stroke-width: 2; stroke-dash: 8 }
}

# lifecycle-rule
workload -> storage: "lifecycle-rule: my-rule" {
  style: { stroke: "#6C8EBF"; stroke-width: 1; stroke-dash: 3 }
}
```

### Event Hub sub-resources

```d2
# consumer-group
workload -> event-hub: "consumer-group: my-group" {
  style: { stroke: "#E67E22"; stroke-width: 2; stroke-dash: 5 }
}

# authorization-rule
workload -> event-hub: "authorization-rule: my-rule" {
  style: { stroke: "#E67E22"; stroke-width: 2; stroke-dash: 8 }
}
```

### Function App sub-resources

```d2
# app-setting
workload -> function-app: "app-setting: my-setting" {
  style: { stroke: "#82B366"; stroke-width: 2; stroke-dash: 5 }
}

# connection-string
workload -> function-app: "connection-string: my-conn" {
  style: { stroke: "#82B366"; stroke-width: 2; stroke-dash: 3 }
}
```

### Networking sub-resources

```d2
# private-endpoint-connection
resource -> private-endpoint: "private-endpoint-connection: my-pe" {
  style: { stroke: "#0078D4"; stroke-width: 2; stroke-dash: 5 }
}
```

### Private Endpoint Rendering

Private Endpoints (`azurerm_private_endpoint`) are **not hidden sub-resources** — they must be rendered as standalone nodes with TWO explicit connections:

1. **Subnet link** (dashed): `subnet -> pe-node` — shows the PE is deployed in a subnet.
2. **Resource link** (solid, thicker): `pe-node -> target-resource` — shows which resource the PE connects to, with label `"private-link: <subresource_name>"`.

Use a distinct color (`#9B59B6` — purple) to differentiate PE links from regular network links.

**Style classes for PE links:**

```d2
classes: {
  pe-link: {
    style: {
      stroke: "#9B59B6"
      stroke-width: 2
      stroke-dash: 5
    }
  }
  pe-resource-link: {
    style: {
      stroke: "#9B59B6"
      stroke-width: 3
      stroke-dash: 0
    }
  }
}
```

**Example with Key Vault PE:**

```d2
pe-kv: "PE Key Vault" {
  shape: image
  icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/other/02579-icon-service-Private-Endpoints.png
}

# Subnet -> PE (dashed, shows placement)
snet-pe -> pe-kv: "subnet" { class: pe-link }

# PE -> Target resource (solid, shows private-link connection)
pe-kv -> key-vault: "private-link: vault" { class: pe-resource-link }
```

**Cross-container example (PE in a different RG than its subnet):**

```d2
rg-common.snet-pe -> rg-app.pe-cosmos: "subnet" { class: pe-link }
rg-app.pe-cosmos -> rg-app.cosmos-db: "private-link: Sql" { class: pe-resource-link }
```

### Monitoring sub-resources

```d2
# diagnostic-setting
resource -> log-analytics: "diagnostic-setting: my-diag" {
  style: { stroke: "#0072C6"; stroke-width: 2; stroke-dash: 5 }
}
```
