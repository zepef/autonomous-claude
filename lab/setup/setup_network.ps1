# Setup VirtualBox Host-Only Network for AI-Defender Lab
# Run as Administrator

$VBoxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"

Write-Host "=== AI-Defender Lab Network Setup ===" -ForegroundColor Cyan

# Check if VirtualBox is installed
if (-not (Test-Path $VBoxManage)) {
    Write-Host "ERROR: VirtualBox not found. Please install it first." -ForegroundColor Red
    Write-Host "See: install_virtualbox.md" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[1/4] Creating Host-Only Network..." -ForegroundColor Yellow

# Create host-only network
$networkName = "AI-Defender-Lab"

# List existing host-only networks
$existingNetworks = & $VBoxManage list hostonlyifs 2>$null

if ($existingNetworks -match "AI-Defender-Lab") {
    Write-Host "Network already exists, reconfiguring..." -ForegroundColor Yellow
} else {
    # Create new host-only adapter
    & $VBoxManage hostonlyif create
}

Write-Host "`n[2/4] Configuring Network Adapter..." -ForegroundColor Yellow

# Get the name of the host-only adapter (usually "VirtualBox Host-Only Ethernet Adapter")
$adapters = & $VBoxManage list hostonlyifs
$adapterName = ($adapters | Select-String "Name:" | Select-Object -First 1) -replace "Name:\s+", ""

if ($adapterName) {
    # Configure the adapter
    & $VBoxManage hostonlyif ipconfig $adapterName --ip 10.0.0.1 --netmask 255.255.255.0
    Write-Host "Configured adapter: $adapterName" -ForegroundColor Green
    Write-Host "  Host IP: 10.0.0.1" -ForegroundColor Green
    Write-Host "  Subnet:  255.255.255.0" -ForegroundColor Green
} else {
    Write-Host "WARNING: Could not find host-only adapter. You may need to configure manually." -ForegroundColor Yellow
}

Write-Host "`n[3/4] Disabling DHCP Server..." -ForegroundColor Yellow

# Disable DHCP (we use static IPs)
& $VBoxManage dhcpserver remove --netname "HostInterfaceNetworking-$adapterName" 2>$null
Write-Host "DHCP disabled (using static IPs)" -ForegroundColor Green

Write-Host "`n[4/4] Verifying Configuration..." -ForegroundColor Yellow

# Show final configuration
& $VBoxManage list hostonlyifs

Write-Host "`n=== Network Setup Complete ===" -ForegroundColor Cyan
Write-Host @"

Network Configuration:
  Name:    AI-Defender-Lab
  Host IP: 10.0.0.1
  Subnet:  10.0.0.0/24

Planned VM IPs:
  Kali (Attacker):  10.0.0.10
  DVWA (Target):    10.0.0.20
  Honeypot (Host):  10.0.0.1:5000

Next Steps:
  1. Download Kali VM image
  2. Run setup_kali.ps1
  3. Run setup_dvwa.ps1

"@ -ForegroundColor White
