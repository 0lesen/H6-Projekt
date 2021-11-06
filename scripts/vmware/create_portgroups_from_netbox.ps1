# Parameters skal udfyldes for scriptet kan køre
param (
    [string]$type = $(throw "-type is required - can be standalone OR cluster."),
    [string]$ip = $(throw "-ip is required - can be ESXi OR vCenter ip."),
    [string]$username = $(throw "-username is required."),
    [string]$password = $(throw "-password is required" )
)

# Netbox variabler bruges til at lave API kald
$api_base_url = "https://10.0.20.4/api"
$headers = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
$headers.Add("Authorization", 'Token 7ec29c2b2011f8244ff8822d7ba1f9ee3c514f10')
$headers.Add("Content-Type", 'application/json')
$headers.Add("Accept", 'application/json')

# Statisk variabler 
$cluster_name = "cluster01"
$vlanStatusActive = "active"
$vlanStatusDeprecated = "deprecated"


$getClusterVlansDetails = (Invoke-RestMethod -SkipCertificateCheck -Uri $api_base_url/ipam/vlans/?role=$($cluster_name) -Headers $headers).results












Function Create-Portgroups
{
    $VMHosts = Get-VMHost
    $vswitch = "vSwitch0"
#    $getClusterVlansDetails = (Invoke-RestMethod -SkipCertificateCheck -Uri $api_base_url/ipam/vlans/?role=$($cluster_name) -Headers $headers).results
    foreach ($VMHost in $VMHosts) 
    {
        foreach ($vlan in $getClusterVlansDetails) 
        {
            $vlanPrefix = (Invoke-RestMethod -SkipCertificateCheck -Uri $api_base_url/ipam/prefixes/?vlan_id=$($vlan.id) -Headers $headers).results
            $vlan_id = $vlan.vid
            $vlan_data = "$($vlan.name) - $($vlanPrefix.prefix)"
            if ($vlan.status.value -eq $vlanStatusActive)
            {
                Try
                {
                $CheckPortGroupNameExist = Get-VMHost -name "$($VMhost)" | Get-VirtualPortGroup -Name "$($vlan_data)" -ErrorAction Stop
                Write-Host "Skipping - portgroup: $($vlan_data) already exist on host: $($VMHost)" -ForegroundColor blue
                }
                Catch
                {
                $CreatePortGroup = Get-VMHost -name "$($VMhost)" | Get-VirtualSwitch -name "$($vswitch)" | New-VirtualPortGroup -name "$($vlan_data)" -VLanId "$($vlan_id)"
                Write-Host "Created portgroup: $($vlan_data) on host: $($VMHost)" -ForegroundColor green
                }
            }
            elseif ($vlan.status.value -eq $vlanStatusDeprecated)
            {
                Try
                {
                $CheckPortGroupNameExist = Get-VMHost -name "$($VMhost)" | Get-VirtualPortGroup -Name "$($vlan_data)" -ErrorAction Stop
                    Try
                    {
                    $DeletePortGroup = Get-VMHost | Get-VirtualPortGroup -Name "$($vlan_data)" | Remove-VirtualPortGroup -Confirm:$false -ErrorAction Stop
                    Write-Host "Deleted portgroup: $($vlan_data) on host: $($VMHost)" -ForegroundColor yellow
                    }
                    Catch
                    {
                    Write-Host "ERROR when deleting portgroup: $($vlan_data)" -ForegroundColor red
                    }
                }
                Catch
                {
                Write-Host "Try deleting portgroup: ($vlan_data) - but it does not exist on host: $($VMHost)" -ForegroundColor red
                }
            }
        }
	}
    Disconnect-viserver -Server * -Confirm:$false
}



#if ($confirmation -eq "n")

if ($type -eq "standalone")
{
    #$ES = Read-Host "Enter standalone ESXi ip: "

    $StartConnection = Connect-VIServer -Server $ip -User $username -Password $password
    Write-Host "Connected to host: $($ip)"
    Create-Portgroups
} 
elseif ($type -eq "cluster")
{ 
    #$VC = Read-Host "Enter vCenter name: "
    $StartConnection = Connect-VIServer -Server $ip -User $username -Password $password
    Write-Host "Connected to vCenter: $($ip)"
    $CL = Read-Host " Enter Cluster name: "
    $VMHosts = Get-cluster "$CL | Get-VMHost"
    Create-Portgroups
}
else {
     Write-Host "You fucked up"
}
