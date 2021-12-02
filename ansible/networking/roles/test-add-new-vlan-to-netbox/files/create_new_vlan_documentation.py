import urllib3
import pynetbox

import argparse

# Parser
parser = argparse.ArgumentParser(description='Opret ny vlan i netbox')

# Argumenter
parser.add_argument('-name', action='store', type=str, required=True, help='Navn på vlan')
parser.add_argument('-id', action='store', type=int, required=True, help='Id på vlan')
parser.add_argument('-subnet', action='store', type=str, required=True, help='Vlan subnet')
parser.add_argument('-prefix', action='store', type=int, required=True, help='Subnet prefix')

# Execute the parse_args() method
args = parser.parse_args()

nb = pynetbox.api('https://netbox.netupnu.dk', token='bbbf9087d591f7651da4b8f2ce0d13ad071927bc')
nb.http_session.verify = False
urllib3.disable_warnings()

### Statiske variabler
dc_vlans_group_name = "DC01-VLANS"
dc_site_name = "DC01"
new_vlan_tag = "CREATE_NEW_CLUSTER_VLAN"
dc_prefixes_tag = "DC-PREFIXES"
dc_vlan_role = "C01"
gateway_name = "FW01"
interface_downlink_tag = "DOWNLINK"
interface_uplink_tag = "UPLINK"
interface_esxi_tag = "ESXI"

### Hent informationer fra netbox
dc_site_info = nb.dcim.sites.get(name=dc_site_name)
dc_vlans_group_info = nb.ipam.vlan_groups.get(name=dc_vlans_group_name)
dc_vlan_role_info = nb.ipam.roles.get(name=dc_vlan_role)
gateway_info = nb.dcim.devices.get(name=gateway_name)


### Opret nyt vlan og tilføj til vlan gruppen og sitet
create_new_vlan = nb.ipam.vlans.create({
    "name": "{}".format(args.name),
    "vid": "{}".format(args.id),
    "group": "{}".format(dc_vlans_group_info.id),
    "site": "{}".format(dc_site_info.id),
    "role": dc_vlan_role_info.id,
    "tags": [
        {
            "name": "{}".format(new_vlan_tag)
        }
    ]
})

### Opret prefix for nyt vlan
dc_prefixes = nb.ipam.prefixes.get(tag=dc_prefixes_tag.lower())
create_new_vlan_prefix = nb.ipam.prefixes.create({
    "prefix": "{}/{}".format(args.subnet, args.prefix),
    "site": "{}".format(dc_site_info.id),
    "vlan": create_new_vlan.id
})


## Opret vlan interface på firewall 
create_new_interface = nb.dcim.interfaces.create({
    "device": "{}".format(gateway_info.id),
    "name": "{}".format(create_new_vlan.name),
    "type": "virtual"
})


### Opret gateway ip for nye vlan
prefix_in_new_vlan = nb.ipam.prefixes.get(site=dc_site_info.name.lower(), vlan_vid=create_new_vlan.vid)
get_vlan_interface_id = nb.dcim.interfaces.get(site=dc_site_info.name.lower(), device=gateway_info.name, name=create_new_interface.name)
create_vlan_gateway_ip= prefix_in_new_vlan.available_ips.create({
        "assigned_object_type": "dcim.interface",
        "assigned_object_id": "{}".format(get_vlan_interface_id.id)
})


### Tag nyt vlan på UPLINK og DOWNLINK interfaces på gateway
all_interfaces= []
get_downlink_interfaces = nb.dcim.interfaces.filter(site=dc_site_info.name.lower(), tag=interface_downlink_tag.lower())
all_interfaces.append(get_downlink_interfaces)
get_uplink_interfaces = nb.dcim.interfaces.filter(site=dc_site_info.name.lower(), tag=interface_uplink_tag.lower())
all_interfaces.append(get_uplink_interfaces)
get_esxi_interfaces = nb.dcim.interfaces.filter(site=dc_site_info.name.lower(), tag=interface_esxi_tag.lower())
all_interfaces.append(get_esxi_interfaces)

for interfaces in all_interfaces:
    for interface in interfaces:
        interface.tagged_vlans.append(create_new_vlan.id)
        interface.save()
