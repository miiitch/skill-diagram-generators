# D2 Language Reference

## Nodes (Resources)

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

## Connections / Links (Edges)

This is the core feature for representing dependencies between resources.

### Direction

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

### Labels on Connections

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

### Chaining Connections

Create a path through multiple nodes in one line:

```d2
client -> api-gateway -> function-app -> cosmosdb
```

This creates three separate connections: `client->api-gateway`, `api-gateway->function-app`, `function-app->cosmosdb`.

### Multiple Connections Between Same Nodes

D2 supports multiple connections between the same pair of nodes. Each connection is distinct:

```d2
function-app -> storage: "blob read"
function-app -> storage: "queue trigger"
function-app -> storage: "table lookup"
```

### Connection References

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

## Connection Style Properties

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

### Available Style Properties for Connections

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

## Containers (Grouping)

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

### Cross-Container Connections

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

## Icons (Azure Resources)

D2 supports icons via the `icon` property.

### Icon Strategy: Mapping-Driven PNG URLs

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

## Layout Engines

D2 supports multiple layout engines. Choose based on diagram complexity:

| Engine   | Best for                              | Command                          |
|----------|---------------------------------------|----------------------------------|
| `dagre`  | Simple diagrams, default              | `d2 input.d2 output.svg`        |
| `elk`    | Complex diagrams, many connections    | `d2 --layout=elk input.d2 out.svg` |
| `tala`   | Premium engine, best readability      | `d2 --layout=tala input.d2 out.svg` |

**Default recommendation for infrastructure diagrams**: `elk` — it handles deeply nested containers and many cross-container connections better than `dagre`.

## Themes

Apply a built-in theme for consistent styling:

```bash
d2 --theme=200 input.d2 output.svg   # Terminal theme (dark)
d2 --theme=1 input.d2 output.svg     # Default light
d2 --theme=300 input.d2 output.svg   # Origami
```

Use `d2 --theme=0` (Neutral default) or `d2 --theme=1` for professional documentation diagrams.
