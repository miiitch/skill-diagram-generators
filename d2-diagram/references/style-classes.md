# Reusable Style Classes

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
