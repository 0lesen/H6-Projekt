# Parameters skal udfyldes for scriptet kan køre
param (
    [string]$type = $(throw "-type is required - can be standalone OR cluster."),
    [string]$ip = $(throw "-ip is required - can be ESXi OR vCenter ip."),
    [string]$username = $(throw "-username is required."),
    [string]$password = $(throw "-password is required" )
)

# Netbox variabler bruges til at lave API kald
$api_base_url = "https://netbox01.netupnu.dk/api"
$headers = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
$headers.Add("Authorization", 'Token bbbf9087d591f7651da4b8f2ce0d13ad071927bc')
$headers.Add("Content-Type", 'application/json')
$headers.Add("Accept", 'application/json')

# Statisk variabler 
$CL= "c01"
$vlanStatusActive = "active"
$vlanStatusDeprecated = "deprecated"

$getClusterVlansDetails = (Invoke-RestMethod -SkipCertificateCheck -Uri $api_base_url/ipam/vlans/?role=$($CL) -Headers $headers).results

Function Create-Portgroups
{
    if ($type -eq "standalone" ){
        $VMHosts = Get-VMHost
    }
    elseif ($type -eq "cluster"){
        $VMHosts = Get-cluster -Name $CL | Get-VMHost
    }
    $vswitch = "vSwitch0"
    foreach ($VMhost in $VMHosts) 
    {
        Write-Host ""
        Write-Host "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Doing host: $($VMhost) ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        foreach ($vlan in $getClusterVlansDetails) 
        {
            $vlanPrefix = (Invoke-RestMethod -SkipCertificateCheck -Uri $api_base_url/ipam/prefixes/?vlan_id=$($vlan.id) -Headers $headers).results
            $vlan_id = $vlan.vid
            $vlan_data = "$($vlan.name) - $($vlanPrefix.prefix)"
            if ($vlan.status.value -eq $vlanStatusActive)
            {
                Try
                {
                $CheckPortGroupNameExist = Get-VMHost $VMhost | Get-VirtualPortGroup -Name "$($vlan_data)" -ErrorAction Stop
                Write-Host "Skipping - portgroup: $($vlan_data) already exist on host: $($VMHost)" -ForegroundColor blue
                }
                Catch
                {
                $CreatePortGroup = Get-VMHost $VMhost | Get-VirtualSwitch -name "$($vswitch)" | New-VirtualPortGroup -name "$($vlan_data)" -VLanId "$($vlan_id)"
                Write-Host "Created portgroup: $($vlan_data) on host: $($VMHost)" -ForegroundColor green
                }
            }
            if ($vlan.status.value -eq $vlanStatusDeprecated)
            {
                Try
                {
                $CheckPortGroupNameExist = Get-VMHost $VMhost | Get-VirtualPortGroup -Name "$($vlan_data)" -ErrorAction Stop
                    Try
                    {
                    $DeletePortGroup = Get-VMHost $VMhost | Get-VirtualPortGroup -Name "$($vlan_data)" | Remove-VirtualPortGroup -Confirm:$false -ErrorAction Stop
                    Write-Host "Deleted portgroup: $($vlan_data) on host: $($VMhost)" -ForegroundColor yellow
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
if ($type -eq "standalone")
{
    $StartConnection = Connect-VIServer -Server $ip -User $username -Password $password
    Write-Host "Connected to host: $($ip)"
    Create-Portgroups
} 
elseif ($type -eq "cluster")
{ 
    $StartConnection = Connect-VIServer -Server $ip -User $username -Password $password
    Write-Host "Connected to vCenter: $($ip)"
    Create-Portgroups
}
else {
     Write-Host "ERROR - Cant connect to host"
}
