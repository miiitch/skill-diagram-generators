"""
icon_resolver.py
Module minimal pour consommer icon-mapping.json dans un skill de génération de diagrammes.
Aucune dépendance externe — stdlib Python uniquement.

Usage:
    from icon_resolver import IconResolver

    resolver = IconResolver("mapping/icon-mapping.json")

    # Résolution par type Terraform (azurerm_* ou azuread_*)
    icon = resolver.by_terraform("azurerm_kubernetes_cluster")
    icon = resolver.by_terraform("azuread_group")

    # Résolution par type Azure/Graph (Bicep/ARM)
    icon = resolver.by_azure_type("Microsoft.Compute/virtualMachines")
    icon = resolver.by_azure_type("Microsoft.Graph/groups")

    # Téléchargement SVG (bytes)
    svg_bytes = resolver.download_svg(icon)

    # URL directe
    print(icon["svg_url"])
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any


class IconResolver:
    """Charge icon-mapping.json et fournit résolution + téléchargement d'icônes."""

    def __init__(self, mapping_path: str | Path) -> None:
        mapping_path = Path(mapping_path)
        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        with mapping_path.open(encoding="utf-8") as f:
            data = json.load(f)

        self._icons: list[dict[str, Any]] = data["icons"]
        self.base_url: str = data.get("base_url", "")
        self.version: str = data.get("version", "")

        # Index de lookup
        self._by_id: dict[str, dict] = {i["id"]: i for i in self._icons}
        self._by_terraform: dict[str, list[dict]] = {}
        self._by_azure_type: dict[str, list[dict]] = {}

        for icon in self._icons:
            for tf_type in icon.get("terraform_resource_types", []):
                self._by_terraform.setdefault(tf_type.lower(), []).append(icon)
            az_type = icon.get("azure_resource_type", "")
            if az_type:
                self._by_azure_type.setdefault(az_type.lower(), []).append(icon)

    # ------------------------------------------------------------------
    # Résolution
    # ------------------------------------------------------------------

    def by_id(self, icon_id: str) -> dict | None:
        """Retourne une icône par son ID numérique (ex: '10023')."""
        return self._by_id.get(icon_id)

    def by_terraform(self, resource_type: str) -> dict | None:
        """
        Retourne l'icône correspondant à un type Terraform.
        Supporte azurerm_* (hashicorp/azurerm) et azuread_* (hashicorp/azuread).
        Retourne None si aucune correspondance.
        """
        results = self._by_terraform.get(resource_type.lower(), [])
        return results[0] if results else None

    def all_by_terraform(self, resource_type: str) -> list[dict]:
        """Retourne toutes les icônes correspondant à un type Terraform."""
        return self._by_terraform.get(resource_type.lower(), [])

    def by_azure_type(self, resource_type: str) -> dict | None:
        """
        Retourne l'icône correspondant à un type Azure ARM ou Microsoft Graph.
        Exemples :
          'Microsoft.Compute/virtualMachines'
          'Microsoft.Graph/groups'
          'Microsoft.Graph/identity/conditionalAccess/policies'
        """
        results = self._by_azure_type.get(resource_type.lower(), [])
        return results[0] if results else None

    def by_provider(self, provider: str) -> list[dict]:
        """
        Retourne toutes les icônes d'un provider Terraform.
        provider : 'azurerm' | 'azuread'
        """
        prefix = provider.lower().rstrip("_") + "_"
        return [
            icon for icon in self._icons
            if any(tf.startswith(prefix) for tf in icon.get("terraform_resource_types", []))
        ]

    def search(self, query: str) -> list[dict]:
        """Recherche insensible à la casse dans display_name et tags."""
        q = query.lower()
        return sorted(
            [
                icon for icon in self._icons
                if q in icon.get("display_name", "").lower()
                or any(q in tag.lower() for tag in icon.get("tags", []))
            ],
            key=lambda i: i["display_name"],
        )

    @property
    def icons(self) -> list[dict]:
        """Retourne toutes les icônes."""
        return self._icons

    # ------------------------------------------------------------------
    # Téléchargement (stdlib uniquement — aucune dépendance externe)
    # ------------------------------------------------------------------

    def download_svg(self, icon: dict, timeout: int = 10) -> bytes:
        """
        Télécharge le SVG de l'icône depuis svg_url et retourne les bytes.

        Args:
            icon:    Entrée du mapping (résultat de by_terraform / by_azure_type).
            timeout: Timeout HTTP en secondes.

        Returns:
            Contenu SVG en bytes.

        Raises:
            ValueError: si l'icône n'a pas de svg_url.
            urllib.error.URLError: en cas d'erreur réseau.
        """
        url = icon.get("svg_url", "")
        if not url:
            raise ValueError(f"Icon '{icon.get('id')}' has no svg_url")
        req = urllib.request.Request(url, headers={"User-Agent": "icon-resolver/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()

    def save_svg(self, icon: dict, output_path: str | Path, timeout: int = 10) -> None:
        """Télécharge le SVG et l'enregistre dans output_path."""
        Path(output_path).write_bytes(self.download_svg(icon, timeout=timeout))

    def svg_url(self, icon: dict) -> str:
        """Retourne l'URL SVG directe de l'icône."""
        return icon.get("svg_url", "")

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._icons)

    def __repr__(self) -> str:
        return f"IconResolver(icons={len(self)}, version={self.version!r})"
