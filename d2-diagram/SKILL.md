---
name: d2-diagram
description: "Generate architecture diagrams using D2 language from Terraform/Terragrunt infrastructure. USE FOR: generating D2 diagram code (.d2 files), defining connections and link styles between Azure resources, grouping resources with containers, applying Azure icons, choosing layout engines, and producing clean infrastructure visuals. DO NOT USE FOR: runtime application debugging, code compilation issues, cloud deployment operations, or draw.io diagrams (use the drawio-mcp skill instead)."
license: MIT
---

# D2 Diagram Generator

## Goal
Create readable architecture diagrams using D2 language for Azure/Terraform infrastructure.
Output is `.d2` text files, rendered to SVG or PNG via the `d2` CLI.

## Tools
- **d2 CLI**: Render `.d2` files to SVG/PNG: `d2 input.d2 output.svg`
- **d2 CLI with layout engine**: `d2 --layout=elk input.d2 output.svg`
- **d2 fmt**: Format D2 files: `d2 fmt input.d2`
- No MCP server is used — the skill generates D2 source code as text.

## Icon Source Requirement

Use this Terraform icon mapping as the source of truth:

- Mapping index: `https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/icon-index-terraform-png.json`
- Base path for icon files: `https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main`

Resolution rule:

- Look up the Terraform resource type key (for example `azurerm_linux_function_app`) in the mapping JSON.
- The mapped value is a relative path (for example `png/Icons/iot/10029-icon-service-Function-Apps.png`).
- Build the final icon URL by concatenating base path + `/` + relative path.
- In generated `.d2` files, you can reference the full URL directly in `icon:`.

Fallback rule:

- If no mapping entry exists for a resource, use `shape: rectangle` (or another neutral shape) with a clear text label.

## Recommended Workflow
1. Read Terraform/Terragrunt files and list all resources + dependencies.
2. Analyze sub-resources for each parent and classify as hidden (from registry) or explicit.
3. Ask the mandatory Yes/No questionnaire before generating connections or containers (must be asked every time).
4. Determine the resource hierarchy before placing nodes.
5. Build workload-centric clusters first (workload at center, required resources around it).
6. Apply the **Hidden Sub-Resources Registry**: hide listed sub-resources and represent them as styled connections to the parent resource.
7. Resolve icon URLs from the mapping index, then generate the `.d2` file with containers, nodes, connections, icons, and styles.
8. Validate D2 syntax with `d2 fmt` before sharing.
9. Render with `d2 --layout=elk input.d2 output.svg` and verify output.
10. If the user wants an autonomous SVG, download mapped icons locally and render a bundled SVG.
11. When regenerating an existing diagram, re-resolve icon URLs from the mapping file (and re-download only used icons for autonomous output if needed).

## Mandatory Questions Before Diagram Generation

These questions are mandatory and must be asked for every new diagram and every diagram regeneration.
The agent must ask one question per link type, with only two allowed answers: `Yes` or `No`.

### Required Link-Type Questions (ask all of them)
1. Network links: `Display network links? (Yes/No)`
2. RBAC/IAM links: `Display RBAC/IAM links? (Yes/No)`
3. Monitoring links: `Display monitoring links? (Yes/No)`
4. Data flow links: `Display data flow links? (Yes/No)`
5. Secrets links: `Display secrets links (Key Vault references/reads)? (Yes/No)`
6. Hosting links: `Display hosting links (App/Function -> Service Plan)? (Yes/No)`
7. DNS/custom-domain links: `Display DNS/custom-domain links? (Yes/No)`
8. Internet links: `Display Internet node with inbound/outbound links? (Yes/No)`

### Additional Required Scope Questions
9. Data sources: `Display data source objects? (Yes/No)`
10. Grouping mode: `Which grouping mode? (resource-group/vnet-centric/flat)`
  - `resource-group`: wrap resources inside their Azure Resource Group as D2 containers. Cross-RG links use dot notation. **(default)**
  - `vnet-centric`: wrap only network resources (VNet, subnets, NSGs, PEs, public IPs, NAT gateways) inside VNet containers. All non-network resources (compute, data, monitoring, etc.) are placed outside and connect into VNet containers. VNet peerings are placed **between** VNet containers, not inside.
  - `flat`: no containers at all — every resource is a top-level node. Simplest layout, best for small infra or quick overviews.

### Required Rendering Questions
11. Layout engine: `Which layout engine should be used? (dagre/elk/tala)`
  - `dagre`: fastest and simple; best for small diagrams.
  - `elk`: best readability for complex infrastructure with many cross-links (recommended default).
  - `tala`: premium layout engine with high readability when available.
12. Theme: `Which D2 theme should be used? (0/1/200/300)`
  - `0`: neutral default style.
  - `1`: default light style for documentation.
  - `200`: terminal-like dark style.
  - `300`: origami style for more visual distinction.

### Default Behavior If User Does Not Answer
- Network links: `Yes`
- RBAC/IAM links: `Yes`
- Monitoring links: `Yes`
- Data flow links: `No`
- Secrets links: `No`
- Hosting links: `No`
- DNS/custom-domain links: `No`
- Internet links: `Yes`
- Data source objects: `No`
- Grouping mode: `resource-group`
- Layout engine: `elk`
- Theme: `1`

---

## D2 Language Reference

### Nodes (Resources)

Declare a node by writing its identifier. Use descriptive keys, and set the display label with a colon.

```d2
# Simple node
function-app

# Node with label
function-app: "Azure Function App"

# Node with shape
function-app: "Azure Function App" {
  shape: rectangle
}

# Node with icon (Azure SVG)
function-app: "Azure Function App" {
  shape: image
  icon: https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Cloud/SVG/ic_fluent_cloud_24_regular.svg
}
```

### Connections / Links (Edges)

This is the core feature for representing dependencies between resources.

#### Direction

```d2
# Directed (A depends on B, or A sends to B)
A -> B

# Reverse direction
A <- B

# Bidirectional
A <-> B

# Undirected (association without direction)
A -- B
```

#### Labels on Connections

```d2
# Simple label
function-app -> key-vault: "reads secrets"

# Multi-word labels
app-service -> sql-database: "JDBC connection"

# Connection with label and line break
function-app -> storage: |md
  blob read/write
  queue trigger
|
```

#### Chaining Connections

Create a path through multiple nodes in one line:

```d2
client -> api-gateway -> function-app -> cosmosdb
```

This creates three separate connections: `client->api-gateway`, `api-gateway->function-app`, `function-app->cosmosdb`.

#### Multiple Connections Between Same Nodes

D2 supports multiple connections between the same pair of nodes. Each connection is distinct:

```d2
function-app -> storage: "blob read"
function-app -> storage: "queue trigger"
function-app -> storage: "table lookup"
```

#### Connection References

Reference a specific connection to style it separately:

```d2
function-app -> key-vault: "secret lookup"

# Style the connection after declaring it
(function-app -> key-vault)[0].style: {
  stroke: "#D79B00"
  stroke-width: 2
  stroke-dash: 5
}
```

### Connection Style Properties

Apply styles inline or via connection references:

```d2
# Inline style
function-app -> key-vault: "secrets" {
  style: {
    stroke: "#D79B00"
    stroke-width: 2
    stroke-dash: 5
    opacity: 0.8
    font-color: "#333333"
    animated: true
  }
}
```

#### Available Style Properties for Connections

| Property       | Description                              | Example Values               |
|----------------|------------------------------------------|------------------------------|
| `stroke`       | Line color (hex)                         | `"#D79B00"`, `"#0072C6"`    |
| `stroke-width` | Line thickness                           | `1`, `2`, `3`                |
| `stroke-dash`  | Dash pattern (0 = solid)                 | `0`, `3`, `5`, `8`          |
| `opacity`      | Transparency (0.0–1.0)                   | `0.5`, `0.8`, `1.0`         |
| `font-color`   | Label text color                         | `"#333333"`, `"#FF0000"`    |
| `animated`     | Animated flow on the connection          | `true`, `false`             |
| `bold`         | Bold label                               | `true`, `false`             |
| `italic`       | Italic label                             | `true`, `false`             |

### Containers (Grouping)

Use containers to group resources by resource group, domain, or source file:

```d2
# Container with label
rg-it-resources-neu: "rg-it-resources-neu" {
  style: {
    fill: "#F5F5F5"
    stroke: "#CCCCCC"
    border-radius: 8
  }

  function-app: "Function App" {
    shape: image
    icon: https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/assets/Cloud/SVG/ic_fluent_cloud_24_regular.svg
  }

  storage: "Storage Account"
}

# Nested containers
rg-shared-resources-neu: "rg-shared-resources-neu" {
  monitoring: "Monitoring" {
    log-analytics: "Log Analytics"
    app-insights: "Application Insights"
  }

  security: "Security" {
    key-vault: "Key Vault"
  }
}
```

#### Cross-Container Connections

Connect nodes across different containers using dot notation:

```d2
rg-it-resources-neu.function-app -> rg-shared-resources-neu.security.key-vault: "reads secrets" {
  style: {
    stroke: "#D79B00"
    stroke-dash: 5
  }
}

rg-it-resources-neu.function-app -> rg-shared-resources-neu.monitoring.app-insights: "telemetry" {
  style: {
    stroke: "#0072C6"
    stroke-width: 2
  }
}
```

### Icons (Azure Resources)

D2 supports icons via the `icon` property.

#### Icon Strategy: Mapping-Driven PNG URLs

Use the mapping JSON as the canonical registry for Terraform resource type -> icon path.

- Mapping file: `https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/icon-index-terraform-png.json`
- Base URL: `https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main`

Build icon URLs with:

```text
<base-url>/<relative-path-from-mapping>
```

Example resolution:

- `azurerm_linux_function_app` -> `png/Icons/iot/10029-icon-service-Function-Apps.png`
- Final URL -> `https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/iot/10029-icon-service-Function-Apps.png`

Use full URLs directly in D2:

```d2
function-app: "Function App" {
  shape: image
  icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/iot/10029-icon-service-Function-Apps.png
}

key-vault: "Key Vault" {
  shape: image
  icon: https://raw.githubusercontent.com/miiitch/skill-diagram-generators/refs/heads/main/png/Icons/security/10245-icon-service-Key-Vaults.png
}
```

Optional autonomous SVG flow:

1. Download only the mapped icons used by the diagram into a local folder near the `.d2` file.
2. Replace `icon:` URLs with local relative paths.
3. Render with bundled output.

When no icon is available for a resource, use `shape: rectangle` with a text label.

### Layout Engines

D2 supports multiple layout engines. Choose based on diagram complexity:

| Engine   | Best for                              | Command                          |
|----------|---------------------------------------|----------------------------------|
| `dagre`  | Simple diagrams, default              | `d2 input.d2 output.svg`        |
| `elk`    | Complex diagrams, many connections    | `d2 --layout=elk input.d2 out.svg` |
| `tala`   | Premium engine, best readability      | `d2 --layout=tala input.d2 out.svg` |

**Default recommendation for infrastructure diagrams**: `elk` — it handles deeply nested containers and many cross-container connections better than `dagre`.

### Themes

Apply a built-in theme for consistent styling:

```bash
d2 --theme=200 input.d2 output.svg   # Terminal theme (dark)
d2 --theme=1 input.d2 output.svg     # Default light
d2 --theme=300 input.d2 output.svg   # Origami
```

Use `d2 --theme=0` (Neutral default) or `d2 --theme=1` for professional documentation diagrams.

---

## Internet Exposure Rendering

When "Internet links" is enabled, the agent must analyze each resource's Terraform configuration to determine internet exposure.

**Detailed detection rules per resource type are documented in [internet-exposure-detection.md](internet-exposure-detection.md).** Read this file before determining internet links.

### Detection Rules

**Inbound (Internet -> Resource):**
- `azurerm_linux_web_app` / `azurerm_windows_web_app`: internet-accessible by default (public FQDN) unless `public_network_access_enabled = false`.
- `azurerm_linux_function_app` / `azurerm_windows_function_app`: internet-accessible by default unless `public_network_access_enabled = false`.
- `azurerm_log_analytics_workspace`: internet-accessible by default (`internet_ingestion_enabled` and `internet_query_enabled` default to `true`). Private only when both are `false`.
- `azurerm_application_insights`: internet-accessible by default (same attributes as Log Analytics). If co-located with a public Log Analytics, prefer drawing only the Log Analytics link.
- `azurerm_application_gateway`: always internet-facing (has public IP).
- `azurerm_cdn_frontdoor_profile`: always internet-facing.
- `azurerm_lb` with `azurerm_public_ip`: internet-facing load balancer.
- `azurerm_static_site`: always internet-accessible.
- `azurerm_api_management` (non-internal): internet-facing.

**Outbound (Resource -> Internet):**
- `azurerm_nat_gateway` associated with a subnet: provides outbound internet for that subnet.
- GitHub-hosted runner subnets with outbound NSG rules allowing Internet.

### Rendering

Place a single "Internet" cloud node **outside all resource group containers**, using `shape: cloud`.

```d2
internet: "Internet" {
  shape: cloud
}
```

**Inbound style class** (green, solid — traffic coming in):
```d2
internet-inbound: {
  style: {
    stroke: "#27AE60"
    stroke-width: 3
  }
}
```

**Outbound style class** (orange, dashed — traffic going out):
```d2
internet-outbound: {
  style: {
    stroke: "#E67E22"
    stroke-width: 2
    stroke-dash: 5
  }
}
```

**Example:**
```d2
internet -> rg-app.web-app: "HTTPS (public FQDN)" { class: internet-inbound }
rg-common.nat-gateway -> internet: "outbound NAT" { class: internet-outbound }
```

### Label Conventions
- Inbound: `"HTTPS (public FQDN)"`, `"HTTPS (Front Door)"`, `"HTTP/HTTPS (App Gateway)"`
- Outbound: `"outbound NAT"`, `"outbound (NSG allow)"`

---

## Grouping Modes

### `resource-group` (default)

Wrap all resources inside D2 containers matching their Azure Resource Group.
Cross-container links use dot notation (`rg-common.key-vault`).

```d2
rg-common: "Resource Group — Common" {
  style: { fill: "#F0F0F0"; stroke: "#999999"; border-radius: 8 }

  vnet: "Virtual Network" { ... }
  snet-pe: "snet-pe" { ... }
  key-vault: "Key Vault" { ... }
}

rg-app: "Resource Group — App" {
  style: { fill: "#F5F9FF"; stroke: "#B0C4DE"; border-radius: 8 }

  web-app: "Web App" { ... }
  cosmos-db: "Cosmos DB" { ... }
}

rg-app.web-app -> rg-common.key-vault: "reads secrets" { ... }
```

### `vnet-centric`

Wrap **only network resources** inside VNet containers. Non-network resources
are top-level nodes that connect into VNet containers via links.

**Resources inside VNet containers:**
- `azurerm_virtual_network` (the container itself)
- `azurerm_subnet`
- `azurerm_network_security_group` (+ association)
- `azurerm_private_endpoint`
- `azurerm_public_ip`
- `azurerm_nat_gateway` (+ subnet association)
- `azurerm_route_table`
- `azurerm_network_interface`

**Resources outside VNet containers (top-level):**
- All compute: web apps, function apps, VMs, AKS, container apps
- All data: Cosmos DB, SQL, Storage
- All shared services: Key Vault, App Configuration, Log Analytics
- All monitoring: Application Insights
- Service Plans
- Internet node

**VNet peerings** are placed **between** VNet containers, never inside:

```d2
vnet-hub: "VNet Hub\n10.0.0.0/16" {
  style: { fill: "#E8F0FE"; stroke: "#0D3B66"; border-radius: 8 }

  snet-pe: "snet-pe" { ... }
  snet-app: "snet-app" { ... }
  nsg-runner: "NSG Runner" { ... }
  pe-kv: "PE Key Vault" { ... }
}

vnet-spoke: "VNet Spoke\n10.1.0.0/16" {
  style: { fill: "#E8F0FE"; stroke: "#0D3B66"; border-radius: 8 }

  snet-workload: "snet-workload" { ... }
}

# Peering — outside both VNet containers
vnet-hub <-> vnet-spoke: "VNet peering" {
  style: {
    stroke: "#0D3B66"
    stroke-width: 3
    stroke-dash: 3
  }
}

# Non-network resources at top level
web-app: "Web App" { ... }
key-vault: "Key Vault" { ... }
cosmos-db: "Cosmos DB" { ... }

# Links go into VNet containers
web-app -> vnet-hub.snet-app: "VNet integration" { class: vnet-integration }
vnet-hub.pe-kv -> key-vault: "private-link: vault" { class: pe-resource-link }
```

**VNet container style:**
```d2
style: {
  fill: "#E8F0FE"
  stroke: "#0D3B66"
  border-radius: 8
}
```

### `flat`

No containers — every resource is a top-level node. All links are direct
(no dot notation). Simplest layout, best for small infra or quick overviews.

```d2
vnet: "Virtual Network" { ... }
snet-pe: "snet-pe" { ... }
web-app: "Web App" { ... }
key-vault: "Key Vault" { ... }

vnet -> snet-pe: "" { class: network-link }
web-app -> snet-pe: "VNet integration" { class: vnet-integration }
```

---

## Resource Hierarchy and Link Policy

- Perform explicit sub-resource analysis before layout.
- Do not flatten all resource types on the same level.
- Use a hierarchy by resource type to reduce connection crossings.
- If network resources exist, make the network layer the central anchor.
- Place compute resources after the network layer.
- Keep each workload as a visual center and place its required resources nearby.
- Monitoring and storage associated with a workload must remain close to that workload.
- Shared/global monitoring backends (e.g., shared Log Analytics) can be grouped separately, but workload-level monitoring (e.g., App Insights instance) stays near its workload.
- Place data resources after the compute layer.
- Keep shared or external resources in separate containers.
- Default link categories to display: network, RBAC, monitoring.
- **Monitoring links**: style with `stroke: "#0072C6"` and `stroke-width: 2` to emphasize telemetry flow.
- Hide or summarize secondary dependency links (secret lookups, hosting, indirect) unless explicitly requested.
- For hidden sub-resources, represent dependency using a styled connection to the parent with label `<type>: <name>`.

## Hidden Sub-Resources Registry (Single Source of Truth)

When a sub-resource is listed here, do NOT create a standalone node. Instead, represent it as a styled connection to the parent resource.

### Parent Theme Colors

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

### Registry Entries

Each entry specifies: sub-resource type, parent, connection label format, and D2 style.

#### Key Vault sub-resources

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

#### Service Bus sub-resources

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

#### Storage Account sub-resources

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

#### Event Hub sub-resources

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

#### Function App sub-resources

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

#### Networking sub-resources

```d2
# private-endpoint-connection
resource -> private-endpoint: "private-endpoint-connection: my-pe" {
  style: { stroke: "#0078D4"; stroke-width: 2; stroke-dash: 5 }
}
```

#### Private Endpoint Rendering

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

#### Monitoring sub-resources

```d2
# diagnostic-setting
resource -> log-analytics: "diagnostic-setting: my-diag" {
  style: { stroke: "#0072C6"; stroke-width: 2; stroke-dash: 5 }
}
```

---

## Reusable Style Classes

Define style classes at the top of the `.d2` file to keep connection styles DRY:

```d2
classes: {
  monitoring-link: {
    style: {
      stroke: "#0072C6"
      stroke-width: 2
      animated: true
    }
  }
  secret-link: {
    style: {
      stroke: "#D79B00"
      stroke-width: 2
      stroke-dash: 5
    }
  }
  network-link: {
    style: {
      stroke: "#0078D4"
      stroke-width: 2
    }
  }
  rbac-link: {
    style: {
      stroke: "#A0522D"
      stroke-width: 2
      stroke-dash: 3
    }
  }
  data-flow: {
    style: {
      stroke: "#6C8EBF"
      stroke-width: 2
      animated: true
    }
  }
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

# Usage
function-app -> app-insights: "telemetry" { class: monitoring-link }
function-app -> key-vault: "secret: api-key" { class: secret-link }
snet-pe -> pe-kv: "subnet" { class: pe-link }
pe-kv -> key-vault: "private-link: vault" { class: pe-resource-link }
```

---

## Complete Example: Azure Infrastructure Diagram

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

---

## Quality Gate Before Delivery

- [ ] D2 syntax is valid (`d2 fmt` passes without errors).
- [ ] No overlapping labels or ambiguous connections.
- [ ] Sub-resource analysis is complete — every hidden sub-resource mapped to a parent connection with registry-compliant label and style.
- [ ] Resource hierarchy is visible (network → compute → data layering when applicable).
- [ ] Only the requested link categories are shown.
- [ ] Data sources are represented only if requested by the user.
- [ ] Grouping follows user choice (resource group or source file).
- [ ] Containers and external dependencies are visually distinct.
- [ ] Icons render correctly (use `shape: image` with valid icon paths).
- [ ] Resources without available icons use `shape: rectangle` with a text label.
- [ ] Workload-associated monitoring and storage are placed nearby, not in distant groups.
- [ ] Style classes are used for consistent connection styling (DRY).
- [ ] Layout engine is specified (`elk` recommended for infrastructure diagrams).
