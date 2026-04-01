#!/usr/bin/env python3
"""
generate-mapping.py
Scans local Azure SVG icons and generates icon-mapping.json.

Usage:
    python generate-mapping.py \
        --svg-dir   ../svg/Icons \
        --output    ../mapping/icon-mapping.json \
        --overrides ../mapping/mapping-overrides.json \
        --base-url  https://raw.githubusercontent.com/{owner}/azure-icons/main/icons/
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Seed table: display_name (lowercase) → (azure_resource_type, [terraform_types])
# Keys are lowercase, stripped versions of the service name parsed from the filename.
# ---------------------------------------------------------------------------
SEED_TABLE: dict[str, tuple[str, list[str]]] = {
    # Compute
    "virtual machine": (
        "Microsoft.Compute/virtualMachines",
        ["azurerm_linux_virtual_machine", "azurerm_windows_virtual_machine"],
    ),
    "virtual machines": (
        "Microsoft.Compute/virtualMachines",
        ["azurerm_linux_virtual_machine", "azurerm_windows_virtual_machine"],
    ),
    "virtual machine scale sets": (
        "Microsoft.Compute/virtualMachineScaleSets",
        ["azurerm_linux_virtual_machine_scale_set", "azurerm_windows_virtual_machine_scale_set"],
    ),
    "disk": (
        "Microsoft.Compute/disks",
        ["azurerm_managed_disk"],
    ),
    "disks": (
        "Microsoft.Compute/disks",
        ["azurerm_managed_disk"],
    ),
    "disk encryption sets": (
        "Microsoft.Compute/diskEncryptionSets",
        ["azurerm_disk_encryption_set"],
    ),
    "availability set": (
        "Microsoft.Compute/availabilitySets",
        ["azurerm_availability_set"],
    ),
    "image templates": (
        "Microsoft.VirtualMachineImages/imageTemplates",
        ["azurerm_image_builder_template"],
    ),
    "maintenance configuration": (
        "Microsoft.Maintenance/maintenanceConfigurations",
        ["azurerm_maintenance_configuration"],
    ),
    # Containers
    "azure kubernetes service": (
        "Microsoft.ContainerService/managedClusters",
        ["azurerm_kubernetes_cluster"],
    ),
    "kubernetes services": (
        "Microsoft.ContainerService/managedClusters",
        ["azurerm_kubernetes_cluster"],
    ),
    "container instances": (
        "Microsoft.ContainerInstance/containerGroups",
        ["azurerm_container_group"],
    ),
    "container registry": (
        "Microsoft.ContainerRegistry/registries",
        ["azurerm_container_registry"],
    ),
    "container apps": (
        "Microsoft.App/containerApps",
        ["azurerm_container_app"],
    ),
    "container app environments": (
        "Microsoft.App/managedEnvironments",
        ["azurerm_container_app_environment"],
    ),
    # App Services
    "app service": (
        "Microsoft.Web/sites",
        ["azurerm_linux_web_app", "azurerm_windows_web_app"],
    ),
    "app services": (
        "Microsoft.Web/sites",
        ["azurerm_linux_web_app", "azurerm_windows_web_app"],
    ),
    "app service plans": (
        "Microsoft.Web/serverfarms",
        ["azurerm_service_plan"],
    ),
    "function app": (
        "Microsoft.Web/sites",
        ["azurerm_linux_function_app", "azurerm_windows_function_app"],
    ),
    "static web apps": (
        "Microsoft.Web/staticSites",
        ["azurerm_static_site"],
    ),
    "api management services": (
        "Microsoft.ApiManagement/service",
        ["azurerm_api_management"],
    ),
    "api connections": (
        "Microsoft.Web/connections",
        ["azurerm_api_connection"],
    ),
    # Networking
    "virtual networks": (
        "Microsoft.Network/virtualNetworks",
        ["azurerm_virtual_network"],
    ),
    "virtual network": (
        "Microsoft.Network/virtualNetworks",
        ["azurerm_virtual_network"],
    ),
    "subnets": (
        "Microsoft.Network/virtualNetworks/subnets",
        ["azurerm_subnet"],
    ),
    "load balancers": (
        "Microsoft.Network/loadBalancers",
        ["azurerm_lb"],
    ),
    "application gateways": (
        "Microsoft.Network/applicationGateways",
        ["azurerm_application_gateway"],
    ),
    "application gateway": (
        "Microsoft.Network/applicationGateways",
        ["azurerm_application_gateway"],
    ),
    "azure firewall": (
        "Microsoft.Network/azureFirewalls",
        ["azurerm_firewall"],
    ),
    "firewalls": (
        "Microsoft.Network/azureFirewalls",
        ["azurerm_firewall"],
    ),
    "dns zones": (
        "Microsoft.Network/dnsZones",
        ["azurerm_dns_zone"],
    ),
    "private dns zones": (
        "Microsoft.Network/privateDnsZones",
        ["azurerm_private_dns_zone"],
    ),
    "network security groups": (
        "Microsoft.Network/networkSecurityGroups",
        ["azurerm_network_security_group"],
    ),
    "network interfaces": (
        "Microsoft.Network/networkInterfaces",
        ["azurerm_network_interface"],
    ),
    "public ip addresses": (
        "Microsoft.Network/publicIPAddresses",
        ["azurerm_public_ip"],
    ),
    "public ip prefixes": (
        "Microsoft.Network/publicIPPrefixes",
        ["azurerm_public_ip_prefix"],
    ),
    "route tables": (
        "Microsoft.Network/routeTables",
        ["azurerm_route_table"],
    ),
    "virtual network gateways": (
        "Microsoft.Network/virtualNetworkGateways",
        ["azurerm_virtual_network_gateway"],
    ),
    "local network gateways": (
        "Microsoft.Network/localNetworkGateways",
        ["azurerm_local_network_gateway"],
    ),
    "connections": (
        "Microsoft.Network/connections",
        ["azurerm_virtual_network_gateway_connection"],
    ),
    "express route circuits": (
        "Microsoft.Network/expressRouteCircuits",
        ["azurerm_express_route_circuit"],
    ),
    "traffic manager profiles": (
        "Microsoft.Network/trafficManagerProfiles",
        ["azurerm_traffic_manager_profile"],
    ),
    "front door": (
        "Microsoft.Cdn/profiles",
        ["azurerm_cdn_frontdoor_profile"],
    ),
    "cdn profiles": (
        "Microsoft.Cdn/profiles",
        ["azurerm_cdn_profile"],
    ),
    "nat gateways": (
        "Microsoft.Network/natGateways",
        ["azurerm_nat_gateway"],
    ),
    "private endpoints": (
        "Microsoft.Network/privateEndpoints",
        ["azurerm_private_endpoint"],
    ),
    "private link services": (
        "Microsoft.Network/privateLinkServices",
        ["azurerm_private_link_service"],
    ),
    "bastion": (
        "Microsoft.Network/bastionHosts",
        ["azurerm_bastion_host"],
    ),
    "azure bastion": (
        "Microsoft.Network/bastionHosts",
        ["azurerm_bastion_host"],
    ),
    "ddos protection plans": (
        "Microsoft.Network/ddosProtectionPlans",
        ["azurerm_network_ddos_protection_plan"],
    ),
    # Storage
    "storage accounts": (
        "Microsoft.Storage/storageAccounts",
        ["azurerm_storage_account"],
    ),
    "storage account": (
        "Microsoft.Storage/storageAccounts",
        ["azurerm_storage_account"],
    ),
    "azure netapp files": (
        "Microsoft.NetApp/netAppAccounts",
        ["azurerm_netapp_account"],
    ),
    "data lake storage": (
        "Microsoft.Storage/storageAccounts",
        ["azurerm_storage_data_lake_gen2_filesystem"],
    ),
    "azure data lake storage gen1": (
        "Microsoft.DataLakeStore/accounts",
        ["azurerm_data_lake_store"],
    ),
    # Databases
    "sql database": (
        "Microsoft.Sql/servers/databases",
        ["azurerm_mssql_database"],
    ),
    "sql server": (
        "Microsoft.Sql/servers",
        ["azurerm_mssql_server"],
    ),
    "sql servers": (
        "Microsoft.Sql/servers",
        ["azurerm_mssql_server"],
    ),
    "sql managed instance": (
        "Microsoft.Sql/managedInstances",
        ["azurerm_mssql_managed_instance"],
    ),
    "azure cosmos db": (
        "Microsoft.DocumentDB/databaseAccounts",
        ["azurerm_cosmosdb_account"],
    ),
    "azure cache for redis": (
        "Microsoft.Cache/Redis",
        ["azurerm_redis_cache"],
    ),
    "azure database for postgresql": (
        "Microsoft.DBforPostgreSQL/servers",
        ["azurerm_postgresql_server", "azurerm_postgresql_flexible_server"],
    ),
    "azure database for mysql": (
        "Microsoft.DBforMySQL/servers",
        ["azurerm_mysql_server", "azurerm_mysql_flexible_server"],
    ),
    "azure database for mariadb": (
        "Microsoft.DBforMariaDB/servers",
        ["azurerm_mariadb_server"],
    ),
    "azure synapse analytics": (
        "Microsoft.Synapse/workspaces",
        ["azurerm_synapse_workspace"],
    ),
    "synapse analytics": (
        "Microsoft.Synapse/workspaces",
        ["azurerm_synapse_workspace"],
    ),
    # Identity & Security
    "key vaults": (
        "Microsoft.KeyVault/vaults",
        ["azurerm_key_vault"],
    ),
    "key vault": (
        "Microsoft.KeyVault/vaults",
        ["azurerm_key_vault"],
    ),
    "azure active directory": (
        "Microsoft.AAD/domainServices",
        ["azurerm_active_directory_domain_service"],
    ),
    "managed identities": (
        "Microsoft.ManagedIdentity/userAssignedIdentities",
        ["azurerm_user_assigned_identity"],
    ),
    "entra id": (
        "Microsoft.AAD/domainServices",
        ["azurerm_active_directory_domain_service"],
    ),
    # Management
    "resource groups": (
        "Microsoft.Resources/resourceGroups",
        ["azurerm_resource_group"],
    ),
    "subscriptions": (
        "Microsoft.Resources/subscriptions",
        [],
    ),
    "policy": (
        "Microsoft.Authorization/policyDefinitions",
        ["azurerm_policy_definition", "azurerm_policy_assignment"],
    ),
    "blueprints": (
        "Microsoft.Blueprint/blueprints",
        [],
    ),
    "management groups": (
        "Microsoft.Management/managementGroups",
        ["azurerm_management_group"],
    ),
    "log analytics workspaces": (
        "Microsoft.OperationalInsights/workspaces",
        ["azurerm_log_analytics_workspace"],
    ),
    "automation accounts": (
        "Microsoft.Automation/automationAccounts",
        ["azurerm_automation_account"],
    ),
    "azure monitor": (
        "Microsoft.Insights/components",
        ["azurerm_monitor_action_group", "azurerm_monitor_metric_alert"],
    ),
    "application insights": (
        "Microsoft.Insights/components",
        ["azurerm_application_insights"],
    ),
    "azure dashboard": (
        "Microsoft.Portal/dashboards",
        ["azurerm_portal_dashboard"],
    ),
    # Integration / Messaging
    "service bus": (
        "Microsoft.ServiceBus/namespaces",
        ["azurerm_servicebus_namespace"],
    ),
    "event hubs": (
        "Microsoft.EventHub/namespaces",
        ["azurerm_eventhub_namespace"],
    ),
    "event grid": (
        "Microsoft.EventGrid/topics",
        ["azurerm_eventgrid_topic"],
    ),
    "logic apps": (
        "Microsoft.Logic/workflows",
        ["azurerm_logic_app_workflow"],
    ),
    "azure data factory": (
        "Microsoft.DataFactory/factories",
        ["azurerm_data_factory"],
    ),
    # IoT
    "iot hub": (
        "Microsoft.Devices/IotHubs",
        ["azurerm_iothub"],
    ),
    "iot hubs": (
        "Microsoft.Devices/IotHubs",
        ["azurerm_iothub"],
    ),
    "iot central": (
        "Microsoft.IoTCentral/iotApps",
        ["azurerm_iotcentral_application"],
    ),
    # DevOps / Dev
    "azure devops": (
        "Microsoft.DevOps/pipelines",
        [],
    ),
    # AI / ML
    "machine learning": (
        "Microsoft.MachineLearningServices/workspaces",
        ["azurerm_machine_learning_workspace"],
    ),
    "azure openai": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "cognitive services": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "bot services": (
        "Microsoft.BotService/botServices",
        ["azurerm_bot_service_azure_bot"],
    ),
    # Analytics
    "azure databricks": (
        "Microsoft.Databricks/workspaces",
        ["azurerm_databricks_workspace"],
    ),
    "hdinsight": (
        "Microsoft.HDInsight/clusters",
        ["azurerm_hdinsight_hadoop_cluster"],
    ),
    "stream analytics jobs": (
        "Microsoft.StreamAnalytics/streamingjobs",
        ["azurerm_stream_analytics_job"],
    ),
    "analysis services": (
        "Microsoft.AnalysisServices/servers",
        ["azurerm_analysis_services_server"],
    ),
    # Web
    "api apps": (
        "Microsoft.Web/sites",
        ["azurerm_linux_web_app", "azurerm_windows_web_app"],
    ),
    "notification hubs": (
        "Microsoft.NotificationHubs/namespaces",
        ["azurerm_notification_hub_namespace"],
    ),
    "signalr service": (
        "Microsoft.SignalRService/signalR",
        ["azurerm_signalr_service"],
    ),
    "azure spring apps": (
        "Microsoft.AppPlatform/Spring",
        ["azurerm_spring_cloud_service"],
    ),
    # Cognitive Services (all map to the same provider resource)
    "computer vision": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "custom vision": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "face apis": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "speech services": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "translator text": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "language understanding": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "content moderators": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "personalizers": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "qna makers": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "anomaly detector": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "form recognizers": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "immersive readers": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "language": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "content safety": (
        "Microsoft.CognitiveServices/accounts",
        ["azurerm_cognitive_account"],
    ),
    "ai studio": (
        "Microsoft.MachineLearningServices/workspaces",
        ["azurerm_machine_learning_workspace"],
    ),
    # Search
    "cognitive search": (
        "Microsoft.Search/searchServices",
        ["azurerm_search_service"],
    ),
    "serverless search": (
        "Microsoft.Search/searchServices",
        ["azurerm_search_service"],
    ),
    # Networking (display name ≠ heuristic)
    "expressroute circuits": (
        "Microsoft.Network/expressRouteCircuits",
        ["azurerm_express_route_circuit"],
    ),
    "express route circuits": (
        "Microsoft.Network/expressRouteCircuits",
        ["azurerm_express_route_circuit"],
    ),
    "azure firewall policy": (
        "Microsoft.Network/firewallPolicies",
        ["azurerm_firewall_policy"],
    ),
    "dns private resolver": (
        "Microsoft.Network/dnsResolvers",
        ["azurerm_private_dns_resolver"],
    ),
    "virtual wans": (
        "Microsoft.Network/virtualWans",
        ["azurerm_virtual_wan"],
    ),
    "virtual wan hub": (
        "Microsoft.Network/virtualHubs",
        ["azurerm_virtual_hub"],
    ),
    "ip groups": (
        "Microsoft.Network/ipGroups",
        ["azurerm_ip_group"],
    ),
    "front door and cdn profiles": (
        "Microsoft.Cdn/profiles",
        ["azurerm_cdn_frontdoor_profile"],
    ),
    "web application firewall policies": (
        "Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies",
        ["azurerm_web_application_firewall_policy"],
    ),
    "proximity placement groups": (
        "Microsoft.Compute/proximityPlacementGroups",
        ["azurerm_proximity_placement_group"],
    ),
    # Compute
    "shared image galleries": (
        "Microsoft.Compute/galleries",
        ["azurerm_shared_image_gallery"],
    ),
    "image definitions": (
        "Microsoft.Compute/galleries/images",
        ["azurerm_shared_image"],
    ),
    "image versions": (
        "Microsoft.Compute/galleries/images/versions",
        ["azurerm_shared_image_version"],
    ),
    "host groups": (
        "Microsoft.Compute/hostGroups",
        ["azurerm_dedicated_host_group"],
    ),
    "hosts": (
        "Microsoft.Compute/hosts",
        ["azurerm_dedicated_host"],
    ),
    "vm scale sets": (
        "Microsoft.Compute/virtualMachineScaleSets",
        ["azurerm_linux_virtual_machine_scale_set", "azurerm_windows_virtual_machine_scale_set"],
    ),
    "disks snapshots": (
        "Microsoft.Compute/snapshots",
        ["azurerm_snapshot"],
    ),
    "restore points collections": (
        "Microsoft.Compute/restorePointCollections",
        ["azurerm_restore_points_collection"],
    ),
    "automanaged vm": (
        "Microsoft.Automanage/configurationProfiles",
        ["azurerm_automanage_configuration"],
    ),
    "spot vm": (
        "Microsoft.Compute/virtualMachines",
        ["azurerm_linux_virtual_machine", "azurerm_windows_virtual_machine"],
    ),
    "spot vmss": (
        "Microsoft.Compute/virtualMachineScaleSets",
        ["azurerm_linux_virtual_machine_scale_set", "azurerm_windows_virtual_machine_scale_set"],
    ),
    "managed service fabric": (
        "Microsoft.ServiceFabric/managedClusters",
        ["azurerm_service_fabric_managed_cluster"],
    ),
    # Containers
    "batch accounts": (
        "Microsoft.Batch/batchAccounts",
        ["azurerm_batch_account"],
    ),
    "container registries": (
        "Microsoft.ContainerRegistry/registries",
        ["azurerm_container_registry"],
    ),
    "service fabric clusters": (
        "Microsoft.ServiceFabric/clusters",
        ["azurerm_service_fabric_cluster"],
    ),
    "azure red hat openshift": (
        "Microsoft.RedHatOpenShift/openShiftClusters",
        ["azurerm_redhat_openshift_cluster"],
    ),
    "aks automatic": (
        "Microsoft.ContainerService/managedClusters",
        ["azurerm_kubernetes_cluster"],
    ),
    # Databases
    "azure database mysql server": (
        "Microsoft.DBforMySQL/flexibleServers",
        ["azurerm_mysql_flexible_server"],
    ),
    "azure database postgresql server": (
        "Microsoft.DBforPostgreSQL/flexibleServers",
        ["azurerm_postgresql_flexible_server"],
    ),
    "azure database mariadb server": (
        "Microsoft.DBforMariaDB/servers",
        ["azurerm_mariadb_server"],
    ),
    "sql elastic pools": (
        "Microsoft.Sql/servers/elasticPools",
        ["azurerm_mssql_elasticpool"],
    ),
    "managed database": (
        "Microsoft.Sql/managedInstances/databases",
        ["azurerm_mssql_managed_database"],
    ),
    "elastic job agents": (
        "Microsoft.Sql/servers/jobAgents",
        ["azurerm_mssql_job_agent"],
    ),
    "azure sql": (
        "Microsoft.Sql/servers",
        ["azurerm_mssql_server"],
    ),
    "azure data explorer clusters": (
        "Microsoft.Kusto/clusters",
        ["azurerm_kusto_cluster"],
    ),
    # Storage
    "recovery services vaults": (
        "Microsoft.RecoveryServices/vaults",
        ["azurerm_recovery_services_vault"],
    ),
    "storage sync services": (
        "Microsoft.StorageSync/storageSyncServices",
        ["azurerm_storage_sync"],
    ),
    "data shares": (
        "Microsoft.DataShare/accounts",
        ["azurerm_data_share_account"],
    ),
    # Web
    "app service environments": (
        "Microsoft.Web/hostingEnvironments",
        ["azurerm_app_service_environment_v3"],
    ),
    "app service certificates": (
        "Microsoft.Web/certificates",
        ["azurerm_app_service_certificate"],
    ),
    "notification hub namespaces": (
        "Microsoft.NotificationHubs/namespaces",
        ["azurerm_notification_hub_namespace"],
    ),
    "signalr": (
        "Microsoft.SignalRService/signalR",
        ["azurerm_signalr_service"],
    ),
    "static apps": (
        "Microsoft.Web/staticSites",
        ["azurerm_static_site"],
    ),
    "api center": (
        "Microsoft.ApiCenter/services",
        ["azurerm_api_center"],
    ),
    # Analytics
    "hd insight clusters": (
        "Microsoft.HDInsight/clusters",
        ["azurerm_hdinsight_hadoop_cluster"],
    ),
    "power bi embedded": (
        "Microsoft.PowerBIDedicated/capacities",
        ["azurerm_powerbi_embedded"],
    ),
    "data lake analytics": (
        "Microsoft.DataLakeAnalytics/accounts",
        ["azurerm_data_lake_analytics_account"],
    ),
    "data lake store gen1": (
        "Microsoft.DataLakeStore/accounts",
        ["azurerm_data_lake_store"],
    ),
    # ── azuread provider — identity icons ────────────────────────────────────
    "users": (
        "Microsoft.Graph/users",
        ["azuread_user"],
    ),
    "groups": (
        "Microsoft.Graph/groups",
        ["azuread_group"],
    ),
    "enterprise applications": (
        "Microsoft.Graph/servicePrincipals",
        ["azuread_service_principal", "azuread_application_registration"],
    ),
    "administrative units": (
        "Microsoft.Graph/administrativeUnits",
        ["azuread_administrative_unit"],
    ),
    "conditional access": (
        "Microsoft.Graph/identity/conditionalAccess/policies",
        ["azuread_conditional_access_policy"],
    ),
    "azure ad b2c": (
        "Microsoft.AzureActiveDirectory/b2cDirectories",
        ["azuread_b2c_directory"],
    ),
    "external identities": (
        "Microsoft.AzureActiveDirectory/b2cDirectories",
        ["azuread_b2c_directory"],
    ),
    "identity governance": (
        "Microsoft.Graph/identityGovernance/entitlementManagement/accessPackageCatalogs",
        ["azuread_access_package_catalog", "azuread_access_package"],
    ),
    "entra domain services": (
        "Microsoft.AAD/domainServices",
        ["azurerm_active_directory_domain_service"],
    ),
    "entra id protection": (
        "Microsoft.Graph/identityProtection/riskyUsers",
        ["azuread_conditional_access_policy"],
    ),
    "entra privleged identity management": (
        "Microsoft.Graph/identityGovernance/privilegedAccess/group/eligibilitySchedules",
        ["azuread_privileged_access_group_eligibility_schedule"],
    ),
    "entra identity custom roles": (
        "Microsoft.Graph/roleManagement/directory/roleDefinitions",
        ["azuread_custom_directory_role"],
    ),
    "entra connect": (
        "Microsoft.Graph/onPremisesPublishingProfiles",
        [],
    ),
    "entra connect sync": (
        "Microsoft.Graph/onPremisesPublishingProfiles",
        [],
    ),
    "entra connect health": (
        "Microsoft.Graph/onPremisesPublishingProfiles",
        [],
    ),
    "entra verified id": (
        "Microsoft.Graph/verifiedIdAuthority",
        [],
    ),
    "verifiable credentials": (
        "Microsoft.Graph/verifiedIdAuthority",
        [],
    ),
    "entra identity risky signins": (
        "Microsoft.Graph/identityProtection/riskDetections",
        ["azuread_conditional_access_policy"],
    ),
    "entra identity risky users": (
        "Microsoft.Graph/identityProtection/riskyUsers",
        ["azuread_conditional_access_policy"],
    ),
    "identity secure score": (
        "Microsoft.Graph/security/secureScores",
        [],
    ),
    "multifactor authentication": (
        "Microsoft.Graph/policies/authenticationMethodsPolicy",
        ["azuread_authentication_method_policy"],
    ),
    "multi factor authentication": (
        "Microsoft.Graph/policies/authenticationMethodsPolicy",
        ["azuread_authentication_method_policy"],
    ),
    # Sentinel / Defender
    "azure sentinel": (
        "Microsoft.OperationsManagement/solutions",
        ["azurerm_sentinel_log_analytics_workspace_onboarding"],
    ),
    "microsoft defender for cloud": (
        "Microsoft.Security/pricings",
        ["azurerm_security_center_subscription_pricing"],
    ),
    "microsoft defender for iot": (
        "Microsoft.IoTSecurity/defenderSettings",
        [],
    ),
    "application security groups": (
        "Microsoft.Network/applicationSecurityGroups",
        ["azurerm_application_security_group"],
    ),
    # Management additional
    "azure arc": (
        "Microsoft.AzureArcData/dataControllers",
        ["azurerm_arc_kubernetes_cluster"],
    ),
    "arc machines": (
        "Microsoft.HybridCompute/machines",
        ["azurerm_arc_machine"],
    ),
    "azure lighthouse": (
        "Microsoft.ManagedServices/registrationDefinitions",
        ["azurerm_lighthouse_definition"],
    ),
    "resource graph explorer": (
        "Microsoft.ResourceGraph/operations",
        [],
    ),
}


# ---------------------------------------------------------------------------
# Terraform → Azure resource type reverse lookup
# Authoritative source: Terraform AzureRM provider schema + ARM documentation.
# Used to derive azure_resource_type from a known azurerm_* type when the
# display-name seed table doesn't have a match.
# ---------------------------------------------------------------------------
TERRAFORM_TO_AZURE: dict[str, str] = {
    # ── Compute ──────────────────────────────────────────────────────────────
    "azurerm_linux_virtual_machine":              "Microsoft.Compute/virtualMachines",
    "azurerm_windows_virtual_machine":            "Microsoft.Compute/virtualMachines",
    "azurerm_virtual_machine":                    "Microsoft.Compute/virtualMachines",
    "azurerm_linux_virtual_machine_scale_set":    "Microsoft.Compute/virtualMachineScaleSets",
    "azurerm_windows_virtual_machine_scale_set":  "Microsoft.Compute/virtualMachineScaleSets",
    "azurerm_orchestrated_virtual_machine_scale_set": "Microsoft.Compute/virtualMachineScaleSets",
    "azurerm_managed_disk":                       "Microsoft.Compute/disks",
    "azurerm_availability_set":                   "Microsoft.Compute/availabilitySets",
    "azurerm_proximity_placement_group":          "Microsoft.Compute/proximityPlacementGroups",
    "azurerm_capacity_reservation_group":         "Microsoft.Compute/capacityReservationGroups",
    "azurerm_disk_encryption_set":                "Microsoft.Compute/diskEncryptionSets",
    "azurerm_image":                              "Microsoft.Compute/images",
    "azurerm_snapshot":                           "Microsoft.Compute/snapshots",
    "azurerm_dedicated_host":                     "Microsoft.Compute/hosts",
    "azurerm_dedicated_host_group":               "Microsoft.Compute/hostGroups",
    "azurerm_maintenance_configuration":          "Microsoft.Maintenance/maintenanceConfigurations",
    "azurerm_image_builder_template":             "Microsoft.VirtualMachineImages/imageTemplates",
    "azurerm_automanage_configuration":           "Microsoft.Automanage/configurationProfiles",
    # ── App Service / Web ────────────────────────────────────────────────────
    "azurerm_linux_web_app":                      "Microsoft.Web/sites",
    "azurerm_windows_web_app":                    "Microsoft.Web/sites",
    "azurerm_app_service":                        "Microsoft.Web/sites",
    "azurerm_linux_function_app":                 "Microsoft.Web/sites",
    "azurerm_windows_function_app":               "Microsoft.Web/sites",
    "azurerm_function_app":                       "Microsoft.Web/sites",
    "azurerm_logic_app_standard":                 "Microsoft.Web/sites",
    "azurerm_service_plan":                       "Microsoft.Web/serverfarms",
    "azurerm_app_service_plan":                   "Microsoft.Web/serverfarms",
    "azurerm_static_site":                        "Microsoft.Web/staticSites",
    "azurerm_app_service_environment_v3":         "Microsoft.Web/hostingEnvironments",
    "azurerm_app_service_certificate":            "Microsoft.Web/certificates",
    "azurerm_app_service_custom_hostname_binding": "Microsoft.Web/sites/hostNameBindings",
    # ── Logic Apps ───────────────────────────────────────────────────────────
    "azurerm_logic_app_workflow":                 "Microsoft.Logic/workflows",
    "azurerm_logic_app_integration_account":      "Microsoft.Logic/integrationAccounts",
    # ── Networking ───────────────────────────────────────────────────────────
    "azurerm_virtual_network":                    "Microsoft.Network/virtualNetworks",
    "azurerm_subnet":                             "Microsoft.Network/virtualNetworks/subnets",
    "azurerm_virtual_network_peering":            "Microsoft.Network/virtualNetworks/virtualNetworkPeerings",
    "azurerm_network_interface":                  "Microsoft.Network/networkInterfaces",
    "azurerm_network_security_group":             "Microsoft.Network/networkSecurityGroups",
    "azurerm_application_security_group":         "Microsoft.Network/applicationSecurityGroups",
    "azurerm_public_ip":                          "Microsoft.Network/publicIPAddresses",
    "azurerm_public_ip_prefix":                   "Microsoft.Network/publicIPPrefixes",
    "azurerm_lb":                                 "Microsoft.Network/loadBalancers",
    "azurerm_application_gateway":                "Microsoft.Network/applicationGateways",
    "azurerm_firewall":                           "Microsoft.Network/azureFirewalls",
    "azurerm_firewall_policy":                    "Microsoft.Network/firewallPolicies",
    "azurerm_dns_zone":                           "Microsoft.Network/dnsZones",
    "azurerm_private_dns_zone":                   "Microsoft.Network/privateDnsZones",
    "azurerm_virtual_network_gateway":            "Microsoft.Network/virtualNetworkGateways",
    "azurerm_local_network_gateway":              "Microsoft.Network/localNetworkGateways",
    "azurerm_virtual_network_gateway_connection": "Microsoft.Network/connections",
    "azurerm_express_route_circuit":              "Microsoft.Network/expressRouteCircuits",
    "azurerm_express_route_gateway":              "Microsoft.Network/expressRouteGateways",
    "azurerm_route_table":                        "Microsoft.Network/routeTables",
    "azurerm_nat_gateway":                        "Microsoft.Network/natGateways",
    "azurerm_private_endpoint":                   "Microsoft.Network/privateEndpoints",
    "azurerm_private_link_service":               "Microsoft.Network/privateLinkServices",
    "azurerm_bastion_host":                       "Microsoft.Network/bastionHosts",
    "azurerm_network_ddos_protection_plan":       "Microsoft.Network/ddosProtectionPlans",
    "azurerm_traffic_manager_profile":            "Microsoft.Network/trafficManagerProfiles",
    "azurerm_cdn_profile":                        "Microsoft.Cdn/profiles",
    "azurerm_cdn_frontdoor_profile":              "Microsoft.Cdn/profiles",
    "azurerm_cdn_endpoint":                       "Microsoft.Cdn/profiles/endpoints",
    "azurerm_virtual_hub":                        "Microsoft.Network/virtualHubs",
    "azurerm_virtual_wan":                        "Microsoft.Network/virtualWans",
    "azurerm_vpn_gateway":                        "Microsoft.Network/vpnGateways",
    "azurerm_vpn_site":                           "Microsoft.Network/vpnSites",
    "azurerm_web_application_firewall_policy":    "Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies",
    "azurerm_network_watcher":                    "Microsoft.Network/networkWatchers",
    "azurerm_network_watcher_flow_log":           "Microsoft.Network/networkWatchers/flowLogs",
    "azurerm_ip_group":                           "Microsoft.Network/ipGroups",
    "azurerm_network_manager":                    "Microsoft.Network/networkManagers",
    # ── Storage ──────────────────────────────────────────────────────────────
    "azurerm_storage_account":                    "Microsoft.Storage/storageAccounts",
    "azurerm_storage_blob":                       "Microsoft.Storage/storageAccounts/blobServices/containers/blobs",
    "azurerm_storage_container":                  "Microsoft.Storage/storageAccounts/blobServices/containers",
    "azurerm_storage_share":                      "Microsoft.Storage/storageAccounts/fileServices/shares",
    "azurerm_storage_queue":                      "Microsoft.Storage/storageAccounts/queueServices/queues",
    "azurerm_storage_table":                      "Microsoft.Storage/storageAccounts/tableServices/tables",
    "azurerm_storage_data_lake_gen2_filesystem":  "Microsoft.Storage/storageAccounts",
    "azurerm_netapp_account":                     "Microsoft.NetApp/netAppAccounts",
    "azurerm_netapp_pool":                        "Microsoft.NetApp/netAppAccounts/capacityPools",
    "azurerm_netapp_volume":                      "Microsoft.NetApp/netAppAccounts/capacityPools/volumes",
    "azurerm_data_lake_store":                    "Microsoft.DataLakeStore/accounts",
    # ── Databases ────────────────────────────────────────────────────────────
    "azurerm_mssql_server":                       "Microsoft.Sql/servers",
    "azurerm_mssql_database":                     "Microsoft.Sql/servers/databases",
    "azurerm_mssql_managed_instance":             "Microsoft.Sql/managedInstances",
    "azurerm_mssql_elasticpool":                  "Microsoft.Sql/servers/elasticPools",
    "azurerm_cosmosdb_account":                   "Microsoft.DocumentDB/databaseAccounts",
    "azurerm_cosmosdb_sql_database":              "Microsoft.DocumentDB/databaseAccounts/sqlDatabases",
    "azurerm_redis_cache":                        "Microsoft.Cache/Redis",
    "azurerm_redis_enterprise_cluster":           "Microsoft.Cache/redisEnterprise",
    "azurerm_postgresql_server":                  "Microsoft.DBforPostgreSQL/servers",
    "azurerm_postgresql_flexible_server":         "Microsoft.DBforPostgreSQL/flexibleServers",
    "azurerm_mysql_server":                       "Microsoft.DBforMySQL/servers",
    "azurerm_mysql_flexible_server":              "Microsoft.DBforMySQL/flexibleServers",
    "azurerm_mariadb_server":                     "Microsoft.DBforMariaDB/servers",
    "azurerm_synapse_workspace":                  "Microsoft.Synapse/workspaces",
    "azurerm_synapse_spark_pool":                 "Microsoft.Synapse/workspaces/bigDataPools",
    "azurerm_synapse_sql_pool":                   "Microsoft.Synapse/workspaces/sqlPools",
    # ── Containers ───────────────────────────────────────────────────────────
    "azurerm_kubernetes_cluster":                 "Microsoft.ContainerService/managedClusters",
    "azurerm_kubernetes_cluster_node_pool":       "Microsoft.ContainerService/managedClusters/agentPools",
    "azurerm_container_registry":                 "Microsoft.ContainerRegistry/registries",
    "azurerm_container_group":                    "Microsoft.ContainerInstance/containerGroups",
    "azurerm_container_app":                      "Microsoft.App/containerApps",
    "azurerm_container_app_environment":          "Microsoft.App/managedEnvironments",
    "azurerm_container_app_job":                  "Microsoft.App/jobs",
    # ── Identity & Security ──────────────────────────────────────────────────
    "azurerm_key_vault":                          "Microsoft.KeyVault/vaults",
    "azurerm_key_vault_key":                      "Microsoft.KeyVault/vaults/keys",
    "azurerm_key_vault_secret":                   "Microsoft.KeyVault/vaults/secrets",
    "azurerm_key_vault_certificate":              "Microsoft.KeyVault/vaults/certificates",
    "azurerm_key_vault_managed_hardware_security_module": "Microsoft.KeyVault/managedHSMs",
    "azurerm_user_assigned_identity":             "Microsoft.ManagedIdentity/userAssignedIdentities",
    "azurerm_active_directory_domain_service":    "Microsoft.AAD/domainServices",
    "azurerm_security_center_workspace":          "Microsoft.Security/workspaceSettings",
    "azurerm_security_center_subscription_pricing": "Microsoft.Security/pricings",
    "azurerm_sentinel_alert_rule_ms_security_incident": "Microsoft.SecurityInsights/alertRules",
    # ── Management & Governance ──────────────────────────────────────────────
    "azurerm_resource_group":                     "Microsoft.Resources/resourceGroups",
    "azurerm_management_group":                   "Microsoft.Management/managementGroups",
    "azurerm_policy_definition":                  "Microsoft.Authorization/policyDefinitions",
    "azurerm_policy_set_definition":              "Microsoft.Authorization/policySetDefinitions",
    "azurerm_policy_assignment":                  "Microsoft.Authorization/policyAssignments",
    "azurerm_role_assignment":                    "Microsoft.Authorization/roleAssignments",
    "azurerm_role_definition":                    "Microsoft.Authorization/roleDefinitions",
    "azurerm_log_analytics_workspace":            "Microsoft.OperationalInsights/workspaces",
    "azurerm_log_analytics_solution":             "Microsoft.OperationsManagement/solutions",
    "azurerm_automation_account":                 "Microsoft.Automation/automationAccounts",
    "azurerm_automation_runbook":                 "Microsoft.Automation/automationAccounts/runbooks",
    "azurerm_portal_dashboard":                   "Microsoft.Portal/dashboards",
    "azurerm_blueprints_assignment":              "Microsoft.Blueprint/blueprintAssignments",
    # ── Monitoring ───────────────────────────────────────────────────────────
    "azurerm_application_insights":              "Microsoft.Insights/components",
    "azurerm_application_insights_workbook":     "Microsoft.Insights/workbooks",
    "azurerm_monitor_action_group":              "Microsoft.Insights/actionGroups",
    "azurerm_monitor_metric_alert":              "Microsoft.Insights/metricAlerts",
    "azurerm_monitor_activity_log_alert":        "Microsoft.Insights/activityLogAlerts",
    "azurerm_monitor_scheduled_query_rules_alert": "Microsoft.Insights/scheduledQueryRules",
    "azurerm_monitor_diagnostic_setting":        "Microsoft.Insights/diagnosticSettings",
    "azurerm_monitor_data_collection_rule":      "Microsoft.Insights/dataCollectionRules",
    # ── Integration / Messaging ──────────────────────────────────────────────
    "azurerm_servicebus_namespace":              "Microsoft.ServiceBus/namespaces",
    "azurerm_servicebus_queue":                  "Microsoft.ServiceBus/namespaces/queues",
    "azurerm_servicebus_topic":                  "Microsoft.ServiceBus/namespaces/topics",
    "azurerm_servicebus_subscription":           "Microsoft.ServiceBus/namespaces/topics/subscriptions",
    "azurerm_eventhub_namespace":                "Microsoft.EventHub/namespaces",
    "azurerm_eventhub":                          "Microsoft.EventHub/namespaces/eventhubs",
    "azurerm_eventgrid_topic":                   "Microsoft.EventGrid/topics",
    "azurerm_eventgrid_domain":                  "Microsoft.EventGrid/domains",
    "azurerm_eventgrid_system_topic":            "Microsoft.EventGrid/systemTopics",
    "azurerm_eventgrid_event_subscription":      "Microsoft.EventGrid/eventSubscriptions",
    "azurerm_data_factory":                      "Microsoft.DataFactory/factories",
    "azurerm_data_factory_pipeline":             "Microsoft.DataFactory/factories/pipelines",
    "azurerm_api_management":                    "Microsoft.ApiManagement/service",
    "azurerm_api_management_api":                "Microsoft.ApiManagement/service/apis",
    "azurerm_api_connection":                    "Microsoft.Web/connections",
    "azurerm_notification_hub_namespace":        "Microsoft.NotificationHubs/namespaces",
    "azurerm_notification_hub":                  "Microsoft.NotificationHubs/namespaces/notificationHubs",
    "azurerm_signalr_service":                   "Microsoft.SignalRService/signalR",
    "azurerm_web_pubsub":                        "Microsoft.SignalRService/webPubSub",
    # ── IoT ──────────────────────────────────────────────────────────────────
    "azurerm_iothub":                            "Microsoft.Devices/IotHubs",
    "azurerm_iothub_dps":                        "Microsoft.Devices/provisioningServices",
    "azurerm_iotcentral_application":            "Microsoft.IoTCentral/iotApps",
    "azurerm_digital_twins_instance":            "Microsoft.DigitalTwins/digitalTwinsInstances",
    "azurerm_iot_time_series_insights_gen2_environment": "Microsoft.TimeSeriesInsights/environments",
    # ── AI / ML ──────────────────────────────────────────────────────────────
    "azurerm_machine_learning_workspace":        "Microsoft.MachineLearningServices/workspaces",
    "azurerm_machine_learning_compute_cluster":  "Microsoft.MachineLearningServices/workspaces/computes",
    "azurerm_cognitive_account":                 "Microsoft.CognitiveServices/accounts",
    "azurerm_bot_service_azure_bot":             "Microsoft.BotService/botServices",
    "azurerm_search_service":                    "Microsoft.Search/searchServices",
    # ── Analytics ────────────────────────────────────────────────────────────
    "azurerm_databricks_workspace":              "Microsoft.Databricks/workspaces",
    "azurerm_hdinsight_hadoop_cluster":          "Microsoft.HDInsight/clusters",
    "azurerm_hdinsight_spark_cluster":           "Microsoft.HDInsight/clusters",
    "azurerm_hdinsight_kafka_cluster":           "Microsoft.HDInsight/clusters",
    "azurerm_stream_analytics_job":              "Microsoft.StreamAnalytics/streamingjobs",
    "azurerm_analysis_services_server":          "Microsoft.AnalysisServices/servers",
    "azurerm_purview_account":                   "Microsoft.Purview/accounts",
    "azurerm_data_share_account":                "Microsoft.DataShare/accounts",
    # ── Developer tools / Misc ───────────────────────────────────────────────
    "azurerm_spring_cloud_service":              "Microsoft.AppPlatform/Spring",
    "azurerm_app_configuration":                 "Microsoft.AppConfiguration/configurationStores",
    "azurerm_service_fabric_cluster":            "Microsoft.ServiceFabric/clusters",
    "azurerm_service_fabric_managed_cluster":    "Microsoft.ServiceFabric/managedClusters",
    "azurerm_batch_account":                     "Microsoft.Batch/batchAccounts",
    "azurerm_batch_pool":                        "Microsoft.Batch/batchAccounts/pools",
    # ── Heuristic aliases (plural/variant names generated by the filename parser) ──
    # These are NOT real Terraform resource names but match the auto-generated heuristic
    # so that azure_resource_type can be derived even without a SEED_TABLE entry.
    "azurerm_virtual_wans":                      "Microsoft.Network/virtualWans",
    "azurerm_virtual_wan_hub":                   "Microsoft.Network/virtualHubs",
    "azurerm_virtual_hubs":                      "Microsoft.Network/virtualHubs",
    "azurerm_expressroute_circuits":             "Microsoft.Network/expressRouteCircuits",
    "azurerm_express_route_circuits":            "Microsoft.Network/expressRouteCircuits",
    "azurerm_azure_firewall_policy":             "Microsoft.Network/firewallPolicies",
    "azurerm_dns_private_resolver":              "Microsoft.Network/dnsResolvers",
    "azurerm_ip_groups":                         "Microsoft.Network/ipGroups",
    "azurerm_proximity_placement_groups":        "Microsoft.Compute/proximityPlacementGroups",
    "azurerm_shared_image_galleries":            "Microsoft.Compute/galleries",
    "azurerm_shared_image_gallery":              "Microsoft.Compute/galleries",
    "azurerm_dedicated_host_group":              "Microsoft.Compute/hostGroups",
    "azurerm_dedicated_host_groups":             "Microsoft.Compute/hostGroups",
    "azurerm_dedicated_host":                    "Microsoft.Compute/hosts",
    "azurerm_dedicated_hosts":                   "Microsoft.Compute/hosts",
    "azurerm_vm_scale_sets":                     "Microsoft.Compute/virtualMachineScaleSets",
    "azurerm_disks_snapshots":                   "Microsoft.Compute/snapshots",
    "azurerm_restore_points_collections":        "Microsoft.Compute/restorePointCollections",
    "azurerm_restore_points_collection":         "Microsoft.Compute/restorePointCollections",
    "azurerm_automanage_configuration":          "Microsoft.Automanage/configurationProfiles",
    "azurerm_automanaged_vm":                    "Microsoft.Automanage/configurationProfiles",
    "azurerm_batch_accounts":                    "Microsoft.Batch/batchAccounts",
    "azurerm_container_registries":              "Microsoft.ContainerRegistry/registries",
    "azurerm_service_fabric_clusters":           "Microsoft.ServiceFabric/clusters",
    "azurerm_service_fabric_managed_cluster":    "Microsoft.ServiceFabric/managedClusters",
    "azurerm_managed_service_fabric":            "Microsoft.ServiceFabric/managedClusters",
    "azurerm_redhat_openshift_cluster":          "Microsoft.RedHatOpenShift/openShiftClusters",
    "azurerm_azure_red_hat_openshift":           "Microsoft.RedHatOpenShift/openShiftClusters",
    "azurerm_aks_automatic":                     "Microsoft.ContainerService/managedClusters",
    "azurerm_mysql_flexible_server":             "Microsoft.DBforMySQL/flexibleServers",
    "azurerm_postgresql_flexible_server":        "Microsoft.DBforPostgreSQL/flexibleServers",
    "azurerm_azure_database_mysql_server":       "Microsoft.DBforMySQL/flexibleServers",
    "azurerm_azure_database_postgresql_server":  "Microsoft.DBforPostgreSQL/flexibleServers",
    "azurerm_azure_database_mariadb_server":     "Microsoft.DBforMariaDB/servers",
    "azurerm_sql_elastic_pools":                 "Microsoft.Sql/servers/elasticPools",
    "azurerm_mssql_managed_database":            "Microsoft.Sql/managedInstances/databases",
    "azurerm_mssql_job_agent":                   "Microsoft.Sql/servers/jobAgents",
    "azurerm_azure_sql":                         "Microsoft.Sql/servers",
    "azurerm_kusto_cluster":                     "Microsoft.Kusto/clusters",
    "azurerm_azure_data_explorer_clusters":      "Microsoft.Kusto/clusters",
    "azurerm_recovery_services_vault":           "Microsoft.RecoveryServices/vaults",
    "azurerm_recovery_services_vaults":          "Microsoft.RecoveryServices/vaults",
    "azurerm_storage_sync":                      "Microsoft.StorageSync/storageSyncServices",
    "azurerm_storage_sync_services":             "Microsoft.StorageSync/storageSyncServices",
    "azurerm_data_share_account":                "Microsoft.DataShare/accounts",
    "azurerm_data_shares":                       "Microsoft.DataShare/accounts",
    "azurerm_app_service_environment_v3":        "Microsoft.Web/hostingEnvironments",
    "azurerm_app_service_environments":          "Microsoft.Web/hostingEnvironments",
    "azurerm_app_service_certificate":           "Microsoft.Web/certificates",
    "azurerm_app_service_certificates":          "Microsoft.Web/certificates",
    "azurerm_static_site":                       "Microsoft.Web/staticSites",
    "azurerm_static_apps":                       "Microsoft.Web/staticSites",
    "azurerm_api_center":                        "Microsoft.ApiCenter/services",
    "azurerm_notification_hub_namespaces":       "Microsoft.NotificationHubs/namespaces",
    "azurerm_signalr":                           "Microsoft.SignalRService/signalR",
    "azurerm_hdinsight_hadoop_cluster":          "Microsoft.HDInsight/clusters",
    "azurerm_hd_insight_clusters":               "Microsoft.HDInsight/clusters",
    "azurerm_powerbi_embedded":                  "Microsoft.PowerBIDedicated/capacities",
    "azurerm_power_bi_embedded":                 "Microsoft.PowerBIDedicated/capacities",
    "azurerm_data_lake_analytics_account":       "Microsoft.DataLakeAnalytics/accounts",
    "azurerm_data_lake_analytics":               "Microsoft.DataLakeAnalytics/accounts",
    "azurerm_data_lake_store_gen1":              "Microsoft.DataLakeStore/accounts",
    "azurerm_front_door_and_cdn_profiles":       "Microsoft.Cdn/profiles",
    "azurerm_web_application_firewall_policieswaf": "Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies",
    "azurerm_cognitive_search":                  "Microsoft.Search/searchServices",
    "azurerm_ai_studio":                         "Microsoft.MachineLearningServices/workspaces",
    # Integration heuristic names
    "azurerm_data_factories":                    "Microsoft.DataFactory/factories",
    "azurerm_event_grid_topics":                 "Microsoft.EventGrid/topics",
    "azurerm_event_grid_domains":                "Microsoft.EventGrid/domains",
    "azurerm_partner_topic":                     "Microsoft.EventGrid/partnerTopics",
    "azurerm_system_topic":                      "Microsoft.EventGrid/systemTopics",
    "azurerm_partner_namespace":                 "Microsoft.EventGrid/partnerNamespaces",
    "azurerm_partner_registration":              "Microsoft.EventGrid/partnerRegistrations",
    "azurerm_relays":                            "Microsoft.Relay/namespaces",
    "azurerm_azure_service_bus":                 "Microsoft.ServiceBus/namespaces",
    "azurerm_integration_accounts":              "Microsoft.Logic/integrationAccounts",
    "azurerm_integration_service_environments":  "Microsoft.Logic/integrationServiceEnvironments",
    "azurerm_logic_apps_custom_connector":       "Microsoft.Web/customApis",
    "azurerm_azure_api_for_fhir":               "Microsoft.HealthcareApis/services",
    # Storage additional heuristic names
    "azurerm_azure_fileshares":                  "Microsoft.Storage/storageAccounts/fileServices/shares",
    "azurerm_storage_accounts_classic":          "Microsoft.ClassicStorage/storageAccounts",
    # Management additional
    "azurerm_log_analytics_workspaces":          "Microsoft.OperationalInsights/workspaces",
    "azurerm_automation_accounts":               "Microsoft.Automation/automationAccounts",
    # ── azuread provider (hashicorp/azuread) — Microsoft Entra ID / Azure AD ─
    # Applications & Service Principals
    "azuread_application":                       "Microsoft.Graph/applications",
    "azuread_application_registration":          "Microsoft.Graph/applications",
    "azuread_application_password":              "Microsoft.Graph/applications",
    "azuread_application_certificate":           "Microsoft.Graph/applications",
    "azuread_application_federated_identity_credential": "Microsoft.Graph/applications",
    "azuread_application_optional_claims":       "Microsoft.Graph/applications",
    "azuread_application_api_access":            "Microsoft.Graph/applications",
    "azuread_service_principal":                 "Microsoft.Graph/servicePrincipals",
    "azuread_service_principal_password":        "Microsoft.Graph/servicePrincipals",
    "azuread_service_principal_certificate":     "Microsoft.Graph/servicePrincipals",
    "azuread_service_principal_delegated_permission_grant": "Microsoft.Graph/servicePrincipals",
    "azuread_service_principal_claims_mapping_policy_assignment": "Microsoft.Graph/servicePrincipals",
    # Users
    "azuread_user":                              "Microsoft.Graph/users",
    "azuread_invitation":                        "Microsoft.Graph/invitations",
    # Groups
    "azuread_group":                             "Microsoft.Graph/groups",
    "azuread_group_member":                      "Microsoft.Graph/groups",
    "azuread_group_role_management_policy":      "Microsoft.Graph/groups",
    # Directory Roles
    "azuread_directory_role":                    "Microsoft.Graph/directoryRoles",
    "azuread_directory_role_assignment":         "Microsoft.Graph/roleManagement/directory/roleAssignments",
    "azuread_directory_role_member":             "Microsoft.Graph/directoryRoles",
    "azuread_custom_directory_role":             "Microsoft.Graph/roleManagement/directory/roleDefinitions",
    # Administrative Units
    "azuread_administrative_unit":               "Microsoft.Graph/administrativeUnits",
    "azuread_administrative_unit_member":        "Microsoft.Graph/administrativeUnits",
    "azuread_administrative_unit_role_member":   "Microsoft.Graph/administrativeUnits",
    # Conditional Access
    "azuread_conditional_access_policy":         "Microsoft.Graph/identity/conditionalAccess/policies",
    "azuread_named_location":                    "Microsoft.Graph/identity/conditionalAccess/namedLocations",
    "azuread_authentication_strength_policy":    "Microsoft.Graph/policies/authenticationStrengthPolicies",
    "azuread_authentication_method_policy":      "Microsoft.Graph/policies/authenticationMethodsPolicy",
    "azuread_claims_mapping_policy":             "Microsoft.Graph/policies/claimsMappingPolicies",
    # B2C / External Identities
    "azuread_b2c_directory":                     "Microsoft.AzureActiveDirectory/b2cDirectories",
    # Entitlement Management / Identity Governance
    "azuread_access_package":                    "Microsoft.Graph/identityGovernance/entitlementManagement/accessPackages",
    "azuread_access_package_catalog":            "Microsoft.Graph/identityGovernance/entitlementManagement/accessPackageCatalogs",
    "azuread_access_package_assignment_policy":  "Microsoft.Graph/identityGovernance/entitlementManagement/assignmentPolicies",
    "azuread_access_package_resource_catalog_association": "Microsoft.Graph/identityGovernance/entitlementManagement/accessPackageCatalogs",
    "azuread_access_package_resource_package_association": "Microsoft.Graph/identityGovernance/entitlementManagement/accessPackages",
    # Privileged Identity Management (PIM)
    "azuread_privileged_access_group_eligibility_schedule": "Microsoft.Graph/identityGovernance/privilegedAccess/group/eligibilitySchedules",
    "azuread_privileged_access_group_assignment_schedule":  "Microsoft.Graph/identityGovernance/privilegedAccess/group/assignmentSchedules",
    # Domains & Tenants
    "azuread_domain":                            "Microsoft.Graph/domains",
    # Heuristic aliases — match names auto-generated from SVG filenames
    "azuread_users":                             "Microsoft.Graph/users",
    "azuread_groups":                            "Microsoft.Graph/groups",
    "azuread_enterprise_applications":           "Microsoft.Graph/servicePrincipals",
    "azuread_enterprise_application":            "Microsoft.Graph/servicePrincipals",
    "azuread_administrative_units":              "Microsoft.Graph/administrativeUnits",
    "azuread_conditional_access":                "Microsoft.Graph/identity/conditionalAccess/policies",
    "azuread_azure_ad_b2c":                      "Microsoft.AzureActiveDirectory/b2cDirectories",
    "azuread_azure_ad_b_2_c":                    "Microsoft.AzureActiveDirectory/b2cDirectories",
    "azuread_identity_governance":               "Microsoft.Graph/identityGovernance/entitlementManagement/accessPackageCatalogs",
    "azuread_entra_domain_services":             "Microsoft.AAD/domainServices",
    "azuread_entra_id_protection":               "Microsoft.Graph/identityProtection/riskyUsers",
    "azuread_entra_privleged_identity_management": "Microsoft.Graph/identityGovernance/privilegedAccess/group/eligibilitySchedules",
    "azuread_entra_identity_custom_roles":       "Microsoft.Graph/roleManagement/directory/roleDefinitions",
    "azuread_entra_connect":                     "Microsoft.Graph/onPremisesPublishingProfiles",
    "azuread_entra_connect_sync":                "Microsoft.Graph/onPremisesPublishingProfiles",
    "azuread_entra_connect_health":              "Microsoft.Graph/onPremisesPublishingProfiles",
    "azuread_entra_verified_id":                 "Microsoft.Graph/verifiedIdAuthority",
    "azuread_entra_identity_risky_signins":      "Microsoft.Graph/identityProtection/riskDetections",
    "azuread_entra_identity_risky_users":        "Microsoft.Graph/identityProtection/riskyUsers",
    "azuread_identity_secure_score":             "Microsoft.Graph/security/secureScores",
    "azuread_multifactor_authentication":        "Microsoft.Graph/policies/authenticationMethodsPolicy",
    "azuread_multi_factor_authentication":       "Microsoft.Graph/policies/authenticationMethodsPolicy",
}


def azure_type_from_terraform_types(terraform_types: list[str]) -> str:
    """Return the Azure resource type derived from a list of Terraform types.
    Returns the first non-empty match, or empty string if none found.
    """
    for tf_type in terraform_types:
        az = TERRAFORM_TO_AZURE.get(tf_type.lower(), "")
        if az:
            return az
    return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FILENAME_RE = re.compile(r"^(\d+)-icon-service-(.+)\.svg$", re.IGNORECASE)

# Map folder names (on disk, with spaces) → normalized category slug
CATEGORY_SLUG: dict[str, str] = {
    "ai + machine learning": "ai-machine-learning",
    "analytics": "analytics",
    "app services": "app-services",
    "azure ecosystem": "azure-ecosystem",
    "azure stack": "azure-stack",
    "blockchain": "blockchain",
    "compute": "compute",
    "containers": "containers",
    "databases": "databases",
    "devops": "devops",
    "general": "general",
    "hybrid + multicloud": "hybrid-multicloud",
    "identity": "identity",
    "integration": "integration",
    "intune": "intune",
    "iot": "iot",
    "management + governance": "management-governance",
    "menu": "menu",
    "migrate": "migrate",
    "migration": "migration",
    "mixed reality": "mixed-reality",
    "mobile": "mobile",
    "monitor": "monitor",
    "networking": "networking",
    "new icons": "new-icons",
    "other": "other",
    "security": "security",
    "storage": "storage",
    "web": "web",
}


def parse_filename(filename: str) -> tuple[str, str] | None:
    """Return (icon_id, service_name) or None if the filename doesn't match."""
    m = FILENAME_RE.match(filename)
    if not m:
        return None
    icon_id = m.group(1)
    raw_name = m.group(2)
    # Remove surrounding parentheses artifacts, replace dashes with spaces
    service_name = raw_name.replace("-", " ").replace("(", "").replace(")", "").strip()
    # Collapse multiple spaces
    service_name = re.sub(r"\s+", " ", service_name)
    return icon_id, service_name


def display_name_to_heuristic_terraform(display_name: str) -> str:
    """Heuristic: 'Virtual Machine' → 'azurerm_virtual_machine'."""
    slug = display_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return f"azurerm_{slug}"


def lookup(display_name: str) -> tuple[str, list[str]]:
    """Return (azure_resource_type, [terraform_types]) using seed table → reverse lookup → heuristic."""
    key = display_name.lower().strip()
    if key in SEED_TABLE:
        azure_type, tf_types = SEED_TABLE[key]
        # Fill azure_type from reverse table if seed didn't have it
        if not azure_type:
            azure_type = azure_type_from_terraform_types(tf_types)
        return azure_type, tf_types
    # Try without trailing 's' (plural → singular)
    if key.endswith("s") and key[:-1] in SEED_TABLE:
        azure_type, tf_types = SEED_TABLE[key[:-1]]
        if not azure_type:
            azure_type = azure_type_from_terraform_types(tf_types)
        return azure_type, tf_types
    # Heuristic fallback: derive azurerm_* name, then look up Azure type
    heuristic_tf = display_name_to_heuristic_terraform(display_name)
    azure_type = TERRAFORM_TO_AZURE.get(heuristic_tf, "")
    return azure_type, [heuristic_tf]


def build_svg_url(base_url: str, category_slug: str, filename: str) -> str:
    """Build the full raw GitHub URL for an SVG file."""
    base = base_url.rstrip("/")
    # URL-encode spaces in the category slug (should be none after normalization)
    return f"{base}/{category_slug}/{filename}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scan_icons(svg_dir: Path, base_url: str) -> list[dict]:
    icons = []
    for category_folder in sorted(svg_dir.iterdir()):
        if not category_folder.is_dir():
            continue
        cat_name = category_folder.name.lower()
        cat_slug = CATEGORY_SLUG.get(cat_name, re.sub(r"[^a-z0-9]+", "-", cat_name).strip("-"))

        for svg_file in sorted(category_folder.glob("*.svg")):
            parsed = parse_filename(svg_file.name)
            if not parsed:
                print(f"  [SKIP] Unrecognised filename: {svg_file.name}", file=sys.stderr)
                continue
            icon_id, display_name = parsed
            azure_type, terraform_types = lookup(display_name)

            icons.append(
                {
                    "id": icon_id,
                    "display_name": display_name,
                    "category": cat_name,
                    "category_slug": cat_slug,
                    "svg_path": f"svg/Icons/{cat_name}/{svg_file.name}",
                    "png_path": f"png/Icons/{cat_name}/{svg_file.stem}.png",
                    "azure_resource_type": azure_type,
                    "terraform_resource_types": terraform_types,
                    "tags": [],
                }
            )
    return icons


def apply_overrides(icons: list[dict], overrides_path: Path) -> list[dict]:
    if not overrides_path.exists():
        return icons
    with overrides_path.open(encoding="utf-8") as f:
        overrides: dict = json.load(f).get("overrides", {})

    index = {icon["id"]: icon for icon in icons}
    for icon_id, patch in overrides.items():
        if icon_id in index:
            index[icon_id].update(patch)
        else:
            print(f"  [WARN] Override for unknown id '{icon_id}'", file=sys.stderr)
    return list(index.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate icon-mapping.json from Azure SVG icons.")
    parser.add_argument("--svg-dir", default="../svg/Icons", help="Root folder containing category sub-folders of SVGs")
    parser.add_argument("--output", default="../icon-mapping.json", help="Output JSON file")
    parser.add_argument("--overrides", default="../mapping/mapping-overrides.json", help="Manual overrides JSON file")
    parser.add_argument("--base-url", default="https://raw.githubusercontent.com/OWNER/azure-icons/main/icons", help="Base URL for raw SVG files")
    args = parser.parse_args()

    svg_dir = Path(args.svg_dir).resolve()
    output_path = Path(args.output).resolve()
    overrides_path = Path(args.overrides).resolve()

    if not svg_dir.exists():
        sys.exit(f"ERROR: svg-dir not found: {svg_dir}")

    print(f"Scanning SVGs in: {svg_dir}")
    icons = scan_icons(svg_dir, args.base_url)
    print(f"  Found {len(icons)} icons")

    icons = apply_overrides(icons, overrides_path)

    mapping = {
        "version": "1.0",
        "base_url": args.base_url.rstrip("/") + "/",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(icons),
        "icons": icons,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"Written: {output_path}")

    # Compact indexes split by usage (terraform vs bicep) and format (svg vs png)
    tf_svg:    dict[str, str] = {}   # azurerm_* / azuread_* → svg_path
    tf_png:    dict[str, str] = {}   # azurerm_* / azuread_* → png_path
    bicep_svg: dict[str, str] = {}   # Microsoft.*/* (lowercase) → svg_path
    bicep_png: dict[str, str] = {}   # Microsoft.*/* (lowercase) → png_path

    for icon in icons:
        svg, png = icon["svg_path"], icon["png_path"]
        for tf in icon.get("terraform_resource_types", []):
            if tf:
                tf_svg.setdefault(tf, svg)
                tf_png.setdefault(tf, png)
        az = icon.get("azure_resource_type", "")
        if az:
            key = az.lower()
            bicep_svg.setdefault(key, svg)
            bicep_png.setdefault(key, png)

    def write_index(data: dict, name: str) -> None:
        path = output_path.parent / name
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        print(f"Written: {path}  ({path.stat().st_size // 1024} KB, {len(data)} entries)")

    write_index(tf_svg,    "icon-index-terraform-svg.json")
    write_index(tf_png,    "icon-index-terraform-png.json")
    write_index(bicep_svg, "icon-index-bicep-svg.json")
    write_index(bicep_png, "icon-index-bicep-png.json")

    # Quick stats
    with_tf = sum(1 for i in icons if i["terraform_resource_types"])
    with_az = sum(1 for i in icons if i["azure_resource_type"])
    from_seed = sum(1 for i in icons if i["display_name"].lower() in SEED_TABLE or (i["display_name"].lower().endswith("s") and i["display_name"].lower()[:-1] in SEED_TABLE))
    print(f"  Terraform mapping : {with_tf}/{len(icons)} ({100*with_tf//len(icons)}%)")
    print(f"  Azure type mapping: {with_az}/{len(icons)} ({100*with_az//len(icons)}%)")
    print(f"    - from seed table          : {from_seed}")
    print(f"    - from TERRAFORM_TO_AZURE  : {with_az - from_seed}")
    print(f"    - heuristic only (no match): {len(icons) - with_az}")


if __name__ == "__main__":
    main()
