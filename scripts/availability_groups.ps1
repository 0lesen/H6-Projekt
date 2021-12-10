$server1 = 'SQL01'
$server2 = 'SQL02'
$share = '\\DC01\backup'
$IP = '10.0.21.23'
$Subnet = '255.255.255.0'
$serviceaccount = 'netupnu\gMSASQL$'
$AGName = 'SQLAG'
$AGListener = 'SQLAG'

#Variable for an array object of Availability Group replicas
$replicas = @()

#Variable for T-SQL command
$createLogin = "CREATE LOGIN [$serviceaccount] FROM WINDOWS; " 
$grantConnectPermissions = "GRANT CONNECT ON ENDPOINT::Endpoint_AG TO [$serviceaccount];"


#List all of the WSFC nodes; all SQL Server instances run DEFAULT instances
foreach($node in Get-ClusterNode)
{
    #Step 1: Enable SQL Server Always On High Availability feature
    Enable-SqlAlwaysOn -ServerInstance $node -Force 

    #Step 2: Create the Availability Group endpoints
    New-SqlHADREndpoint -Path "SQLSERVER:\SQL\$node\Default" -Name "Endpoint_AG" -Port 5022 -EncryptionAlgorithm Aes -Encryption Required 

    #Step 3: Start the Availability Group endpoint
    Set-SqlHADREndpoint -Path "SQLSERVER:\SQL\$node\Default\Endpoints\Endpoint_AG" -State Started
   
    #Step 4: Create login and grant CONNECT permissions to the SQL Server service account
    Invoke-SqlCmd -Server $node.Name -Query $createLogin
    Invoke-SqlCmd -Server $node.Name -Query $grantConnectPermissions 

    #Step 5: Create the Availability Group replicas as template objects
    $replicas += New-SqlAvailabilityReplica -Name $node -EndpointUrl "TCP://$node.TEST.local:5022" -AvailabilityMode "SynchronousCommit" -FailoverMode "Automatic" -AsTemplate -Version 15 
}

#Step 6: Create database on both servers
Invoke-sqlcmd -server $server1 -Query "Create database Test" 
Backup-SqlDatabase  -Database "Test"  -BackupFile "$share\test.bak" -ServerInstance $server1 
  
Backup-SqlDatabase  -Database "Test"   -BackupFile "$share\test.log" -ServerInstance $server1  -BackupAction Log   
  
# Restore the database and log on the secondary (using NO RECOVERY)  
Restore-SqlDatabase   -Database "Test"   -BackupFile "$share\test.bak" -ServerInstance $server2   -NoRecovery  
  
Restore-SqlDatabase   -Database "Test" -BackupFile "$share\test.log" -ServerInstance $server2  -RestoreAction Log -NoRecovery  

#Step 7: Create the Availability Group, replace SERVERNAME with the name of the primary replica instance
New-SqlAvailabilityGroup -InputObject $server1 -Name "$AGName" -AvailabilityReplica $replicas -Database @("Test")

#Step 8: Join the secondary replicas and databases to the Availability Group
Join-SqlAvailabilityGroup -Path "SQLSERVER:\SQL\$server2\Default" -Name "$AGName"
Add-SqlAvailabilityDatabase -Path "SQLSERVER:\SQL\$server2\Default\AvailabilityGroups\$AGName" -Database "Test" 

#Step 9: Create the Availability Group listener name (on the primary replica) 
New-SqlAvailabilityGroupListener -Name $AGListener -staticIP "$IP/$subnet" -Port 1433 -Path "SQLSERVER:\Sql\$server1\DEFAULT\AvailabilityGroups\$AGName"
