import pynetbox
import urllib3
import ipaddress
import json
import requests
import os




# Netbox information
nb = pynetbox.api( 'https://netbox01.netupnu.dk', token='bbbf9087d591f7651da4b8f2ce0d13ad071927bc')
nb.http_session.verify = False
urllib3.disable_warnings()
# LibreNMS information
api_librenms_url = 'http://nms01.netupnu.dk/api/v0/devices'
headers = {'X-Auth-Token': 'ddfe52cc2bfbdef20ac402f0e4cb863a'}

devices_list = []
type_devices = nb.dcim.devices.all()
devices_list.append(type_devices)
type_vms = nb.virtualization.virtual_machines.all()
devices_list.append(type_vms)

def get_devices_information():
    alert_list = []
    add_devices_list = []
    for device_type in devices_list:
        for device in device_type:
            if device.primary_ip and device.custom_fields["snmp"] == True:
                get_device_ip_address = ipaddress.IPv4Interface(device.primary_ip)
                if device.custom_fields["community"] != "NULL":
                    tmp = {}
                    tmp["hostname"] = device.name
                    tmp["ip"] = get_device_ip_address.ip
                    tmp["community"] = device.custom_fields["community"]
                    add_devices_list.append(tmp)
            else:
                tmp = {}
                tmp["hostname"] = device.name
                tmp["snmp"] = device.custom_fields["snmp"]
                alert_list.append(tmp)
    cant_add_devices(alert_list)
    add_devices_to_nms(add_devices_list)

def cant_add_devices(alert_list):
    for device in alert_list:
        print ("Device: %s has no IP address and/or snmp status is: %s" % (device["hostname"], device["snmp"]))


def add_devices_to_nms(add_devices_list):
    for device in add_devices_list:
        ### Building data as json format with vaiables from betbox
        pre_data = json.dumps({"hostname":"%s","version":"v2c","community":"%s"})
        data = (pre_data % (device["ip"], device["community"]))
        try:
            send_data = requests.post(url = api_librenms_url, data = data, headers=headers )
            print (send_data.content)
            #send_data.raise_for_status()
        except Exception as err:
            print (err)


get_devices_information()
