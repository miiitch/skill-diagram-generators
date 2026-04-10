---
name: d2-diagram
description: "Generate D2 architecture diagrams from Terraform/Terragrunt infrastructure code. USE FOR: Terraform diagram, Terragrunt diagram, Azure architecture diagram, infrastructure visualization, generate .d2 file, D2 diagram code, connections and link styles between Azure resources, grouping with containers, applying Azure icons, layout engines (elk/dagre/tala), infrastructure visuals from HCL. DO NOT USE FOR: runtime debugging, code compilation, cloud deployment, or draw.io diagrams (use drawio-mcp instead)."
argument-hint: "Path to Terraform/Terragrunt files or folder to diagram"
---

# D2 Diagram Generator

## When to Use
- Generate architecture diagrams from Terraform or Terragrunt code
- Visualize Azure infrastructure with proper icons, connections, and grouping
- Create `.d2` files rendered to SVG/PNG via the `d2` CLI
- Represent resource dependencies, network topology, RBAC, monitoring, and data flows

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

- Look up the Terraform resource type key (e.g. `azurerm_linux_function_app`) in the mapping JSON.
- The mapped value is a relative path (e.g. `png/Icons/iot/10029-icon-service-Function-Apps.png`).
- Build the final icon URL: base path + `/` + relative path.
- In generated `.d2` files, reference the full URL directly in `icon:`.

Fallback: if no mapping entry exists, use `shape: rectangle` with a clear text label.

## Recommended Workflow
1. Read Terraform/Terragrunt files and list all resources + dependencies.
2. Analyze sub-resources for each parent and classify as hidden (from [registry](./references/hidden-sub-resources-registry.md)) or explicit.
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

These questions **must** be asked for every new diagram and every regeneration. Ask all at once using the ask-questions tool if available.

1. `Display network links? (Yes/No)`
2. `Display RBAC/IAM links? (Yes/No)`
3. `Display monitoring links? (Yes/No)`
4. `Display data flow links? (Yes/No)`
5. `Display secrets links (Key Vault references/reads)? (Yes/No)`
6. `Display hosting links (App/Function -> Service Plan)? (Yes/No)`
7. `Display DNS/custom-domain links? (Yes/No)`
8. `Display Internet node with inbound/outbound links? (Yes/No)`
9. `Display data source objects? (Yes/No)`
10. `Which grouping mode? (resource-group/vnet-centric/flat)`
11. `Which layout engine? (dagre/elk/tala)`
12. `Which D2 theme? (0/1/200/300)`

For full question descriptions and default values, see [questions reference](./references/questions.md).

---

## Reference Documents

Load these on-demand when needed during diagram generation:

| Reference | When to load |
|-----------|-------------|
| [D2 Language Reference](./references/d2-language-reference.md) | D2 syntax for nodes, connections, containers, icons, layouts, themes |
| [Hidden Sub-Resources Registry](./references/hidden-sub-resources-registry.md) | Lookup sub-resource styles and parent theme colors |
| [Grouping Modes](./references/grouping-modes.md) | Detailed rules for resource-group, vnet-centric, flat modes |
| [Style Classes](./references/style-classes.md) | Reusable D2 style class definitions for connections |
| [Internet Exposure Detection](./references/internet-exposure-detection.md) | Per-resource-type HCL attribute inspection for inbound/outbound exposure |
| [Complete Example](./references/complete-example.md) | Full Azure infrastructure diagram example with render command |

---

## Internet Exposure Rendering

When "Internet links" is enabled, analyze each resource's Terraform configuration to determine internet exposure. **Read [internet-exposure-detection.md](./references/internet-exposure-detection.md) for per-resource-type detection rules.**

Place a single "Internet" cloud node **outside all containers** using `shape: cloud`. Use green solid lines for inbound, orange dashed lines for outbound.

Label conventions:
- Inbound: `"HTTPS (public FQDN)"`, `"HTTPS (Front Door)"`, `"HTTP/HTTPS (App Gateway)"`
- Outbound: `"outbound NAT"`, `"outbound (NSG allow)"`

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

---

## Quality Gate Before Delivery

- [ ] D2 syntax is valid (`d2 fmt` passes without errors).
- [ ] No overlapping labels or ambiguous connections.
- [ ] Sub-resource analysis is complete — every hidden sub-resource mapped to a parent connection with registry-compliant label and style.
- [ ] Resource hierarchy is visible (network → compute → data layering when applicable).
- [ ] Only the requested link categories are shown.
- [ ] Data sources are represented only if requested by the user.
- [ ] Grouping follows user choice (resource-group, vnet-centric, or flat).
- [ ] Containers and external dependencies are visually distinct.
- [ ] Icons render correctly (use `shape: image` with valid icon paths).
- [ ] Resources without available icons use `shape: rectangle` with a text label.
- [ ] Workload-associated monitoring and storage are placed nearby, not in distant groups.
- [ ] Style classes are used for consistent connection styling (DRY).
- [ ] Layout engine is specified (`elk` recommended for infrastructure diagrams).
