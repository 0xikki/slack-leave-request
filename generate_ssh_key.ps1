# Generate SSH key pair
$keyFile = "vultr_ssh_key"

# Remove existing key files if they exist
if (Test-Path $keyFile) {
    Remove-Item $keyFile -Force
}
if (Test-Path "$keyFile.pub") {
    Remove-Item "$keyFile.pub" -Force
}

# Create the .ssh directory if it doesn't exist
$sshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
}

# Generate the key using ssh-keygen
$process = Start-Process -FilePath "ssh-keygen" -ArgumentList "-t", "rsa", "-b", "4096", "-f", "$keyFile", "-N", "`"`"" -NoNewWindow -PassThru -Wait

if ($process.ExitCode -eq 0) {
    Write-Host "SSH key pair generated successfully!"
    Write-Host "Private key: $keyFile"
    Write-Host "Public key: $keyFile.pub"
    
    # Display the public key
    Write-Host "`nPublic Key content (copy this to Vultr):"
    Get-Content "$keyFile.pub"
} else {
    Write-Error "Failed to generate SSH key pair"
    exit 1
} 