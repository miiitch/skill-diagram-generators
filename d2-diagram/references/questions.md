# Mandatory Questions — Full Reference

These questions are mandatory and must be asked for every new diagram and every diagram regeneration.
The agent must ask one question per link type, with only two allowed answers: `Yes` or `No`.

## Required Link-Type Questions (ask all of them)

1. Network links: `Display network links? (Yes/No)`
2. RBAC/IAM links: `Display RBAC/IAM links? (Yes/No)`
3. Monitoring links: `Display monitoring links? (Yes/No)`
4. Data flow links: `Display data flow links? (Yes/No)`
5. Secrets links: `Display secrets links (Key Vault references/reads)? (Yes/No)`
6. Hosting links: `Display hosting links (App/Function -> Service Plan)? (Yes/No)`
7. DNS/custom-domain links: `Display DNS/custom-domain links? (Yes/No)`
8. Internet links: `Display Internet node with inbound/outbound links? (Yes/No)`

## Additional Required Scope Questions

9. Data sources: `Display data source objects? (Yes/No)`
10. Grouping mode: `Which grouping mode? (resource-group/vnet-centric/flat)`
    - `resource-group`: wrap resources inside their Azure Resource Group as D2 containers. Cross-RG links use dot notation. **(default)**
    - `vnet-centric`: wrap only network resources (VNet, subnets, NSGs, PEs, public IPs, NAT gateways) inside VNet containers. All non-network resources (compute, data, monitoring, etc.) are placed outside and connect into VNet containers. VNet peerings are placed **between** VNet containers, not inside.
    - `flat`: no containers at all — every resource is a top-level node. Simplest layout, best for small infra or quick overviews.

## Required Rendering Questions

11. Layout engine: `Which layout engine should be used? (dagre/elk/tala)`
    - `dagre`: fastest and simple; best for small diagrams.
    - `elk`: best readability for complex infrastructure with many cross-links (recommended default).
    - `tala`: premium layout engine with high readability when available.
12. Theme: `Which D2 theme should be used? (0/1/200/300)`
    - `0`: neutral default style.
    - `1`: default light style for documentation.
    - `200`: terminal-like dark style.
    - `300`: origami style for more visual distinction.

## Default Behavior If User Does Not Answer

| Question | Default |
|----------|---------|
| Network links | `Yes` |
| RBAC/IAM links | `Yes` |
| Monitoring links | `Yes` |
| Data flow links | `No` |
| Secrets links | `No` |
| Hosting links | `No` |
| DNS/custom-domain links | `No` |
| Internet links | `Yes` |
| Data source objects | `No` |
| Grouping mode | `resource-group` |
| Layout engine | `elk` |
| Theme | `1` |
