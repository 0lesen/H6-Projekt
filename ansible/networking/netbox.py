import pynetbox
import urllib3
import ipaddress
import json
import requests
import os
from jinja2 import Template

# Netbox information
nb = pynetbox.api('https://netbox.netupnu.dk', token='bbbf9087d591f7651da4b8f2ce0d13ad071927bc')
nb.http_session.verify = False
urllib3.disable_warnings()
#netbox_inventory_file = 'test_inventory'
dc_vlans_group = "dc01-vlans"


#def get_devices_platform():
#    print("Getting devices platforms from NetBox... ", end="", flush=True)
#    devices_platform = nb.dcim.platforms.all()
#    data_list = ""
#    for platform in devices_platform:
#        devices_list = nb.dcim.devices.filter(platform=platform.slug)
#
#        tm = Template(
#"""[{{platform.slug}}]{% for device in devices_list %}
#{{ device.name }}{% endfor %}
#
#
#""")
#        data = tm.render(platform=platform, devices_list=devices_list)
#        data_list += data
#
#    print ("Done")
#    get_devices_roles(data_list)
#
#def get_devices_roles(data_list):
#    print("Getting devices roles from NetBox... ", end="", flush=True)
#    devices_roles = nb.dcim.device_roles.all()
#    for device_role in devices_roles:
#        devices_list = nb.dcim.devices.filter(role=device_role.slug)
#        tm = Template(
#"""[{{device_role.slug}}]{% for device in devices_list %}
#{{ device.name }}{% endfor %}
#
#
#""")
#        data = tm.render(device_role=device_role, devices_list=devices_list)
#        data_list += data
#    print ("Done")
#    create_inventory(data_list)

#def create_inventory(data_list):
#    print ("Creating inventory file: %s from netbox... " % netbox_inventory_file, end="", flush=True)
#    with open(netbox_inventory_file, 'w') as f:
#        f.write(data_list)
#        f.close()
#    print ("Done")

def get_devices_information():
    print("Getting devices & interfaces information from NetBox... ", end="", flush=True)
    data_list = ""
    devices_list = nb.dcim.devices.filter(role=['switch'])
    print ("Done")
    for device in devices_list:
        if device.primary_ip:
            device_ip = ipaddress.IPv4Interface(device.primary_ip)
        else:
            device_ip = ""
        interfaces = nb.dcim.interfaces.filter(device_id=device.id)
        site = nb.dcim.sites.get(device.site.id)
        dc_vlans = nb.ipam.vlans.filter(group=dc_vlans_group)
        tm = Template(
"""ansible_host: {% if device_ip %}{{device_ip.ip}}{% endif %}
ansible_hostname: {{device.name}}

vlans:{% for vlan in dc_vlans %}
  - name: {{ vlan.name }}
    id: {{ vlan.vid }}
    state: {{ vlan.status }}{% endfor %}




interfaces:{% for interface in interfaces %}
  - name: "{{ interface.name }}"
    config:{% for tag in interface.tags %}
      - {{ tag.name }}{% endfor %}{% if interface.mode %}{% if interface.mode.label == 'Access'%}{% if interface.untagged_vlan.vid %}
    untagged_vlan:
      name: "{{ interface.untagged_vlan.name }}"
      id: {{ interface.untagged_vlan.vid }}{% endif %}{% elif interface.mode.label == 'Tagged' %}{% if interface.tagged_vlans %}
    tagged_vlans:{% for vlan in interface.tagged_vlans %}
      - name: "{{ vlan.name }}"
        id: {{ vlan.vid }}{% endfor %}{% if interface.untagged_vlan %}
    untagged_vlan:
      name: "{{ interface.untagged_vlan.name }}"
      id: {{ interface.untagged_vlan.vid }}{% endif %}{% endif %}{% endif %}{% endif %}{% endfor %}
""")

        data = tm.render(device_ip = device_ip, device = device, interfaces = interfaces, site = site, dc_vlans = dc_vlans)
        create_host_vars(device, data)
        #data_list += data



def create_host_vars(device, data):
    filename = ("host_vars/%s.yml" % device.name)
    print("Creating host_vars/%s.yml from NetBox data... " % device.name, end="", flush=True)
    with open(filename, "w+") as f:
        f.write(data)
        f.close()
    print ("Done")
#        if device.primary_ip:
#            device_ip_address = ipaddress.IPv4Interface(device.primary_ip)
#            print 


#def get_core_vlans():
#    print("Getting core vlans from NetBox... ", end="", flush=True)
#    core_vlans = nb.ipam.vlans.filter(group=vlan_group)
#    tm = Template(
#"""core_vlans:{% for vlan in core_vlans %}
#  - name: {{ vlan.name }}
#    id: {{ vlan.vid }}{% endfor %}
#""")
#    data = tm.render(core_vlans=core_vlans)
#    print ("Done")
#    create_vlans(data)
#
#def create_vlans(data):
#    filename = ("vars/%s.yml" % vlan_group)
#    print ("Creating vlans file: %s from netbox... " % filename, end="", flush=True)
#    with open(filename, 'w') as f:
#        f.write(data)
#        f.close()
#    print ("Done")




if __name__ == "__main__":
#    get_devices_platform()
    get_devices_information()
#    get_core_vlans()
