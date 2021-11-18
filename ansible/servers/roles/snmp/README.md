
Requires variables "community", "location" and extend. They should be defined in host_vars file
example:
path/ansible/host_vars/<hostname>.yml

snmp:
  community: "dk"
  location: "some place"
  extend: [DHCP, NTP]

