import urllib3
import pynetbox

nb = pynetbox.api('https://10.0.20.4', token='7ec29c2b2011f8244ff8822d7ba1f9ee3c514f10')
nb.http_session.verify = False
urllib3.disable_warnings()

#### Bruger input til nyt site
new_site_name_input = str(input("Site name: "))
new_site_id_input = int(input("Site ID: "))
new_site_full_name = str(new_site_name_input).upper() + "-" + str(new_site_id_input)

### Statiske variabler
new_site_tag = "site"
new_site_prefixes_tag = "site-prefixes"
##new_site_prefix_length = 21
site_vlans_data = [
        {"name": "MGMT", "id": 10, "prefix": 24},
        {"name": "CLIENTS", "id": 20, "prefix": 24},
        {"name": "IOT", "id": 30, "prefix": 24},
        {"name": "GUEST", "id": 40, "prefix": 24}
        ]
new_site_switch_type_id = 3 #"c3660"
new_site_switch_role_id = 6 #"multilayer-switch"
new_site_switch_platform_id = 5 #"ios"
new_site_switch_uplink_interface = "gigabitethernet1/0/24"

### Opret nyt site
create_new_site = nb.dcim.sites.create({
    "name": "{}".format(new_site_full_name),
    "slug": "{}".format(new_site_full_name.lower()),
    "tags": [
        {
            "name": "{}".format(new_site_tag)
        }
]})

### Opret vlan gruppe og tilføj til sitet
create_new_vlan_group = nb.ipam.vlan_groups.create({
    "name": "{}-VLANS".format(new_site_full_name),
    "slug": "{}-vlans".format(new_site_full_name.lower()),
    "scope_type": "dcim.site",
    "scope_id": "{}".format(create_new_site.id)
})

### Opret vlans og tilføj til vlan gruppen og sitet
for vlan in site_vlans_data:
    vlan_name = vlan["name"]
    vlan_id = vlan["id"]
    create_new_vlans = nb.ipam.vlans.create({
        "name": "{}-{}".format(new_site_full_name, vlan_name),
        "vid": "{}".format(vlan_id),
        "group": "{}".format(create_new_vlan_group.id),
        "site": "{}".format(create_new_site.id)
})


### Opret nyt site ledigt prefix
site_prefixes = nb.ipam.prefixes.get(tag=new_site_prefixes_tag)
create_new_prefix = site_prefixes.available_prefixes.create({
            "prefix_length": 21,
            "site": "{}".format(create_new_site.id)
})

### Opret prefixes for nye vlan
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    vlan_prefix = vlan["prefix"]
    prefixes_in_new_site = nb.ipam.prefixes.get(prefix=create_new_prefix)
    create_new_vlan_prefix = prefixes_in_new_site.available_prefixes.create({
        "prefix_length": 24,
        "site": "{}".format(create_new_site.id),
        "vlan":
        {
            "name": "{}-{}".format(new_site_full_name, vlan_name)
        }
})

### Opret lag 3 switch på sitet
create_new_device = nb.dcim.devices.create({
    "name": "{}-MSW01".format(new_site_full_name),
    "device_type": "{}".format(new_site_switch_type_id),
    "device_role": "{}".format(new_site_switch_role_id),
    "platform": "{}".format(new_site_switch_platform_id),
    "site": "{}".format(create_new_site.id)
})

## Opret vlan interfaces på switchen 
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    create_new_interfaces = nb.dcim.interfaces.create({
        "device": "{}".format(create_new_device.id),
        "name": "vlan{}".format(vlan_id),
        "description": "{}-{}".format(new_site_full_name, vlan_name),
        "type": "virtual"
})

### Opret gateway ip for nye vlan
for vlan in site_vlans_data:
    vlan_id = vlan["id"]
    vlan_name = vlan["name"]
    vlan_interface_name = "vlan" + str(vlan["id"])
    prefixes_in_new_vlan = nb.ipam.prefixes.get(site=new_site_full_name.lower(), vlan_vid=vlan_id)
    get_vlan_interface_id = nb.dcim.interfaces.get(site=new_site_full_name.lower(), device=create_new_device.name, name=vlan_interface_name)
    create_vlan_gateway_ip= prefixes_in_new_vlan.available_ips.create({
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": "{}".format(get_vlan_interface_id.id)
})
