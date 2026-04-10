# Internet Exposure Detection — Terraform Resource Reference

This document is a sub-reference for the D2 diagram skill. It describes, for each
Azure Terraform resource type that can be internet-facing, exactly which HCL
attributes to inspect and what logic to apply to determine inbound or outbound
internet exposure.

> **⚠ Approximation notice:** Internet exposure detection from static Terraform
> code is inherently approximate. The actual network reachability depends on
> runtime factors not visible in HCL: Azure-level firewall rules, NSG
> effective rules, DNS resolution, service tags, Azure Policy overrides,
> regional restrictions, and conditions evaluated at apply-time (e.g.
> `var.public_access_enabled` whose value may differ per environment).
> Use these rules as a best-effort heuristic for diagram generation, not as a
> security audit.

---

## Inbound — Compute / Web

### `azurerm_linux_web_app` / `azurerm_windows_web_app`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Public** | `HTTPS (public FQDN)` |

**Public when:**
- `public_network_access_enabled` is absent or set to `true` (default).

**Private when:**
- `public_network_access_enabled = false` **AND** access is restricted to VNet
  integration / private endpoint only.

**Attributes to check:**
```hcl
resource "azurerm_linux_web_app" "example" {
  public_network_access_enabled = false   # private
  # Also check ip_restriction blocks in site_config for partial exposure
  site_config {
    ip_restriction {
      # If ip_restriction exists with action = "Allow" for specific IPs,
      # the app is still internet-accessible but restricted.
      # Treat as public with label "HTTPS (restricted IPs)".
    }
  }
}
```

**Decision tree:**
1. `public_network_access_enabled = false` → **private**, no internet link.
2. `ip_restriction` blocks present with `action = "Allow"` → **public (restricted)**, label `"HTTPS (restricted IPs)"`.
3. Otherwise → **public**, label `"HTTPS (public FQDN)"`.

---

### `azurerm_linux_function_app` / `azurerm_windows_function_app`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Public** | `HTTPS (public FQDN)` |

Same logic as Web App above.

**Attributes to check:**
```hcl
resource "azurerm_linux_function_app" "example" {
  public_network_access_enabled = false   # private

  site_config {
    ip_restriction { ... }   # partial exposure
  }
}
```

**Additional consideration:**
- Functions with `service_plan_id` referencing a **Consumption** plan are always
  public unless `public_network_access_enabled = false`.
- Functions on a **Premium/Dedicated** plan with VNet integration may still be
  public unless explicitly disabled.

---

### `azurerm_static_site`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Always public** | `HTTPS (static site)` |

Static Web Apps are always internet-accessible. There is no
`public_network_access_enabled` toggle.

**No attributes to check** — always generate an internet inbound link.

---

## Inbound — Monitoring

### `azurerm_log_analytics_workspace`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Public** | `ingestion + queries (default: public)` |

**Public when:**
- `internet_ingestion_enabled` is absent or set to `true` (default).
- `internet_query_enabled` is absent or set to `true` (default).

**Private when:**
- Both `internet_ingestion_enabled = false` **AND** `internet_query_enabled = false`.

**Attributes to check:**
```hcl
resource "azurerm_log_analytics_workspace" "example" {
  internet_ingestion_enabled = false   # blocks public data ingestion
  internet_query_enabled     = false   # blocks public query access
}
```

**Decision tree:**
1. Neither attribute set → **public** (both default to `true`), label `"ingestion + queries (default: public)"`.
2. `internet_ingestion_enabled = false` but `internet_query_enabled` absent/true → **partially public**, label `"queries only (public)"`.
3. `internet_query_enabled = false` but `internet_ingestion_enabled` absent/true → **partially public**, label `"ingestion only (public)"`.
4. Both `= false` → **private**, no internet link.

### `azurerm_application_insights`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Public** | `telemetry ingestion (default: public)` |

**Attributes to check:**
```hcl
resource "azurerm_application_insights" "example" {
  internet_ingestion_enabled = false   # blocks public telemetry ingestion
  internet_query_enabled     = false   # blocks public query access
}
```

Same decision tree as Log Analytics Workspace above.

> **Note:** Application Insights typically sends telemetry via its parent
> Log Analytics Workspace. If both are public, only draw the internet link
> to Log Analytics to avoid visual clutter, unless App Insights is queried
> independently.

---

## Inbound — Networking / Gateway

### `azurerm_application_gateway`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Always public** (when frontend has public IP) | `HTTP/HTTPS (App Gateway)` |

**Attributes to check:**
```hcl
resource "azurerm_application_gateway" "example" {
  frontend_ip_configuration {
    public_ip_address_id = azurerm_public_ip.agw.id   # public
    # If only subnet_id is set and no public_ip_address_id → internal only
  }
}
```

**Decision tree:**
1. `frontend_ip_configuration` has `public_ip_address_id` set → **public**, label `"HTTP/HTTPS (App Gateway)"`.
2. Only `subnet_id` in frontend → **private**, no internet link.

---

### `azurerm_cdn_frontdoor_profile`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Always public** | `HTTPS (Front Door)` |

Front Door is a global CDN/WAF — always internet-facing by design.

**No attributes to check** — always generate an internet inbound link.

---

### `azurerm_lb` (Load Balancer)

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Depends on SKU and frontend** | `HTTPS (Load Balancer)` |

**Attributes to check:**
```hcl
resource "azurerm_lb" "example" {
  sku = "Standard"   # or "Basic"

  frontend_ip_configuration {
    public_ip_address_id = azurerm_public_ip.lb.id   # public
    # If only subnet_id → internal LB
  }
}
```

**Decision tree:**
1. `frontend_ip_configuration` has `public_ip_address_id` → **public**, label `"HTTPS (Load Balancer)"`.
2. Only `subnet_id` → **internal**, no internet link.

---

### `azurerm_api_management`

| Direction | Default | Label |
|-----------|---------|-------|
| Inbound   | **Public by default** | `HTTPS (API Management)` |

**Attributes to check:**
```hcl
resource "azurerm_api_management" "example" {
  sku_name             = "Developer_1"
  virtual_network_type = "Internal"   # "None" (default) | "External" | "Internal"

  public_network_access_enabled = false   # only on Premium/Developer with VNet
}
```

**Decision tree:**
1. `virtual_network_type = "Internal"` → **private**, no internet link.
2. `virtual_network_type = "External"` → **public** (gateway public, management
   on VNet), label `"HTTPS (API Management)"`.
3. `virtual_network_type = "None"` or absent → **public**, label `"HTTPS (API Management)"`.
4. `public_network_access_enabled = false` overrides → **private**.

---

### `azurerm_public_ip`

Not rendered as a standalone internet-facing resource. Instead, check which
resource references it (`azurerm_application_gateway`, `azurerm_lb`,
`azurerm_nat_gateway`, `azurerm_firewall`, etc.) and apply the internet link
to that parent resource.

---

## Inbound — Data / Storage (conditional)

These resources are **not** internet-facing by default in well-architected
setups, but can be exposed if public access is toggled on.

### `azurerm_cosmosdb_account`

**Attributes to check:**
```hcl
resource "azurerm_cosmosdb_account" "example" {
  public_network_access_enabled = true   # default is true!
  is_virtual_network_filter_enabled = true

  ip_range_filter = "0.0.0.0"   # allows Azure portal; broader ranges = public
}
```

**Decision tree:**
1. `public_network_access_enabled = false` → **private**.
2. `public_network_access_enabled = true` (or absent) **AND** no `ip_range_filter`
   restrictive enough → treat as **conditionally public** but do NOT draw
   internet link by default (data plane, not a web endpoint).
3. Only draw internet link if explicitly requested via data-flow question.

---

### `azurerm_key_vault`

**Attributes to check:**
```hcl
resource "azurerm_key_vault" "example" {
  public_network_access_enabled = false

  network_acls {
    default_action = "Deny"    # "Allow" | "Deny"
    bypass         = "AzureServices"
    ip_rules       = ["203.0.113.0/24"]   # if present = some public access
  }
}
```

**Decision tree:**
1. `public_network_access_enabled = false` → **private**.
2. `network_acls.default_action = "Deny"` with no `ip_rules` → **private**.
3. `network_acls.default_action = "Allow"` or `ip_rules` present → **conditionally public** (do NOT draw unless data-flow enabled).

---

### `azurerm_storage_account`

**Attributes to check:**
```hcl
resource "azurerm_storage_account" "example" {
  public_network_access_enabled = false

  network_rules {
    default_action = "Deny"    # "Allow" | "Deny"
    ip_rules       = ["203.0.113.0/24"]
  }
}
```

Same logic as Key Vault above.

---

### `azurerm_app_configuration`

**Attributes to check:**
```hcl
resource "azurerm_app_configuration" "example" {
  public_network_access = "Disabled"   # "Enabled" | "Disabled"
}
```

**Decision tree:**
1. `public_network_access = "Disabled"` → **private**.
2. `public_network_access = "Enabled"` or absent → **conditionally public** (do NOT draw unless data-flow enabled).

---

### `azurerm_mssql_server`

**Attributes to check:**
```hcl
resource "azurerm_mssql_server" "example" {
  public_network_access_enabled = false

  azuread_administrator { ... }
}

resource "azurerm_mssql_firewall_rule" "allow_azure" {
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"   # allows Azure services
}
```

**Decision tree:**
1. `public_network_access_enabled = false` → **private**.
2. `azurerm_mssql_firewall_rule` with `0.0.0.0/0.0.0.0` → Azure services only (not full internet).
3. `azurerm_mssql_firewall_rule` with broad IP range → **conditionally public**.

---

### `azurerm_postgresql_flexible_server` / `azurerm_mysql_flexible_server`

**Attributes to check:**
```hcl
resource "azurerm_postgresql_flexible_server" "example" {
  public_network_access_enabled = false
  delegated_subnet_id           = azurerm_subnet.db.id   # VNet-injected = private
}
```

**Decision tree:**
1. `delegated_subnet_id` set → **private** (VNet-injected).
2. `public_network_access_enabled = false` → **private**.
3. Otherwise → **conditionally public**.

---

## Outbound — NAT / Egress

### `azurerm_nat_gateway`

| Direction | Default | Label |
|-----------|---------|-------|
| Outbound  | **Always** (provides SNAT for subnets) | `outbound NAT` |

**Attributes to check:**
```hcl
resource "azurerm_nat_gateway" "example" {
  # existence = outbound internet for associated subnets
}

resource "azurerm_subnet_nat_gateway_association" "example" {
  subnet_id      = azurerm_subnet.app.id
  nat_gateway_id = azurerm_nat_gateway.example.id
}
```

**Decision tree:**
1. `azurerm_nat_gateway` exists → draw outbound link from NAT gateway to Internet.
2. Check `azurerm_subnet_nat_gateway_association` to determine which subnets use it.
3. Label: `"outbound NAT"`.

---

### `azurerm_firewall`

| Direction | Default | Label |
|-----------|---------|-------|
| Outbound  | **Yes** (if used as egress) | `outbound (Firewall)` |

**Attributes to check:**
```hcl
resource "azurerm_firewall" "example" {
  sku_tier = "Standard"   # or "Premium"
  ip_configuration {
    public_ip_address_id = azurerm_public_ip.fw.id
  }
}
```

**Decision tree:**
1. Has `public_ip_address_id` → capable of outbound. Draw link if route tables
   send `0.0.0.0/0` to the firewall.
2. Also potentially inbound if DNAT rules exist (check `azurerm_firewall_nat_rule_collection`).

---

### NSG Rules (implicit outbound)

**Attributes to check in `azurerm_network_security_group`:**
```hcl
security_rule {
  direction                  = "Outbound"
  access                     = "Allow"
  destination_address_prefix = "Internet"   # or "0.0.0.0/0" or "*"
  destination_port_range     = "443"
}
```

**Decision tree:**
1. Outbound rule with `destination_address_prefix = "Internet"` or `"*"` or `"0.0.0.0/0"` → the associated subnet has outbound internet.
2. Draw outbound link from the subnet (or its workload) to Internet with label `"outbound (NSG allow)"`.
3. If all outbound rules deny Internet → no outbound link.

---

## Summary Table

| Resource Type | Direction | Default Exposure | Key Attribute | Private When |
|---|---|---|---|---|
| `azurerm_linux_web_app` | Inbound | Public | `public_network_access_enabled` | `= false` |
| `azurerm_windows_web_app` | Inbound | Public | `public_network_access_enabled` | `= false` |
| `azurerm_linux_function_app` | Inbound | Public | `public_network_access_enabled` | `= false` |
| `azurerm_windows_function_app` | Inbound | Public | `public_network_access_enabled` | `= false` |
| `azurerm_static_site` | Inbound | Always public | — | Never |
| `azurerm_log_analytics_workspace` | Inbound | Public | `internet_ingestion_enabled`, `internet_query_enabled` | Both `= false` |
| `azurerm_application_insights` | Inbound | Public | `internet_ingestion_enabled`, `internet_query_enabled` | Both `= false` |
| `azurerm_application_gateway` | Inbound | Public (if public IP) | `frontend_ip_configuration.public_ip_address_id` | No public IP |
| `azurerm_cdn_frontdoor_profile` | Inbound | Always public | — | Never |
| `azurerm_lb` | Inbound | Depends | `frontend_ip_configuration.public_ip_address_id` | No public IP |
| `azurerm_api_management` | Inbound | Public | `virtual_network_type` | `= "Internal"` |
| `azurerm_cosmosdb_account` | — | Conditional | `public_network_access_enabled` | `= false` |
| `azurerm_key_vault` | — | Conditional | `public_network_access_enabled`, `network_acls.default_action` | `= false` or `Deny` |
| `azurerm_storage_account` | — | Conditional | `public_network_access_enabled`, `network_rules.default_action` | `= false` or `Deny` |
| `azurerm_app_configuration` | — | Conditional | `public_network_access` | `= "Disabled"` |
| `azurerm_mssql_server` | — | Conditional | `public_network_access_enabled` | `= false` |
| `azurerm_postgresql_flexible_server` | — | Conditional | `public_network_access_enabled`, `delegated_subnet_id` | `= false` or VNet-injected |
| `azurerm_nat_gateway` | Outbound | Always | existence + subnet association | Never |
| `azurerm_firewall` | Outbound | Yes (if public IP) | `ip_configuration.public_ip_address_id` | No public IP |
| NSG rules | Outbound | Depends | `direction=Outbound`, `destination=Internet` | All outbound denied |
