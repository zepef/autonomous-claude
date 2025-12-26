"""
AI-Defender Monitoring Dashboard

Streamlit-based dashboard for monitoring:
- Classifier evolution and fitness
- Honeypot activity
- Memory system status
- Agent decision history
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.memory.short_term import (
    get_recent_memories, get_evolution_history,
    get_best_strategies, get_stats as get_memory_stats
)
from src.memory.long_term import get_long_term_memory


# Page config
st.set_page_config(
    page_title="AI-Defender Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EVOLUTION_STATE_PATH = PROJECT_ROOT / "data" / "evolution_state.json"
AGENT_STATE_PATH = PROJECT_ROOT / "data" / "agent_state.json"
HONEYPOT_LOG_DIR = PROJECT_ROOT / "logs" / "honeypot"


def load_evolution_state():
    """Load evolution state from file"""
    if EVOLUTION_STATE_PATH.exists():
        with open(EVOLUTION_STATE_PATH) as f:
            return json.load(f)
    return None


def load_agent_state():
    """Load agent state from file"""
    if AGENT_STATE_PATH.exists():
        with open(AGENT_STATE_PATH) as f:
            return json.load(f)
    return None


def load_honeypot_logs():
    """Load recent honeypot logs"""
    if not HONEYPOT_LOG_DIR.exists():
        return []

    logs = []
    for log_file in sorted(HONEYPOT_LOG_DIR.glob("*.json"), reverse=True)[:5]:
        try:
            with open(log_file) as f:
                logs.extend(json.load(f))
        except:
            pass

    return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:100]


# Title
st.title("🛡️ AI-Defender Dashboard")
st.markdown("*Autonomous Defensive AI System with Genetic Evolution*")

# Sidebar
st.sidebar.header("System Status")

# Load states
evolution_state = load_evolution_state()
agent_state = load_agent_state()

# Sidebar metrics
if evolution_state:
    best = evolution_state.get('best_strategy', {})
    st.sidebar.metric("Best Fitness", f"{best.get('fitness_score', 0):.3f}")
    st.sidebar.metric("Generation", evolution_state.get('generation', 0))
    st.sidebar.metric("Population Size", len(evolution_state.get('population', [])))

if agent_state:
    st.sidebar.metric("Agent Cycles", agent_state.get('cycle_count', 0))
    st.sidebar.metric("Evolution Runs", agent_state.get('evolution_runs', 0))

# Refresh button
if st.sidebar.button("🔄 Refresh"):
    st.rerun()

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Evolution", "🍯 Honeypot", "🧠 Memory", "📊 Statistics"])

# Tab 1: Evolution
with tab1:
    st.header("Classifier Evolution")

    if evolution_state:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Best Strategy")
            best = evolution_state.get('best_strategy', {})

            st.json({
                "ID": best.get('id', 'N/A'),
                "Generation": best.get('generation', 0),
                "Method": best.get('method', 'N/A'),
                "Threshold": f"{best.get('threshold', 0):.2f}",
                "Roleplay Weight": f"{best.get('roleplay_weight', 0):.2f}",
                "Fitness": f"{best.get('fitness_score', 0):.3f}"
            })

            # Metrics
            metrics = best.get('metrics', {})
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("TP", metrics.get('tp', 0))
            mcol2.metric("FP", metrics.get('fp', 0))
            mcol3.metric("TN", metrics.get('tn', 0))
            mcol4.metric("FN", metrics.get('fn', 0))

        with col2:
            st.subheader("Fitness History")
            history = evolution_state.get('best_fitness_history', [])
            if history:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=history,
                    mode='lines+markers',
                    name='Best Fitness',
                    line=dict(color='#00cc66')
                ))
                fig.update_layout(
                    xaxis_title="Generation",
                    yaxis_title="Fitness",
                    yaxis_range=[0, 1],
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No fitness history yet")

        # Population overview
        st.subheader("Population Overview")
        population = evolution_state.get('population', [])
        if population:
            pop_df = pd.DataFrame([
                {
                    "ID": s.get('id', '')[:8],
                    "Gen": s.get('generation', 0),
                    "Method": s.get('method', ''),
                    "Threshold": f"{s.get('threshold', 0):.2f}",
                    "Fitness": f"{s.get('fitness_score', 0):.3f}"
                }
                for s in population
            ])
            st.dataframe(pop_df, use_container_width=True)
    else:
        st.warning("No evolution state found. Run the classifier evolution first.")

# Tab 2: Honeypot
with tab2:
    st.header("Honeypot Activity")

    honeypot_logs = load_honeypot_logs()

    if honeypot_logs:
        col1, col2 = st.columns(2)

        with col1:
            # Summary metrics
            total = len(honeypot_logs)
            malicious = sum(1 for l in honeypot_logs if l.get('is_malicious'))
            unique_ips = len(set(l.get('ip', '') for l in honeypot_logs))

            st.metric("Total Requests", total)
            st.metric("Malicious Detected", malicious)
            st.metric("Unique IPs", unique_ips)

            # Classification distribution
            if total > 0:
                fig = px.pie(
                    values=[malicious, total - malicious],
                    names=['Malicious', 'Benign'],
                    color_discrete_sequence=['#ff4444', '#44aa44']
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Recent Requests")
            for log in honeypot_logs[:10]:
                status = "🔴" if log.get('is_malicious') else "🟢"
                conf = log.get('confidence', 0)
                prompt = log.get('prompt', '')[:50]
                st.markdown(f"{status} `{log.get('ip', 'unknown')}` ({conf:.2f}): {prompt}...")
    else:
        st.info("No honeypot logs yet. Start the honeypot server to collect data.")

# Tab 3: Memory
with tab3:
    st.header("Memory Systems")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Short-Term Memory")
        try:
            memories = get_recent_memories(20)
            mem_stats = get_memory_stats()

            st.metric("Total Entries", mem_stats.get('total_memories', 0))
            st.metric("Evolution Events", mem_stats.get('evolution_events', 0))

            # Type breakdown
            type_counts = mem_stats.get('by_type', {})
            if type_counts:
                fig = px.bar(
                    x=list(type_counts.keys()),
                    y=list(type_counts.values()),
                    labels={'x': 'Type', 'y': 'Count'}
                )
                fig.update_layout(height=200)
                st.plotly_chart(fig, use_container_width=True)

            # Recent memories
            st.markdown("**Recent Memories:**")
            for mem in memories[:10]:
                mem_type = mem.get('type', 'unknown')
                content = mem.get('content', '')[:60]
                st.markdown(f"- `[{mem_type}]` {content}...")

        except Exception as e:
            st.error(f"Error loading short-term memory: {e}")

    with col2:
        st.subheader("Long-Term Memory")
        try:
            long_term = get_long_term_memory()
            if long_term.is_available():
                stats = long_term.get_stats()
                st.metric("Total Points", stats.get('total_points', 0))
                st.metric("Status", stats.get('status', 'unknown'))

                # Recent strategies
                strategies = long_term.get_strategies(limit=5)
                if strategies:
                    st.markdown("**Stored Strategies:**")
                    for s in strategies:
                        st.markdown(f"- {s.get('content', '')[:60]}...")
            else:
                st.warning("Qdrant not connected. Start Docker container.")

        except Exception as e:
            st.error(f"Error loading long-term memory: {e}")

# Tab 4: Statistics
with tab4:
    st.header("System Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Evolution History")
        try:
            evo_history = get_evolution_history(limit=50)
            if evo_history:
                df = pd.DataFrame(evo_history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                fig = px.scatter(
                    df,
                    x='generation',
                    y='fitness_score',
                    color='strategy_id',
                    hover_data=['action', 'outcome'],
                    title="Fitness by Generation"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Best strategies table
                best = get_best_strategies(limit=5)
                if best:
                    st.markdown("**Top Performing Strategies:**")
                    best_df = pd.DataFrame(best)
                    st.dataframe(best_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading evolution history: {e}")

    with col2:
        st.subheader("Agent State")
        if agent_state:
            st.json(agent_state)
        else:
            st.info("No agent state found. Start the autonomous agent.")

# Footer
st.markdown("---")
st.markdown("*AI-Defender v0.1.0 | Refresh page for latest data*")
