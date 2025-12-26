# VirtualBox Installation Guide for Windows 11

## Step 1: Download VirtualBox
1. Go to: https://www.virtualbox.org/wiki/Downloads
2. Click "Windows hosts" under VirtualBox platform packages
3. Download the latest version (7.x recommended)

## Step 2: Install
1. Run the downloaded installer
2. Click "Next" through the wizard
3. **Important**: When prompted about network interfaces, click "Yes" to allow
4. Complete installation and restart if prompted

## Step 3: Install Extension Pack (Optional but Recommended)
1. On the same download page, get "VirtualBox Extension Pack"
2. Double-click the downloaded file
3. VirtualBox will open and prompt to install - click "Install"
4. Accept the license

## Step 4: Verify Installation
Open PowerShell and run:
```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" --version
```

Should output something like: `7.0.14r161095`

## Troubleshooting

### "VT-x is disabled in BIOS"
1. Restart computer
2. Enter BIOS (usually F2, F12, or Del during boot)
3. Find "Virtualization Technology" or "VT-x"
4. Enable it
5. Save and exit

### "Hyper-V conflicts"
Windows 11 Home shouldn't have this, but if you see it:
```powershell
bcdedit /set hypervisorlaunchtype off
```
Then restart.

## Next Steps
After installation, run `setup_network.ps1` to create the isolated lab network.
