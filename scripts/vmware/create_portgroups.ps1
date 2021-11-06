param (
    [string]$type = $(throw "-type is required - can be standalone OR cluster."),
    [string]$ip = $(throw "-ip is required - can be ESXi OR vCenter ip."),
    [string]$username = $(throw "-username is required."),
    [string]$password = $(throw "-password is required" )
       # [string]$password = $( Read-Host -asSecureString "Input password" )
)

#$confirmation = Read-Host "Create portgroup on Cluster? [y/n]"


Function Create-Portgroups
{
    $pgs = import-csv C:\Users\mbo\Desktop\portgroups.csv
    
    $VMHosts = Get-VMHost
    foreach ($VMHost in $VMHosts) 
    {
        foreach ( $pg in $pgs) 
        {
            Try
            {
            $CheckPortGroupNameExist = Get-VMHost -name $VMhost | Get-VirtualPortGroup -Name "$($pg.name)" -ErrorAction Stop
            Write-Host "Skipping - portgroup: $($pg.name) already exist on host: $($VMHost)"
            }
            Catch
            {
            $CreatePortGroup = Get-VMHost -name $VMhost | Get-VirtualSwitch -name $pg.vswitch | New-VirtualPortGroup -name $pg.name -VLanId $pg.vlanid
            Write-Host "Created portgroup: $($pg.name) on host: $($VMHost)"
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