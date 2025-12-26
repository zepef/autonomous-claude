# Setup DVWA (Damn Vulnerable Web Application) VM
# Lightweight Ubuntu + Docker approach
# Run as Administrator

$VBoxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$LabDir = Split-Path -Parent $PSScriptRoot
$VMDir = "$LabDir\vms"

Write-Host "=== DVWA Target VM Setup ===" -ForegroundColor Cyan

# Check for VirtualBox
if (-not (Test-Path $VBoxManage)) {
    Write-Host "ERROR: VirtualBox not found." -ForegroundColor Red
    exit 1
}

Write-Host @"

OPTION 1: Use Pre-built DVWA VM (Recommended)
============================================
Download from: https://www.yoursecsrc.com/dvwa-vm-download/
Or search "DVWA VirtualBox image download"

OPTION 2: Build from Ubuntu Server (More Control)
=================================================
1. Download Ubuntu Server 22.04 LTS:
   https://ubuntu.com/download/server

2. Minimal installation (no GUI needed)

Press 1 for pre-built DVWA, or 2 for Ubuntu setup:
"@ -ForegroundColor Yellow

$choice = Read-Host "Choice [1/2]"

if ($choice -eq "1") {
    Write-Host "`nUsing pre-built DVWA approach..." -ForegroundColor Cyan
    Write-Host @"

MANUAL STEPS:
1. Download a DVWA VirtualBox image
2. Import into VirtualBox
3. Configure network to Host-Only
4. Set static IP: 10.0.0.20

After import, run this to configure networking:
  VBoxManage modifyvm "DVWA" --nic1 hostonly --hostonlyadapter1 "<adapter-name>"

"@ -ForegroundColor Yellow
} else {
    Write-Host "`nCreating Ubuntu VM for DVWA..." -ForegroundColor Cyan

    $vmName = "DVWA-Target"

    # Create VM
    Write-Host "`n[1/6] Creating VM..." -ForegroundColor Yellow
    & $VBoxManage createvm --name $vmName --ostype "Ubuntu_64" --register

    # Configure resources (minimal for DVWA)
    Write-Host "`n[2/6] Configuring Resources..." -ForegroundColor Yellow
    & $VBoxManage modifyvm $vmName --memory 1024 --cpus 1 --vram 16

    # Create disk
    Write-Host "`n[3/6] Creating Virtual Disk..." -ForegroundColor Yellow
    $diskPath = "$VMDir\$vmName\$vmName.vdi"
    & $VBoxManage createhd --filename $diskPath --size 10240 --format VDI

    # Add storage controller and attach disk
    & $VBoxManage storagectl $vmName --name "SATA" --add sata --controller IntelAhci
    & $VBoxManage storageattach $vmName --storagectl "SATA" --port 0 --device 0 --type hdd --medium $diskPath

    # Add DVD drive for ISO
    & $VBoxManage storagectl $vmName --name "IDE" --add ide

    Write-Host "`n[4/6] Configuring Network..." -ForegroundColor Yellow
    $adapters = & $VBoxManage list hostonlyifs
    $adapterName = ($adapters | Select-String "Name:" | Select-Object -First 1) -replace "Name:\s+", ""
    & $VBoxManage modifyvm $vmName --nic1 hostonly --hostonlyadapter1 $adapterName

    Write-Host "`n[5/6] Enabling features..." -ForegroundColor Yellow
    & $VBoxManage modifyvm $vmName --boot1 dvd --boot2 disk --boot3 none --boot4 none
    & $VBoxManage modifyvm $vmName --graphicscontroller vmsvga

    Write-Host "`n[6/6] Creating DVWA setup script..." -ForegroundColor Yellow
}

# Create DVWA Docker setup script (works for both approaches)
$dvwaSetupScript = @"
#!/bin/bash
# DVWA Setup Script - Run inside Ubuntu VM

set -e

echo "=== DVWA Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "[1/4] Installing Docker..."
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker \$USER

# Set static IP
echo "[2/4] Configuring Network..."
sudo tee /etc/netplan/01-static.yaml << EOF
network:
  version: 2
  ethernets:
    enp0s3:
      addresses:
        - 10.0.0.20/24
      routes:
        - to: default
          via: 10.0.0.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
EOF
sudo netplan apply

# Create DVWA docker-compose
echo "[3/4] Setting up DVWA..."
mkdir -p ~/dvwa && cd ~/dvwa

cat << 'COMPOSE' > docker-compose.yml
version: '3'
services:
  dvwa:
    image: vulnerables/web-dvwa
    ports:
      - "80:80"
    restart: always
COMPOSE

# Start DVWA
echo "[4/4] Starting DVWA..."
sudo docker-compose up -d

echo ""
echo "=== DVWA Setup Complete ==="
echo "Access DVWA at: http://10.0.0.20"
echo "Default login: admin / password"
echo ""
echo "To reset database, go to: http://10.0.0.20/setup.php"
"@

$scriptsDir = "$LabDir\attack_scripts"
if (-not (Test-Path $scriptsDir)) {
    New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
}
$dvwaSetupScript | Out-File -FilePath "$scriptsDir\dvwa_setup.sh" -Encoding UTF8

Write-Host "`n=== DVWA Setup Instructions Complete ===" -ForegroundColor Cyan
Write-Host @"

Next Steps:
1. Download Ubuntu Server ISO or pre-built DVWA image
2. If Ubuntu: Attach ISO and install minimal server
3. After boot, copy and run: dvwa_setup.sh
4. Access DVWA at: http://10.0.0.20

DVWA provides these vulnerable scenarios:
  - SQL Injection
  - XSS (Stored/Reflected)
  - Command Injection
  - File Upload vulnerabilities
  - CSRF
  - Brute Force login

Perfect for testing defensive AI detection!

"@ -ForegroundColor White
