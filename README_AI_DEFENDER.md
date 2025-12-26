# AI-Defender

**Autonomous Defensive AI System with Genetic Evolution**

An experimental system that detects and responds to malicious AI-orchestrated attacks. The classifier evolves over time using genetic algorithms, improving detection accuracy without human intervention.

## Quick Start

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Check system status
python run.py status

# Run autonomous agent for 1 hour
python run.py agent --hours 1

# Or just evolve the classifier
python run.py evolve --gens 30
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              AI-DEFENDER SYSTEM                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│   META-LEARNER ──▶ CLASSIFIER ──▶ HONEYPOT         │
│        │          (evolving)      (fake MCP)        │
│        │                                            │
│        ▼                                            │
│   ┌─────────────────────────────────────────┐      │
│   │            MEMORY LAYER                 │      │
│   │  Short-term (SQLite) + Long-term (Qdrant)     │
│   └─────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Genetic Evolution** | Classifier strategies evolve to improve detection |
| **Dual Memory** | Short-term context + long-term semantic search |
| **Honeypot** | Fake MCP server engages attackers with fake data |
| **Autonomous Loop** | READ→THINK→ACT→RECORD decision cycle |

## Commands

```bash
python run.py agent --hours 24     # Run autonomous agent
python run.py evolve --gens 50     # Evolve classifier
python run.py honeypot --port 5000 # Start honeypot
python run.py dashboard            # Launch monitoring
python run.py classify "prompt"    # Classify single prompt
python run.py status               # Show system status
```

## Documentation

See [docs/SYSTEM_REPORT.md](docs/SYSTEM_REPORT.md) for detailed technical documentation.

## Project Structure

```
├── run.py                  # Main entry point
├── src/
│   ├── classifier/         # Evolving classifier + genetic algo
│   ├── honeypot/           # Fake MCP server
│   ├── agents/             # Autonomous controller
│   ├── memory/             # Short-term + long-term memory
│   └── dashboard/          # Streamlit monitoring
├── data/
│   ├── datasets/           # 1100 training prompts
│   └── memory/             # SQLite database
└── lab/                    # VirtualBox attack simulation setup
```

## Requirements

- Python 3.12+
- Windows 11 (tested)
- Docker (optional, for Qdrant long-term memory)
- VirtualBox (optional, for lab environment)
