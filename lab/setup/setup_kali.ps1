# Setup Kali Linux VM for AI-Defender Lab
# Run as Administrator

$VBoxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$LabDir = Split-Path -Parent $PSScriptRoot
$VMDir = "$LabDir\vms"

Write-Host "=== Kali Linux VM Setup ===" -ForegroundColor Cyan

# Check for VirtualBox
if (-not (Test-Path $VBoxManage)) {
    Write-Host "ERROR: VirtualBox not found." -ForegroundColor Red
    exit 1
}

# Create VM directory
if (-not (Test-Path $VMDir)) {
    New-Item -ItemType Directory -Path $VMDir -Force | Out-Null
}

Write-Host @"

MANUAL STEP REQUIRED:
=====================
1. Download Kali Linux VirtualBox image from:
   https://www.kali.org/get-kali/#kali-virtual-machines

2. Choose "VirtualBox 64-bit" (approximately 3GB download)

3. Extract the .ova or .vbox file to:
   $VMDir

4. Once downloaded, press Enter to continue...

"@ -ForegroundColor Yellow

Read-Host "Press Enter when Kali image is downloaded and extracted"

# Look for .ova or .vbox file
$ovaFile = Get-ChildItem -Path $VMDir -Filter "*.ova" -ErrorAction SilentlyContinue | Select-Object -First 1
$vboxFile = Get-ChildItem -Path $VMDir -Filter "*.vbox" -ErrorAction SilentlyContinue | Select-Object -First 1

if ($ovaFile) {
    Write-Host "`n[1/5] Importing Kali OVA..." -ForegroundColor Yellow
    & $VBoxManage import $ovaFile.FullName --vsys 0 --vmname "Kali-Attacker"
} elseif ($vboxFile) {
    Write-Host "`n[1/5] Registering Kali VM..." -ForegroundColor Yellow
    & $VBoxManage registervm $vboxFile.FullName
} else {
    Write-Host "ERROR: No .ova or .vbox file found in $VMDir" -ForegroundColor Red
    Write-Host "Please download and extract the Kali image first." -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[2/5] Configuring VM Resources..." -ForegroundColor Yellow

# Get the actual VM name (might differ from import)
$vmList = & $VBoxManage list vms
$kaliVM = if ($vmList -match '"(.*[Kk]ali.*)"') { $matches[1] } else { "Kali-Attacker" }

# Configure resources
& $VBoxManage modifyvm $kaliVM --memory 2048 --cpus 2 --vram 128

Write-Host "`n[3/5] Configuring Network..." -ForegroundColor Yellow

# Get host-only adapter name
$adapters = & $VBoxManage list hostonlyifs
$adapterName = ($adapters | Select-String "Name:" | Select-Object -First 1) -replace "Name:\s+", ""

# Set to host-only network
& $VBoxManage modifyvm $kaliVM --nic1 hostonly --hostonlyadapter1 $adapterName

Write-Host "`n[4/5] Creating Shared Folder for Attack Scripts..." -ForegroundColor Yellow

$scriptsDir = "$LabDir\attack_scripts"
if (-not (Test-Path $scriptsDir)) {
    New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
}

& $VBoxManage sharedfolder add $kaliVM --name "attack_scripts" --hostpath $scriptsDir --automount 2>$null

Write-Host "`n[5/5] Creating Post-Boot Configuration Script..." -ForegroundColor Yellow

# Create a script to run inside Kali after first boot
$kaliSetupScript = @"
#!/bin/bash
# Run this inside Kali VM after first boot

# Set static IP
sudo tee /etc/network/interfaces.d/eth0 << EOF
auto eth0
iface eth0 inet static
    address 10.0.0.10
    netmask 255.255.255.0
    gateway 10.0.0.1
EOF

# Restart networking
sudo systemctl restart networking

# Mount shared folder
sudo mkdir -p /mnt/attack_scripts
sudo mount -t vboxsf attack_scripts /mnt/attack_scripts

# Add to fstab for persistence
echo "attack_scripts /mnt/attack_scripts vboxsf defaults 0 0" | sudo tee -a /etc/fstab

# Verify
ip addr show eth0
ping -c 2 10.0.0.1

echo "Kali setup complete!"
"@

$kaliSetupScript | Out-File -FilePath "$scriptsDir\kali_post_boot.sh" -Encoding UTF8

Write-Host "`n=== Kali VM Setup Complete ===" -ForegroundColor Cyan
Write-Host @"

VM Configuration:
  Name:     $kaliVM
  RAM:      2048 MB
  CPUs:     2
  Network:  Host-Only (10.0.0.10)

Default Credentials:
  Username: kali
  Password: kali

Post-Boot Steps:
  1. Start the VM: VBoxManage startvm "$kaliVM"
  2. Login with kali/kali
  3. Open terminal and run:
     sudo bash /mnt/attack_scripts/kali_post_boot.sh

  Or manually set IP:
     sudo ip addr add 10.0.0.10/24 dev eth0
     sudo ip link set eth0 up

"@ -ForegroundColor White
