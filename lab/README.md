# AI-Defender Lab Environment

## Overview
Isolated virtual network for testing defensive AI capabilities against simulated attacks.

## Architecture
```
Host (Windows 11)                    Isolated Network (10.0.0.0/24)
┌─────────────────┐                 ┌─────────────────────────────┐
│ AI-Defender     │                 │  ┌─────────┐  ┌─────────┐  │
│ Agent           │◄───────────────►│  │ Kali    │  │ Target  │  │
│                 │                 │  │ Attacker│  │ DVWA    │  │
│ Port 5000       │                 │  │ .10     │  │ .20     │  │
│ (Honeypot)      │                 │  └─────────┘  └─────────┘  │
└─────────────────┘                 └─────────────────────────────┘
```

## VMs Required

### 1. Kali Linux (Attacker)
- **Purpose**: Simulates AI-orchestrated attacks
- **IP**: 10.0.0.10
- **RAM**: 2GB minimum
- **Disk**: 40GB
- **Download**: https://www.kali.org/get-kali/#kali-virtual-machines

### 2. DVWA on Ubuntu (Target)
- **Purpose**: Vulnerable web application for realistic scenarios
- **IP**: 10.0.0.20
- **RAM**: 1GB
- **Disk**: 10GB
- **Setup**: Docker container on lightweight Ubuntu

## Network Configuration
- **Network Name**: AI-Defender-Lab
- **Type**: Host-Only Adapter
- **Subnet**: 10.0.0.0/24
- **DHCP**: Disabled (static IPs)

## Quick Start
1. Install VirtualBox
2. Run `setup_network.ps1` to create host-only network
3. Import Kali VM
4. Create Ubuntu VM with DVWA
5. Run `test_connectivity.ps1` to verify
