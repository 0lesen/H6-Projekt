import urllib3
import pynetbox
import argparse

# Parser
parser = argparse.ArgumentParser(description='Opret nyt site i Netbox')

# Argumenter
parser.add_argument('-town', action='store', type=str, required=True, help='Site by (AAR): ')
parser.add_argument('-id', action='store', type=str, required=True, help='Site ID (01): ')
parser.add_argument('-core_id', action='store', type=str, required=True, help='Core device ID fra Netbox')
parser.add_argument('-if_id', action='store', type=str, required=True, help='Næste ledig interface ID på core fra Netbox')

# Execute the parse_args() method
args = parser.parse_args()


nb = pynetbox.api('https://netbox01.netupnu.dk', token='bbbf9087d591f7651da4b8f2ce0d13ad071927bc')
nb.http_session.verify = False
urllib3.disable_warnings()

#### Ensartet Navngivning
new_site_name_input = str(args.town)
new_site_id_input = str(args.id)
core_id = str(args.core_id)
core_interface_id = str(args.if_id)
new_site_full_name = str(new_site_name_input).upper() + "-S" + str(new_site_id_input)
new_site_full_name_slug = str(new_site_name_input).upper() + "_s" + str(new_site_id_input)

### Statiske variabler
dhcp_relay_tag = "DHCP-RELAY"
ospf_tag = "OSPF"
site_dhcp_tag = "SITE-DHCP"
new_site_tag = "SITE"
new_site_prefixes_tag = "site-prefixes"
new_site_prefix_length = 21
site_vlans_data = [
        {"name": "MGMT1", "id": 1099, "prefix": 24, "mgmt": True},
        {"name": "CLIENTS1", "id": 1010, "prefix": 24, "mgmt": False},
        {"name": "IOT1", "id": 1020, "prefix": 24, "mgmt": False},
        {"name": "GUEST1", "id": 1030, "prefix": 24, "mgmt": False}
        ]
new_site_switch_type_id = 1 #"WS-C2960S-24TS-S"
new_site_switch_role_id = 1 #"site-switch"
new_site_switch_platform_id = 1 #"ios"
new_site_switch_uplink_interface_name = "GigabitEthernet0/24"

### Hent core info fra Netbox
core_device_info = nb.dcim.devices.get(id=int(core_id))
core_interface_info = nb.dcim.interfaces.get(id=int(core_interface_id))

### Opret nyt site
print ("Opretter site: {}".format(new_site_full_name))
create_new_site = nb.dcim.sites.create({
    "name": "{}".format(new_site_full_name),
    "slug": "{}".format(new_site_full_name_slug.lower()),
    "tags": [
        {
            "name": "{}".format(new_site_tag)
        }
]})

### Opret vlan gruppe og tilføj til sitet
print ("Opretter vlan gruppe: {}-VLANS".format(new_site_full_name))
create_new_vlan_group = nb.ipam.vlan_groups.create({
    "name": "{}-VLANS".format(new_site_full_name),
    "slug": "{}-vlans".format(new_site_full_name_slug.lower()),
    "scope_type": "dcim.site",
    "scope_id": "{}".format(create_new_site.id)
})

### Opret vlans og tilføj til vlan gruppen og sitet
print ("Opretter vlans på site: {}".format(create_new_site.name))
for vlan in site_vlans_data:
    vlan_name = vlan["name"]
    vlan_id = vlan["id"]
    create_new_vlans = nb.ipam.vlans.create({
        "name": "{}-{}".format(new_site_full_name, vlan_name),
        "vid": "{}".format(vlan_id),
        "group": "{}".format(create_new_vlan_group.id),
        "site": "{}".format(create_new_site.id)
})


### Opret ledigt prefix til nyt site
print ("Opretter præfix til site: {}".format(create_new_site.name))
site_prefixes = nb.ipam.prefixes.get(tag=new_site_prefixes_tag)
create_new_prefix = site_prefixes.available_prefixes.create({
            "prefix_length": new_site_prefix_length,
            "site": "{}".format(create_new_site.id)
})

### Opret prefixes for nye vlan
print ("Opretter præfix per vlan")
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    vlan_prefix = vlan["prefix"]
    prefixes_in_new_site = nb.ipam.prefixes.get(prefix=create_new_prefix)
    create_new_vlan_prefix = prefixes_in_new_site.available_prefixes.create({
        "prefix_length": vlan_prefix,
        "site": "{}".format(create_new_site.id),
        "vlan":
        {
            "name": "{}-{}".format(new_site_full_name, vlan_name)
        },
        "tags": [
        {
            "name": "{}".format(site_dhcp_tag)
        }]

})

### Opret switch på sitet
print ("Opretter site switch på: {}".format(create_new_site.name))
create_new_device = nb.dcim.devices.create({
    "name": "{}-ASW01".format(new_site_full_name),
    "device_type": "{}".format(new_site_switch_type_id),
    "device_role": "{}".format(new_site_switch_role_id),
    "platform": "{}".format(new_site_switch_platform_id),
    "site": "{}".format(create_new_site.id)
})

### Opret mgmt vlan på switchen 
print ("Opretter mgmt vlan på: {}".format(create_new_device.name))
for vlan in site_vlans_data:
    if vlan["mgmt"] == True:
        vlan_id = vlan["id"]
        vlan_name = vlan["name"]
        create_mgmt_interface = nb.dcim.interfaces.create({
            "device": "{}".format(create_new_device.id),
            "name": "vlan{}".format(vlan_id),
            "description": "{}-{}".format(new_site_full_name, vlan_name),
            "type": "virtual"
})

### Tag vlans på uplink interface  
print ("Opretter vlan tags på uplink interfacet: {}".format(new_site_switch_uplink_interface_name))
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    vlan_info = nb.ipam.vlans.get(site_id=create_new_site.id, vid=vlan_id)
    get_uplink_interface = nb.dcim.interfaces.get(device_id=create_new_device.id, name=new_site_switch_uplink_interface_name)
    get_uplink_interface.mode = "tagged"
    get_uplink_interface.save()
    get_uplink_interface.tagged_vlans.append(vlan_info.id)
    get_uplink_interface.save()

## Opret sub interfaces på coren 
print ("Opretter subinterfaces på: {}".format(core_device_info.name))
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    create_new_interfaces = nb.dcim.interfaces.create({
        "device": int(core_id),
        "name": "{}.{}".format(core_interface_info.name, vlan_id),
        "parent" : int(core_interface_info.id),
        "type": "virtual",
        "tags": [
            {
                "name": "{}".format(dhcp_relay_tag)
            }
        ]
})

### Opret gateway ip for nye subinterfaces
print ("Opretter gateway IP på subinterfaces")
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    sub_interface_name = "{}.{}".format(core_interface_info.name, vlan_id)
    prefixes_in_new_vlan = nb.ipam.prefixes.get(site=new_site_full_name_slug.lower(), vlan_vid=vlan_id)
    get_sub_interface_info = nb.dcim.interfaces.get(device_id=int(core_id), name=sub_interface_name)
    create_vlan_gateway_ip= prefixes_in_new_vlan.available_ips.create({
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": get_sub_interface_info.id
})

### Opret OSPF tag på nye sub interfaces
print ("Opretter OSPF tag på sub interfaces")
#get_interface.save()
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    sub_interface_name = "{}.{}".format(core_interface_info.name, vlan_id)
    get_sub_interface = nb.dcim.interfaces.get(device_id=int(core_id), name=sub_interface_name)
    get_sub_interface.tags.append({"name": "{}".format(ospf_tag)})
    get_sub_interface.save()

### Opret management ip på mgmt vlan på ny switch
#print ("Opretter mgmt ip på mgmt vlan på switch: {}".format(create_new_device.name))
for vlan in site_vlans_data:
    if vlan["mgmt"] == True:
        vlan_id = vlan["id"]
        vlan_name = vlan["name"]
        prefixes_in_new_vlan = nb.ipam.prefixes.get(site=new_site_full_name_slug.lower(), vlan_vid=vlan_id)
        create_vlan_ip= prefixes_in_new_vlan.available_ips.create({
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": create_mgmt_interface.id
        })
        get_device_info = nb.dcim.devices.get(id=create_new_device.id)
        get_device_info.primary_ip4 = create_vlan_ip.id
        get_device_info.save()

### Forbind kabel mellem core og site
print("Opretter kabel mellem {} og {}".format(core_device_info.name, create_new_device.name))
get_new_site_switch_uplink_info = nb.dcim.interfaces.get(device_id=create_new_device.id, name=new_site_switch_uplink_interface_name)
create_cable = nb.dcim.cables.create({
        "termination_a_type": "dcim.interface",
        "termination_a_id": int(core_interface_id),
        "termination_b_type": "dcim.interface",
        "termination_b_id": get_new_site_switch_uplink_info.id
})
