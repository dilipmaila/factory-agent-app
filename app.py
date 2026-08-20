"""
Manufacturing Operator AI Assistant - Streamlit Application.
Features real-time cognitive state tracking, UCB Contextual Bandit format personalization,
NetworkX Knowledge Graph autonomy learning, and SCADA/CMMS closed-loop feedback.
"""

import os
import sys
from pathlib import Path
from typing import Any
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Project Root and Data Directory
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

# Internal Imports
from mock_services.scada_service import MockSCADA
from mock_services.cmms_service import MockCMMS
from mock_services.hr_lms_service import MockHRLMS
from memory.search import HybridRetriever
from memory.semantic_graph import OperatorKnowledgeGraph
from memory.episodic_store import EpisodicMemory
from memory.working_memory import build_prompt
from agents.bandit_router import ContextualBandit
from agents.chat_agent import ManufacturingChatAgent
from agents.shadow_observer import ShadowObserver

# Set Page Config
st.set_page_config(
    page_title="Shopfloor AI Copilot | Adaptive Learning",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Enterprise-Grade Styling
st.markdown(
    """
    <style>
    /* Global Clean Font Scale */
    html, body, [class*="css"] {
        font-size: 0.93rem;
    }
    
    /* Shrink Metric Values to Moderate Size (26-28px max) */
    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        color: #f1f5f9 !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Standardized Top Column Headers */
    .col-header {
        font-size: 1.18rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 0px;
        margin-bottom: 2px;
        padding-top: 0px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .col-subheader {
        font-size: 0.78rem;
        color: #64748b;
        margin-bottom: 12px;
    }
    
    /* Clean, non-intrusive format pill */
    .format-pill {
        background: #1e1b4b;
        color: #a5b4fc;
        border: 1px solid #3730a3;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        display: inline-block;
        margin-bottom: 6px;
    }
    
    /* Muted, high-contrast tier badges */
    .tier-tag {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    .tier-novice { background: #78350f; color: #fde68a; }
    .tier-intermediate { background: #0c4a6e; color: #bae6fd; }
    .tier-expert { background: #064e3b; color: #a7f3d0; }

    /* Compact Tabs */
    button[data-baseweb="tab"] {
        padding-left: 10px !important;
        padding-right: 10px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    /* Fixed Button Colors: Solve (Green) & Escalate (Red/Orange) */
    div.stButton button:has(p:contains("Solved")),
    button[data-testid*="btn_solve"] {
        background-color: #15803d !important;
        color: #ffffff !important;
        border: 1px solid #22c55e !important;
    }
    div.stButton button:has(p:contains("Solved")):hover,
    button[data-testid*="btn_solve"]:hover {
        background-color: #16a34a !important;
        border-color: #4ade80 !important;
    }

    div.stButton button:has(p:contains("Escalate")),
    button[data-testid*="btn_escalate"] {
        background-color: #991b1b !important;
        color: #ffffff !important;
        border: 1px solid #ef4444 !important;
    }
    div.stButton button:has(p:contains("Escalate")):hover,
    button[data-testid*="btn_escalate"]:hover {
        background-color: #b91c1c !important;
        border-color: #f87171 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_telemetry_metric(key: str, value: Any) -> str:
    """Formats raw SCADA telemetry keys into clear, readable engineering units."""
    key_map = {
        "air_pressure_psi": ("Air Pressure", "PSI"),
        "spindle_rpm": ("Spindle Speed", "RPM"),
        "amplifier_temp_c": ("Amplifier Temp", "°C"),
        "zone_1_temp_c": ("Zone 1 Temp", "°C"),
        "zone_2_temp_c": ("Zone 2 Temp", "°C"),
        "hydraulic_pressure_bar": ("Hydraulic Pressure", "Bar"),
        "clamping_force_kn": ("Clamping Force", "kN"),
        "estop_pressed": ("E-Stop", ""),
    }
    if key in key_map:
        label, unit = key_map[key]
        if key == "estop_pressed":
            status_str = "ACTIVE (Pressed)" if value else "NORMAL (Disengaged)"
            return f"• **{label}:** `{status_str}`"
        return f"• **{label}:** `{value} {unit}`".strip()
    return f"• **{key.replace('_', ' ').title()}:** `{value}`"


# --- 1. SINGLETON / RESOURCES INITIALIZATION ---
@st.cache_resource
def get_shared_resources():
    """Initializes shared backend models, graph, and retrievers."""
    chroma_dir = DATA_DIR / "chroma_db"
    bm25_file = DATA_DIR / "bm25_retriever.pkl"
    graph_file = DATA_DIR / "graph_state.json"
    log_file = DATA_DIR / "episodic_logs.json"

    scada = MockSCADA()
    cmms = MockCMMS()
    hr_lms = MockHRLMS()
    graph = OperatorKnowledgeGraph(state_file=str(graph_file))
    episodic = EpisodicMemory(log_file=str(log_file))

    try:
        retriever = HybridRetriever(
            chroma_persist_dir=str(chroma_dir),
            bm25_path=str(bm25_file),
        )
    except Exception:
        retriever = None

    bandit = ContextualBandit(knowledge_graph=graph, exploration_c=1.2)
    
    try:
        chat_agent = ManufacturingChatAgent(model_name="gemini-3.5-flash-lite")
    except Exception:
        chat_agent = None

    observer = ShadowObserver(
        knowledge_graph=graph,
        bandit_router=bandit,
        episodic_memory=episodic,
        cmms_service=cmms,
        scada_service=scada,
    )

    return {
        "scada": scada,
        "cmms": cmms,
        "hr_lms": hr_lms,
        "graph": graph,
        "episodic": episodic,
        "retriever": retriever,
        "bandit": bandit,
        "chat_agent": chat_agent,
        "observer": observer,
    }


resources = get_shared_resources()

# Session State Variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_context" not in st.session_state:
    st.session_state.last_context = None
if "current_operator_id" not in st.session_state:
    st.session_state.current_operator_id = "OP-001"
if "current_machine" not in st.session_state:
    st.session_state.current_machine = "Haas VF-2"
if "feedback_status" not in st.session_state:
    st.session_state.feedback_status = None


# --- 2. SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("🏭 Factory Hub")
    st.caption("Adaptive Operator Intelligence")
    st.markdown("---")

    # Section A: Operator Profile
    st.markdown("##### 👤 Operator Selection")
    operators = resources["hr_lms"].get_all_operators()
    op_options = {
        f"{op['name']} ({op['default_tier']} - {op['operator_id']})": op["operator_id"]
        for op in operators
    }
    
    selected_label = st.selectbox(
        "Select Active Operator",
        options=list(op_options.keys()),
        index=0,
        label_visibility="collapsed",
    )
    selected_op_id = op_options[selected_label]

    if selected_op_id != st.session_state.current_operator_id:
        st.session_state.current_operator_id = selected_op_id
        st.session_state.chat_history = []
        st.session_state.last_context = None
        st.session_state.feedback_status = None
        st.rerun()

    op_profile = resources["hr_lms"].get_operator_profile(selected_op_id)
    if op_profile:
        st.caption(
            f"**Role:** {op_profile.get('role')} | **Shift:** {op_profile.get('shift')} | **Tenure:** {op_profile.get('experience_months')} mo."
        )

    st.write("")  # Visual breathing room
    st.markdown("---")

    # Section B: Machine & SCADA Telemetry
    st.markdown("##### ⚙️ Workcell Equipment")
    machines = ["Haas VF-2", "Engel Victory 330"]
    selected_machine = st.selectbox("Active Machine", options=machines, index=0, label_visibility="collapsed")
    st.session_state.current_machine = selected_machine

    st.write("")
    st.markdown("##### 📡 SCADA Telemetry State")
    active_alarm = resources["scada"].get_active_alarm(selected_machine)
    alarm_details = resources["scada"].get_alarm_details(selected_machine)

    if "Normal" in active_alarm:
        st.success(f"🟢 **{active_alarm}**")
    else:
        st.error(f"🚨 **{active_alarm}**")

    if alarm_details and "telemetry" in alarm_details:
        for k, v in alarm_details["telemetry"].items():
            st.caption(format_telemetry_metric(k, v))

    st.write("")
    # Alarm Simulation / Clear Controls
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("Trigger Alarm", use_container_width=True):
            if selected_machine == "Haas VF-2":
                resources["scada"].set_active_alarm(
                    "Haas VF-2",
                    "Alarm 102",
                    "SERVOS OFF",
                    "Servo amplifiers disabled. Air pressure low or E-stop.",
                    {"air_pressure_psi": 64.0, "estop_pressed": False, "spindle_rpm": 0},
                )
            else:
                resources["scada"].set_active_alarm(
                    "Engel Victory 330",
                    "E-201",
                    "BARREL OVERHEAT",
                    "Zone 2 heater over operating threshold.",
                    {"zone_1_temp_c": 210.0, "zone_2_temp_c": 272.0, "hydraulic_pressure_bar": 150.0},
                )
            st.rerun()

    with col_s2:
        if st.button("Clear SCADA", use_container_width=True):
            resources["scada"].clear_alarm(selected_machine)
            st.rerun()

    st.markdown("---")
    if st.button("♻️ Reset Graph Defaults", use_container_width=True):
        resources["graph"]._seed_default_graph()
        resources["graph"].save_to_file()
        st.session_state.chat_history = []
        st.session_state.last_context = None
        st.session_state.feedback_status = None
        st.toast("Knowledge Graph & Bandit weights reset to baseline!", icon="♻️")
        st.rerun()


# --- 3. MAIN DASHBOARD LAYOUT (2 COLUMNS) ---
left_col, right_col = st.columns([1.15, 0.85], gap="large")

current_tier = resources["graph"].get_operator_tier(selected_op_id)
current_autonomy = resources["graph"].get_autonomy_score(selected_op_id, selected_machine)

# =========================================================================
# LEFT COLUMN: INTERACTIVE COPILOT CHAT & CLOSED-LOOP FEEDBACK
# =========================================================================
with left_col:
    st.markdown(f'<div class="col-header">💬 Shopfloor AI Copilot — {selected_machine}</div>', unsafe_allow_html=True)
    
    tier_class = f"tier-{current_tier.lower()}"
    st.markdown(
        f"""
        <div class="col-subheader">
            Operator: <strong>{op_profile.get('name', selected_op_id)}</strong> &nbsp;|&nbsp; 
            Tier: <span class="tier-tag {tier_class}">{current_tier}</span> &nbsp;|&nbsp; 
            Machine Autonomy: <strong>{current_autonomy:.1f}%</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Render Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="👨‍🔧" if msg["role"] == "user" else "🤖"):
            if msg.get("format_badge"):
                st.markdown(f"<span class='format-pill'>{msg['format_badge']}</span>", unsafe_allow_html=True)
            st.markdown(msg["content"])
            if msg.get("doc_citations"):
                with st.expander("📚 Grounding SOP References"):
                    for doc_ref in msg["doc_citations"]:
                        st.caption(f"• **{doc_ref['id']}** ({doc_ref['machine']}) — RRF: `{doc_ref['score']:.4f}`")

    # --- SIMPLIFIED, CLEAN FEEDBACK PROMPT (Directly under latest turn) ---
    if st.session_state.chat_history and st.session_state.last_context and not st.session_state.last_context.get("feedback_given"):
        st.markdown(
            "<p style='font-size:0.85rem; color:#94a3b8; margin-top:12px; margin-bottom:6px; font-style:italic;'>Did this guidance resolve the machine issue?</p>",
            unsafe_allow_html=True,
        )

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            if st.button("✅ Solved Independently", use_container_width=True, key="btn_solve_feedback"):
                eval_res = resources["observer"].evaluate_session(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    format_used=st.session_state.last_context.get("format_used", "Visual_StepByStep"),
                    escalated=False,
                    query=st.session_state.last_context.get("query", ""),
                    response=st.session_state.last_context.get("response", ""),
                )
                st.session_state.last_context["feedback_given"] = True
                st.session_state.feedback_status = f"✅ Resolved independently! Autonomy score increased to {eval_res['new_autonomy_score']:.1f}%."
                st.toast(f"Autonomy Score Updated: +5.0 (Now {eval_res['new_autonomy_score']:.1f}%)", icon="📈")
                st.rerun()

        with f_col2:
            if st.button("⚠️ Escalate to Supervisor", use_container_width=True, key="btn_escalate_feedback"):
                eval_res = resources["observer"].evaluate_session(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    format_used=st.session_state.last_context.get("format_used", "Visual_StepByStep"),
                    escalated=True,
                    issue_desc=f"Escalated from turn: {st.session_state.last_context.get('query', 'N/A')}",
                    query=st.session_state.last_context.get("query", ""),
                    response=st.session_state.last_context.get("response", ""),
                )
                st.session_state.last_context["feedback_given"] = True
                st.session_state.feedback_status = f"⚠️ Escalated to maintenance team ({eval_res['ticket_id']}). Autonomy score adjusted to {eval_res['new_autonomy_score']:.1f}%."
                st.toast(f"Escalation Dispatched: {eval_res['ticket_id']} (Autonomy -15.0)", icon="🚨")
                st.rerun()

    elif st.session_state.feedback_status:
        if "✅" in st.session_state.feedback_status:
            st.success(st.session_state.feedback_status)
        else:
            st.warning(st.session_state.feedback_status)

    # Clean Quick Prompt Section Grouped at Bottom
    st.markdown("---")
    st.caption("⚡ Quick Shopfloor Prompts:")
    sample_queries = {
        "Haas VF-2": [
            "How do I clear Alarm 102 (Servos Off)?",
            "What G-code is used for peck drilling cycles?",
            "Tool unclamp is stuck on M06 command. How do I fix it?",
        ],
        "Engel Victory 330": [
            "How do I fix barrel temperature overheat in Zone 2?",
            "What are the resolution steps for low hydraulic clamping pressure?",
            "How do I safely purge the injection screw before mold change?",
        ],
    }

    quick_cols = st.columns(len(sample_queries.get(selected_machine, [])))
    prompt_to_send = None
    for idx, sample_q in enumerate(sample_queries.get(selected_machine, [])):
        with quick_cols[idx]:
            if st.button(sample_q, key=f"quick_{idx}", use_container_width=True):
                prompt_to_send = sample_q

    # Pinned Chat Input
    user_input = st.chat_input("Ask about machine alarms, M-codes, SOPs, or mechanical repairs...")
    active_query = prompt_to_send or user_input

    if active_query:
        st.session_state.feedback_status = None
        
        # 1. Log User Message
        st.session_state.chat_history.append({"role": "user", "content": active_query})

        with st.chat_message("user", avatar="👨‍🔧"):
            st.markdown(active_query)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Retrieving SOPs & personalizing response..."):
                # A. Retrieve SOPs via Hybrid Search
                retrieved_docs = []
                if resources["retriever"]:
                    try:
                        retrieved_docs = resources["retriever"].search(
                            query=active_query,
                            top_k=3,
                            filter_dict={"machine": selected_machine},
                        )
                    except Exception:
                        retrieved_docs = resources["retriever"].search(query=active_query, top_k=3)

                # B. Query Contextual Bandit Router for Winning Arm
                best_arm, arm_instruction, ucb_stats = resources["bandit"].select_format(selected_op_id)

                # C. Build Safety Directives & Operator Context
                safety_rules = [
                    "Lock-Out / Tag-Out (LOTO) mandatory before opening high-voltage enclosures.",
                    "Wear protective heat-resistant gloves and safety glasses during high temp maintenance.",
                    "Verify zero pneumatic line pressure before disconnecting air fittings.",
                ]
                op_ctx = {
                    "name": op_profile.get("name", selected_op_id),
                    "tier": current_tier,
                    "machine_id": selected_machine,
                    "active_alarm": active_alarm,
                    "autonomy_score": current_autonomy,
                }

                # D. Assemble Working Memory Prompt
                prompt_text = build_prompt(
                    safety_warnings=safety_rules,
                    bandit_format_instruction=arm_instruction,
                    retrieved_sops=retrieved_docs,
                    user_query=active_query,
                    operator_context=op_ctx,
                )

                # E. Generate LLM Response
                if resources["chat_agent"]:
                    response_text = resources["chat_agent"].generate_response(prompt_text, active_query)
                else:
                    response_text = f"[Simulation Mode]\n\nStandard SOP Guidance for **{active_query}** under **{best_arm}** policy."

                # F. Display Response
                format_badge = f"Bandit Arm: {best_arm}"
                st.markdown(f"<span class='format-pill'>{format_badge}</span>", unsafe_allow_html=True)
                st.markdown(response_text)

                doc_citations = [
                    {
                        "id": d.metadata.get("id", "SOP"),
                        "machine": d.metadata.get("machine", selected_machine),
                        "score": d.metadata.get("rrf_score", 0.0),
                    }
                    for d in retrieved_docs
                ]

                st.session_state.last_context = {
                    "query": active_query,
                    "response": response_text,
                    "format_used": best_arm,
                    "retrieved_docs": retrieved_docs,
                    "prompt_text": prompt_text,
                    "ucb_stats": ucb_stats,
                    "feedback_given": False,
                }

                # Log to Episodic Memory
                resources["episodic"].log_turn(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    query=active_query,
                    response=response_text,
                    format_used=best_arm,
                    resolution_status="IN_PROGRESS",
                    retrieved_sop_ids=[d.metadata.get("id") for d in retrieved_docs if d.metadata.get("id")],
                )

                # Append to Session Chat History
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text,
                    "format_badge": format_badge,
                    "doc_citations": doc_citations,
                })

        st.rerun()


# =========================================================================
# RIGHT COLUMN: COGNITIVE INSPECTOR (CLEAN, MODERATE-SIZED METRICS)
# =========================================================================
with right_col:
    st.markdown('<div class="col-header">🧠 Cognitive Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="col-subheader">Live Learning State & Policy Telemetry</div>', unsafe_allow_html=True)

    tab_profile, tab_bandit, tab_grounding, tab_graph, tab_episodic = st.tabs([
        "👤 Profile",
        "🎰 Bandit Math",
        "🧠 Memory",
        "🕸️ Graph",
        "📜 Audit",
    ])

    # --- TAB 1: OPERATOR BEHAVIORAL PROFILE ---
    with tab_profile:
        st.markdown("##### Competency & Autonomy")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(
                label="Machine Autonomy",
                value=f"{current_autonomy:.1f}%",
                help="Autonomy dynamically adjusts: +5 points on independent resolution, -15 points on escalation.",
            )
            st.progress(int(current_autonomy) / 100)

        with col_p2:
            st.metric(
                label="Dynamic Tier",
                value=current_tier,
                help=f"Computed from overall machine autonomy. HR Cold-Start Baseline: {op_profile.get('default_tier', 'Novice')}.",
            )

        st.write("")
        st.markdown("##### Machine Breakdown")
        for m in machines:
            score = resources["graph"].get_autonomy_score(selected_op_id, m)
            st.caption(f"**{m}:** `{score:.1f}%`")
            st.progress(int(score) / 100)

    # --- TAB 2: CONTEXTUAL BANDIT FORMAT EXPLORER ---
    with tab_bandit:
        st.markdown("##### Upper Confidence Bound (UCB)")
        st.caption("$$UCB_i = \\bar{X}_i + c \\cdot \\sqrt{\\frac{\\ln(N + 1)}{N_i + \\epsilon}}$$")

        ucb_data = resources["bandit"].calculate_ucb_scores(selected_op_id)
        
        bandit_rows = []
        for arm, stats in ucb_data.items():
            bandit_rows.append({
                "Arm": arm,
                "UCB Score": stats["ucb_score"],
                "Mean Reward": stats["mean_reward"],
                "Exploration Bonus": stats["exploration_bonus"],
                "Pulls": stats["pull_count"],
                "Total Weight": stats["weight"],
                "Solves": stats["success_count"],
                "Escalates": stats["escalation_count"],
            })

        df_bandit = pd.DataFrame(bandit_rows)
        winning_arm = max(ucb_data.keys(), key=lambda k: ucb_data[k]["ucb_score"])
        
        st.info(f"🏆 **Active Policy**: `{winning_arm}` (Score: `{ucb_data[winning_arm]['ucb_score']}`)")

        df_chart = pd.DataFrame({
            "UCB Score": [stats["ucb_score"] for stats in ucb_data.values()],
            "Mean Reward": [stats["mean_reward"] for stats in ucb_data.values()],
            "Exploration Bonus": [stats["exploration_bonus"] for stats in ucb_data.values()],
        }, index=list(ucb_data.keys()))
        
        st.bar_chart(df_chart, height=200, use_container_width=True)
        st.dataframe(df_bandit, use_container_width=True, hide_index=True)

    # --- TAB 3: WORKING MEMORY & GROUNDING SOPS ---
    with tab_grounding:
        st.markdown("##### Retrieved SOP Excerpts")

        if st.session_state.last_context and st.session_state.last_context.get("retrieved_docs"):
            docs = st.session_state.last_context["retrieved_docs"]
            st.caption(f"Retrieved `{len(docs)}` SOPs via Hybrid RRF Search:")

            for i, doc in enumerate(docs, 1):
                with st.expander(f"📄 [{doc.metadata.get('id', 'DOC')}] {doc.metadata.get('machine')} | RRF: {doc.metadata.get('rrf_score', 0):.4f}"):
                    st.json(doc.metadata)
                    st.markdown("**Content Excerpt:**")
                    st.text(doc.page_content)

            st.markdown("##### Assembled LLM Prompt")
            with st.expander("🔍 View Raw Working Memory Prompt"):
                st.code(st.session_state.last_context.get("prompt_text", ""), language="markdown")
        else:
            st.info("No active query in session. Enter a troubleshooting question to inspect working memory.")

    # --- TAB 4: SEMANTIC KNOWLEDGE GRAPH ---
    with tab_graph:
        st.markdown("##### NetworkX Semantic Graph")
        summary = resources["graph"].to_summary_dict(selected_op_id, selected_machine)
        st.json(summary)
        st.caption(f"Graph State: `{resources['graph'].state_file}`")

    # --- TAB 5: EPISODIC AUDIT LOG ---
    with tab_episodic:
        st.markdown("##### Episodic Audit Trail")
        episodes = resources["episodic"].get_recent_history(operator_id=selected_op_id, limit=8)

        if episodes:
            df_ep = pd.DataFrame(episodes)
            st.dataframe(
                df_ep[["timestamp", "machine_id", "format_used", "resolution_status", "ticket_id", "query"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No episodic records logged for this operator yet.")
