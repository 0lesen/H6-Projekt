import urllib3
import pynetbox

nb = pynetbox.api('https://10.0.20.4', token='7ec29c2b2011f8244ff8822d7ba1f9ee3c514f10')
nb.http_session.verify = False
urllib3.disable_warnings()


### Find næste ledig port
core_device = "SITE01-CR01"
device_interfaces = nb.dcim.interfaces.filter(device="SITE-1-MSW01",cabled="False")
interface_list = []
for inf in device_interfaces:
    interface_list.append(inf)

next_interface = interface_list[0]
