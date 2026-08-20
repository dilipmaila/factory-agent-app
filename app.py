"""
Manufacturing Operator AI Assistant - Streamlit Application.
Features:
1. Dynamic Procedural Memory (Bayesian Probabilistic Fault Trees).
2. State-Bound Cognitive Format Personalization (Decoupled UCB Contextual Bandit).
3. Synchronous Fast Event Queue (<100ms) with Asynchronous Sleep Cycle Batch Evaluation.
4. Safety & FMEA Guardrails:
   - Durability Window Escrow Queue (The Duct-Tape Safeguard).
   - Quarantined SOPs with 3-Expert Consensus Auto-Promotion.
   - Episodic Failure History & Proactive Escalation Warnings.
   - Explicit Format Overrides with -10.0 Mathematical Penalties.
5. Section 3 Contextual Enhancements:
   - Environmental Context Matrix (ECM): Fatigue Gate (100% Exploitation) & Offline Supervisor Gate.
   - Micro-Debrief Loop: Intercepts rapid fixes with human Y/N verification before quarantine.
"""

import os
import sys
import datetime
from pathlib import Path
from typing import Any, Dict, List
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

# Internal Imports
from mock_services.scada_service import MockSCADA
from mock_services.cmms_service import MockCMMS
from mock_services.hr_lms_service import MockHRLMS
from mock_services.ecm_service import generate_ecm_payload, ECMService
from memory.search import HybridRetriever
from memory.semantic_graph import OperatorKnowledgeGraph
from memory.procedural_memory import ProceduralMemory, calculate_branch_probability
from memory.episodic_store import EpisodicMemory
from memory.debrief_store import DebriefManager
from memory.working_memory import build_prompt
from agents.bandit_router import ContextualBandit
from agents.chat_agent import ManufacturingChatAgent
from agents.shadow_observer import ShadowObserver
from sleep_cycle_evaluator import SleepCycleEvaluator

# Set Page Config
st.set_page_config(
    page_title="Shopfloor AI Copilot | Adaptive Learning 3.0",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 0.93rem;
    }
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
    .col-header {
        font-size: 1.18rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 0px;
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .col-subheader {
        font-size: 0.78rem;
        color: #64748b;
        margin-bottom: 12px;
    }
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
        margin-right: 6px;
    }
    .procedural-pill {
        background: #064e3b;
        color: #6ee7b7;
        border: 1px solid #059669;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        display: inline-block;
        margin-bottom: 6px;
        margin-right: 6px;
    }
    .ecm-pill {
        background: #3b0764;
        color: #e9d5ff;
        border: 1px solid #7e22ce;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        display: inline-block;
        margin-bottom: 6px;
    }
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

    .debrief-box {
        background: #1e293b;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 14px;
    }
    button[data-baseweb="tab"] {
        padding-left: 8px !important;
        padding-right: 8px !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- 1. SINGLETON / RESOURCES INITIALIZATION ---
@st.cache_resource
def get_shared_resources():
    chroma_dir = DATA_DIR / "chroma_db"
    bm25_file = DATA_DIR / "bm25_retriever.pkl"
    graph_file = DATA_DIR / "graph_state.json"
    procedural_file = DATA_DIR / "procedural_fault_trees.json"
    quarantine_file = DATA_DIR / "quarantine_sops.json"
    log_file = DATA_DIR / "episodic_logs.json"
    queue_file = DATA_DIR / "episodic_event_queue.json"
    escrow_file = DATA_DIR / "escrow_rewards.json"
    debrief_file = DATA_DIR / "pending_debriefs.json"

    scada = MockSCADA()
    cmms = MockCMMS()
    hr_lms = MockHRLMS()
    ecm_svc = ECMService()
    graph = OperatorKnowledgeGraph(state_file=str(graph_file))
    procedural = ProceduralMemory(data_file=str(procedural_file), quarantine_file=str(quarantine_file))
    episodic = EpisodicMemory(log_file=str(log_file), queue_file=str(queue_file), escrow_file=str(escrow_file))
    debrief = DebriefManager(debrief_file=str(debrief_file))

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
        episodic_memory=episodic,
        cmms_service=cmms,
        scada_service=scada,
        debrief_manager=debrief,
    )

    sleep_evaluator = SleepCycleEvaluator(
        knowledge_graph=graph,
        procedural_memory=procedural,
        episodic_memory=episodic,
        scada_service=scada,
    )

    return {
        "scada": scada,
        "cmms": cmms,
        "hr_lms": hr_lms,
        "ecm_svc": ecm_svc,
        "graph": graph,
        "procedural": procedural,
        "episodic": episodic,
        "debrief": debrief,
        "retriever": retriever,
        "bandit": bandit,
        "chat_agent": chat_agent,
        "observer": observer,
        "sleep_evaluator": sleep_evaluator,
    }


resources = get_shared_resources()

# Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_context" not in st.session_state:
    st.session_state.last_context = None
if "current_operator_id" not in st.session_state:
    st.session_state.current_operator_id = "OP-002"  # Sarah Jenkins
if "current_machine" not in st.session_state:
    st.session_state.current_machine = "Haas VF-2"
if "feedback_status" not in st.session_state:
    st.session_state.feedback_status = None
if "shift_hours_in" not in st.session_state:
    st.session_state.shift_hours_in = 2.5
if "supervisor_on_site" not in st.session_state:
    st.session_state.supervisor_on_site = True


# --- 2. SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.title("🏭 Factory Hub")
    st.caption("Adaptive Operator Intelligence 3.0")
    st.markdown("---")

    # Section A: Operator Profile
    st.markdown("##### 👤 Active Operator")
    operators = resources["hr_lms"].get_all_operators()
    op_options = {
        f"{op['name']} ({op['operator_id']})": op["operator_id"]
        for op in operators
    }

    selected_label = st.selectbox(
        "Select Active Operator",
        options=list(op_options.keys()),
        index=1 if "Sarah Jenkins (OP-002)" in op_options else 0,
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
        st.caption(f"**Role:** {op_profile.get('role')} | **Shift:** {op_profile.get('shift')}")

    st.markdown("---")

    # Section B: Machine Selection & Confidence
    st.markdown("##### ⚙️ Workcell Machine")
    machines = ["Haas VF-2", "Engel Victory 330"]
    selected_machine = st.selectbox("Active Machine", options=machines, index=0, label_visibility="collapsed")
    if selected_machine != st.session_state.current_machine:
        st.session_state.current_machine = selected_machine
        st.session_state.feedback_status = None
        st.rerun()

    m_comp = resources["graph"].get_machine_competence(selected_op_id, selected_machine)
    machine_autonomy = m_comp["autonomy_score"]
    machine_tier = m_comp["derived_tier"]

    tier_class = f"tier-{machine_tier.lower()}"
    st.markdown(
        f"""
        <div style="background:#0f172a; padding:8px 12px; border-radius:6px; border:1px solid #1e293b; margin-top:4px;">
            <div style="font-size:0.75rem; color:#94a3b8;">MACHINE CONFIDENCE:</div>
            <div style="font-weight:700; color:#f8fafc; font-size:1.0rem;">
                {selected_machine}: <span class="tier-tag {tier_class}">{machine_tier}</span> ({machine_autonomy:.1f}%)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("##### 📡 SCADA Telemetry State")
    active_alarm = resources["scada"].get_active_alarm(selected_machine)

    if "Normal" in active_alarm:
        st.success(f"🟢 **{active_alarm}**")
    else:
        st.error(f"🚨 **{active_alarm}**")

    # Alarm Simulation Controls
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

    # Section 3.A: Environmental Context Matrix (ECM) Controls
    st.markdown("##### 🌐 Physical Context Matrix (ECM)")
    shift_hours = st.slider(
        "Shift Hour (Fatigue Gauge)",
        min_value=0.5,
        max_value=12.0,
        value=float(st.session_state.shift_hours_in),
        step=0.5,
        help="Simulates hours elapsed since operator clocked in. At >= 80% of shift, Fatigue Gate forces 100% exploitation.",
    )
    st.session_state.shift_hours_in = shift_hours

    sup_on_site = st.checkbox(
        "Supervisor On-Site",
        value=bool(st.session_state.supervisor_on_site),
        help="When unchecked (supervisor offline), AI enforces strict safety checks and blocks Level 2 escalation.",
    )
    st.session_state.supervisor_on_site = sup_on_site

    # Compute current ECM payload
    current_ecm = generate_ecm_payload(
        operator_id=selected_op_id,
        machine_id=selected_machine,
        hours_since_clock_in=shift_hours,
        total_shift_hours=12.0 if "OP-002" in selected_op_id else 8.0,
        supervisor_available=sup_on_site,
    )

    if current_ecm["fatigue_gate_active"]:
        st.error(f"⚡ **Fatigue Gate ACTIVE** (`{current_ecm['fatigue_index']*100:.0f}%` - 100% Exploit)")
    else:
        st.info(f"🟢 Fatigue Index: `{current_ecm['fatigue_index']*100:.0f}%` (Balanced UCB)")

    if current_ecm["supervisor_gate_active"]:
        st.warning("🚨 **Supervisor Gate ACTIVE** (Offline Override)")

    st.markdown("---")

    # Sleep Cycle & Reset Controls
    pending_events_count = len(resources["episodic"].get_pending_events())
    escrow_count = len(resources["episodic"].get_escrow_records())

    st.markdown("##### 🛡️ Safety Escrow & Batch")
    st.caption(f"Shift Events: `{pending_events_count}` | Escrow Held: `{escrow_count}`")

    if st.button("🌙 Run Sleep Cycle (Batch)", use_container_width=True):
        batch_res = resources["sleep_evaluator"].run_sleep_cycle(force_mature_escrow=True)
        st.toast(f"Sleep Cycle completed: {batch_res['processed_events']} events, {batch_res['processed_escrow']} escrow.", icon="🌙")
        st.rerun()

    st.write("")
    if st.button("♻️ Reset Defaults", use_container_width=True):
        resources["graph"]._seed_default_graph()
        resources["graph"].save_to_file()
        resources["episodic"].clear_event_queue()
        resources["episodic"].clear_escrow_records()
        st.session_state.chat_history = []
        st.session_state.last_context = None
        st.session_state.feedback_status = None
        st.session_state.shift_hours_in = 2.5
        st.session_state.supervisor_on_site = True
        st.toast("System reset to baseline!", icon="♻️")
        st.rerun()


# --- 3. MAIN DASHBOARD LAYOUT (2 COLUMNS) ---
left_col, right_col = st.columns([1.15, 0.85], gap="large")

# =========================================================================
# LEFT COLUMN: COPILOT CHAT, MICRO-DEBRIEF INTERCEPT, ECM OVERRIDES
# =========================================================================
with left_col:
    st.markdown(f'<div class="col-header">💬 Shopfloor AI Copilot — {selected_machine}</div>', unsafe_allow_html=True)

    tier_badge_class = f"tier-{machine_tier.lower()}"
    st.markdown(
        f"""
        <div class="col-subheader">
            Operator: <strong>{op_profile.get('name', selected_op_id)}</strong> &nbsp;|&nbsp; 
            Machine Tier: <span class="tier-tag {tier_badge_class}">{machine_tier}</span> &nbsp;|&nbsp; 
            Autonomy: <strong>{machine_autonomy:.1f}%</strong> &nbsp;|&nbsp;
            Fatigue: <strong>{current_ecm['fatigue_index']*100:.0f}%</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- SECTION 3.B: THE MICRO-DEBRIEF LOOP INTERCEPT ---
    pending_debriefs = resources["debrief"].get_pending_debriefs(selected_op_id)
    if pending_debriefs:
        active_deb = pending_debriefs[0]
        st.markdown(
            f"""
            <div class="debrief-box">
                <div style="font-weight:700; color:#f59e0b; font-size:0.95rem; margin-bottom:4px;">
                    🤖 Copilot Micro-Debrief Inquiry
                </div>
                <div style="font-size:0.88rem; color:#e2e8f0; margin-bottom:8px;">
                    Earlier you resolved <strong>{active_deb['fault_code']}</strong> in <strong>~{active_deb['actual_time_mins']} min</strong> 
                    (Standard SOP takes ~{active_deb['sop_avg_time_mins']} min).<br>
                    <strong>Did you use the '{active_deb['suspected_shortcut_title']}'?</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if st.button("✅ Yes, I used that shortcut", key=f"deb_yes_{active_deb['debrief_id']}", use_container_width=True):
                deb_res = resources["debrief"].process_debrief_response(
                    debrief_id=active_deb["debrief_id"],
                    confirmed=True,
                    procedural_memory=resources["procedural"],
                )
                st.toast(deb_res["message"], icon="🧪")
                st.rerun()

        with d_col2:
            if st.button("❌ No, standard procedure", key=f"deb_no_{active_deb['debrief_id']}", use_container_width=True):
                deb_res = resources["debrief"].process_debrief_response(
                    debrief_id=active_deb["debrief_id"],
                    confirmed=False,
                    procedural_memory=resources["procedural"],
                )
                st.toast(deb_res["message"], icon="🗑️")
                st.rerun()

        st.markdown("---")

    # Check for historical failure patterns
    past_escalations = resources["episodic"].get_operator_fault_history(selected_op_id, active_alarm)
    if past_escalations and "Normal" not in active_alarm:
        st.warning(
            f"⚠️ **Historical Failure Pattern**: {op_profile.get('name', selected_op_id)} has escalated "
            f"**{active_alarm}** `{len(past_escalations)}` time(s). Proactive assistance enabled."
        )

    # Render Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="👨‍🔧" if msg["role"] == "user" else "🤖"):
            if msg.get("format_badge"):
                st.markdown(f"<span class='format-pill'>{msg['format_badge']}</span>", unsafe_allow_html=True)
            if msg.get("procedural_badge"):
                st.markdown(f"<span class='procedural-pill'>{msg['procedural_badge']}</span>", unsafe_allow_html=True)
            if msg.get("ecm_badge"):
                st.markdown(f"<span class='ecm-pill'>{msg['ecm_badge']}</span>", unsafe_allow_html=True)
            st.markdown(msg["content"])
            if msg.get("doc_citations"):
                with st.expander("📚 Grounding References"):
                    for doc_ref in msg["doc_citations"]:
                        st.caption(f"• **{doc_ref['id']}** ({doc_ref['machine']}) — RRF: `{doc_ref['score']:.4f}`")

    # --- EXPLICIT FORMAT OVERRIDE BAR ---
    if st.session_state.chat_history and st.session_state.last_context:
        last_fmt = st.session_state.last_context.get("format_used")
        st.markdown(
            "<p style='font-size:0.80rem; color:#64748b; margin-top:8px; margin-bottom:4px;'>⚡ <strong>Format Override</strong>: Switch presentation style instantly:</p>",
            unsafe_allow_html=True,
        )
        ov_col1, ov_col2, ov_col3 = st.columns(3)
        with ov_col1:
            if st.button("Terse Technical", use_container_width=True, key="ov_terse", disabled=(last_fmt == "Terse_Technical")):
                req_fmt, new_instr, _ = resources["bandit"].trigger_format_override(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    rejected_format=last_fmt,
                    requested_format="Terse_Technical",
                )
                prompt_regen = build_prompt(
                    safety_warnings=["Lock-Out/Tag-Out mandatory."],
                    bandit_format_instruction=new_instr,
                    retrieved_sops=st.session_state.last_context.get("retrieved_docs", []),
                    user_query=st.session_state.last_context.get("query", ""),
                    operator_context={"name": op_profile.get("name"), "derived_tier": machine_tier, "machine_id": selected_machine, "autonomy_score": machine_autonomy},
                    procedural_context_text=resources["procedural"].format_procedural_context(st.session_state.last_context.get("procedural_matches", [])),
                    ecm_payload=current_ecm,
                )
                new_resp = resources["chat_agent"].generate_response(prompt_regen) if resources["chat_agent"] else f"[Terse Technical Override]\n\nParameters: M06, Air: 90 PSI."
                st.session_state.chat_history[-1] = {
                    "role": "assistant",
                    "content": new_resp,
                    "format_badge": f"OVERRIDE: {req_fmt} ({machine_tier})",
                }
                st.session_state.last_context["format_used"] = req_fmt
                st.toast("Hard Override applied (-10.0 penalty to rejected format).", icon="⚡")
                st.rerun()

        with ov_col2:
            if st.button("Visual Step-by-Step", use_container_width=True, key="ov_visual", disabled=(last_fmt == "Visual_StepByStep")):
                req_fmt, new_instr, _ = resources["bandit"].trigger_format_override(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    rejected_format=last_fmt,
                    requested_format="Visual_StepByStep",
                )
                prompt_regen = build_prompt(
                    safety_warnings=["Lock-Out/Tag-Out mandatory."],
                    bandit_format_instruction=new_instr,
                    retrieved_sops=st.session_state.last_context.get("retrieved_docs", []),
                    user_query=st.session_state.last_context.get("query", ""),
                    operator_context={"name": op_profile.get("name"), "derived_tier": machine_tier, "machine_id": selected_machine, "autonomy_score": machine_autonomy},
                    procedural_context_text=resources["procedural"].format_procedural_context(st.session_state.last_context.get("procedural_matches", [])),
                    ecm_payload=current_ecm,
                )
                new_resp = resources["chat_agent"].generate_response(prompt_regen) if resources["chat_agent"] else f"[Visual Step-by-Step Override]\n\n1. [ACTION] Check pressure."
                st.session_state.chat_history[-1] = {
                    "role": "assistant",
                    "content": new_resp,
                    "format_badge": f"OVERRIDE: {req_fmt} ({machine_tier})",
                }
                st.session_state.last_context["format_used"] = req_fmt
                st.toast("Hard Override applied (-10.0 penalty to rejected format).", icon="⚡")
                st.rerun()

        with ov_col3:
            if st.button("Detailed Tutorial", use_container_width=True, key="ov_detailed", disabled=(last_fmt == "Detailed_Text")):
                req_fmt, new_instr, _ = resources["bandit"].trigger_format_override(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    rejected_format=last_fmt,
                    requested_format="Detailed_Text",
                )
                prompt_regen = build_prompt(
                    safety_warnings=["Lock-Out/Tag-Out mandatory."],
                    bandit_format_instruction=new_instr,
                    retrieved_sops=st.session_state.last_context.get("retrieved_docs", []),
                    user_query=st.session_state.last_context.get("query", ""),
                    operator_context={"name": op_profile.get("name"), "derived_tier": machine_tier, "machine_id": selected_machine, "autonomy_score": machine_autonomy},
                    procedural_context_text=resources["procedural"].format_procedural_context(st.session_state.last_context.get("procedural_matches", [])),
                    ecm_payload=current_ecm,
                )
                new_resp = resources["chat_agent"].generate_response(prompt_regen) if resources["chat_agent"] else f"[Detailed Tutorial Override]\n\nIn-depth electro-mechanical explanation."
                st.session_state.chat_history[-1] = {
                    "role": "assistant",
                    "content": new_resp,
                    "format_badge": f"OVERRIDE: {req_fmt} ({machine_tier})",
                }
                st.session_state.last_context["format_used"] = req_fmt
                st.toast("Hard Override applied (-10.0 penalty to rejected format).", icon="⚡")
                st.rerun()

    # --- RESOLUTION FEEDBACK PROMPT ---
    if st.session_state.chat_history and st.session_state.last_context and not st.session_state.last_context.get("feedback_given"):
        st.markdown(
            "<p style='font-size:0.85rem; color:#94a3b8; margin-top:12px; margin-bottom:6px; font-style:italic;'>Did this guidance resolve the machine issue?</p>",
            unsafe_allow_html=True,
        )

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            if st.button("✅ Solved Independently", use_container_width=True, key="btn_solve_feedback"):
                last_ctx = st.session_state.last_context
                eval_res = resources["observer"].evaluate_session(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    format_used=last_ctx.get("format_used", "Visual_StepByStep"),
                    escalated=False,
                    cognitive_tier=machine_tier,
                    error_code=last_ctx.get("matched_error_code"),
                    path_id=last_ctx.get("primary_path_id"),
                    execution_time_mins=2.0,  # Fast triage simulated
                    sop_avg_time_mins=10.0,
                    query=last_ctx.get("query", ""),
                    response=last_ctx.get("response", ""),
                )
                st.session_state.last_context["feedback_given"] = True
                st.session_state.feedback_status = f"✅ Resolved independently! Reward in Escrow. ({eval_res['latency_ms']} ms)."
                st.toast(f"Reward Held in Escrow ({eval_res['latency_ms']}ms)", icon="🛡️")
                st.rerun()

        with f_col2:
            if st.button("⚠️ Escalate to Supervisor", use_container_width=True, key="btn_escalate_feedback"):
                last_ctx = st.session_state.last_context
                eval_res = resources["observer"].evaluate_session(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    format_used=last_ctx.get("format_used", "Visual_StepByStep"),
                    escalated=True,
                    cognitive_tier=machine_tier,
                    error_code=last_ctx.get("matched_error_code"),
                    path_id=last_ctx.get("primary_path_id"),
                    issue_desc=f"Escalated from turn: {last_ctx.get('query', 'N/A')}",
                    query=last_ctx.get("query", ""),
                    response=last_ctx.get("response", ""),
                )
                st.session_state.last_context["feedback_given"] = True
                st.session_state.feedback_status = f"⚠️ Escalated to maintenance ({eval_res['ticket_id']}). Logged in {eval_res['latency_ms']} ms."
                st.toast(f"Escalation Dispatched: {eval_res['ticket_id']} ({eval_res['latency_ms']}ms)", icon="🚨")
                st.rerun()

    elif st.session_state.feedback_status:
        if "✅" in st.session_state.feedback_status:
            st.success(st.session_state.feedback_status)
        else:
            st.warning(st.session_state.feedback_status)

    # Quick Shopfloor Prompts
    st.markdown("---")
    st.caption("⚡ Quick Shopfloor Prompts:")
    sample_queries = {
        "Haas VF-2": [
            "How do I clear Alarm 102 (Servos Off)?",
            "X Axis SERVO ERROR TOO LARGE (Alarm 103)",
            "What G-code is used for peck drilling cycles?",
        ],
        "Engel Victory 330": [
            "How do I fix barrel temperature overheat in Zone 2 (E-201)?",
            "What are the resolution steps for low hydraulic clamping pressure (E-105)?",
            "How do I safely purge the injection screw before mold change?",
        ],
    }

    quick_cols = st.columns(len(sample_queries.get(selected_machine, [])))
    prompt_to_send = None
    for idx, sample_q in enumerate(sample_queries.get(selected_machine, [])):
        with quick_cols[idx]:
            if st.button(sample_q, key=f"quick_{idx}", use_container_width=True):
                prompt_to_send = sample_q

    user_input = st.chat_input("Ask about machine alarms, M-codes, SOPs, or mechanical repairs...")
    active_query = prompt_to_send or user_input

    if active_query:
        st.session_state.feedback_status = None
        st.session_state.chat_history.append({"role": "user", "content": active_query})

        with st.chat_message("user", avatar="👨‍🔧"):
            st.markdown(active_query)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Retrieving procedural fault trees & personalizing..."):
                # A. Retrieve Active Procedural Fault Trees
                procedural_matches = resources["procedural"].search(
                    active_query,
                    machine=selected_machine,
                    operator_tier=machine_tier,
                )
                procedural_context = resources["procedural"].format_procedural_context(procedural_matches)

                matched_error = procedural_matches[0].get("error_code") if procedural_matches else None
                primary_path = (
                    procedural_matches[0]["diagnostic_paths"][0].get("path_id")
                    if procedural_matches and procedural_matches[0].get("diagnostic_paths")
                    else None
                )

                # B. Check Historical Failure Logs
                escalation_history = resources["episodic"].get_operator_fault_history(
                    operator_id=selected_op_id,
                    error_code=matched_error or active_query,
                )

                # C. Retrieve Static Grounding SOPs
                retrieved_docs = []
                if resources["retriever"]:
                    try:
                        retrieved_docs = resources["retriever"].search(
                            query=active_query,
                            top_k=2,
                            filter_dict={"machine": selected_machine},
                        )
                    except Exception:
                        retrieved_docs = resources["retriever"].search(query=active_query, top_k=2)

                # D. UCB Bandit Format Selection with ECM Fatigue Gate
                best_arm, arm_instruction, ucb_stats, active_tier = resources["bandit"].select_format(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    ecm_payload=current_ecm,
                )

                # E. Assemble Working Memory Prompt with ECM Directives
                safety_rules = [
                    "Lock-Out / Tag-Out (LOTO) mandatory before opening electrical enclosures.",
                    "Wear protective heat-resistant gloves and safety glasses during high temp maintenance.",
                    "Verify zero pneumatic line pressure before disconnecting air fittings.",
                ]
                op_ctx = {
                    "name": op_profile.get("name", selected_op_id),
                    "derived_tier": active_tier,
                    "machine_id": selected_machine,
                    "active_alarm": active_alarm,
                    "autonomy_score": machine_autonomy,
                }

                prompt_text = build_prompt(
                    safety_warnings=safety_rules,
                    bandit_format_instruction=arm_instruction,
                    retrieved_sops=retrieved_docs,
                    user_query=active_query,
                    operator_context=op_ctx,
                    procedural_context_text=procedural_context,
                    escalation_history=escalation_history,
                    ecm_payload=current_ecm,
                )

                # F. Generate LLM Response
                if resources["chat_agent"]:
                    response_text = resources["chat_agent"].generate_response(prompt_text, active_query)
                else:
                    response_text = f"[Simulation Mode]\n\nStandard SOP Guidance for **{active_query}** under **{best_arm}** ({active_tier} Mode)."

                # G. Badges
                format_badge = f"Bandit Arm: {best_arm} ({active_tier} State)"
                st.markdown(f"<span class='format-pill'>{format_badge}</span>", unsafe_allow_html=True)

                procedural_badge = None
                if procedural_matches:
                    procedural_badge = f"🌳 Fault Tree: {procedural_matches[0].get('error_code')}"
                    st.markdown(f"<span class='procedural-pill'>{procedural_badge}</span>", unsafe_allow_html=True)

                ecm_badge = None
                if current_ecm["fatigue_gate_active"]:
                    ecm_badge = "⚡ Fatigue Gate: 100% Exploit"
                    st.markdown(f"<span class='ecm-pill'>{ecm_badge}</span>", unsafe_allow_html=True)

                st.markdown(response_text)

                doc_citations = [
                    {"id": d.metadata.get("id", "SOP"), "machine": d.metadata.get("machine", selected_machine), "score": d.metadata.get("rrf_score", 0.0)}
                    for d in retrieved_docs
                ]

                st.session_state.last_context = {
                    "query": active_query,
                    "response": response_text,
                    "format_used": best_arm,
                    "active_tier": active_tier,
                    "matched_error_code": matched_error,
                    "primary_path_id": primary_path,
                    "retrieved_docs": retrieved_docs,
                    "procedural_matches": procedural_matches,
                    "prompt_text": prompt_text,
                    "ucb_stats": ucb_stats,
                    "feedback_given": False,
                }

                resources["episodic"].log_turn(
                    operator_id=selected_op_id,
                    machine_id=selected_machine,
                    query=active_query,
                    response=response_text,
                    format_used=best_arm,
                    resolution_status="IN_PROGRESS",
                    error_code=matched_error,
                    retrieved_sop_ids=[d.metadata.get("id") for d in retrieved_docs if d.metadata.get("id")],
                )

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text,
                    "format_badge": format_badge,
                    "procedural_badge": procedural_badge,
                    "ecm_badge": ecm_badge,
                    "doc_citations": doc_citations,
                })

        st.rerun()


# =========================================================================
# RIGHT COLUMN: COGNITIVE INSPECTOR (ECM, DEBRIEF, FMEA)
# =========================================================================
with right_col:
    st.markdown('<div class="col-header">🧠 Cognitive & Safety Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="col-subheader">FMEA Guardrails, Quarantined SOPs & ECM Context</div>', unsafe_allow_html=True)

    tab_profile, tab_bandit, tab_ecm, tab_debrief, tab_procedural, tab_quarantine = st.tabs([
        "👤 Profile",
        "🎰 Bandit",
        "🌐 ECM",
        "📋 Debrief",
        "🌳 Procedural",
        "🧪 Quarantine",
    ])

    # --- TAB 1: OPERATOR PROFILE ---
    with tab_profile:
        st.markdown(f"##### Machine Confidence: {selected_machine}")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric("Machine Autonomy", f"{machine_autonomy:.1f}%")
            st.progress(int(machine_autonomy) / 100)
        with col_p2:
            st.metric("Derived Tier", machine_tier)

        st.write("")
        st.markdown("##### Multi-Machine Autonomy Breakdown")
        for m in machines:
            comp = resources["graph"].get_machine_competence(selected_op_id, m)
            st.caption(f"**{m}:** `{comp['autonomy_score']:.1f}%` ({comp['derived_tier']})")
            st.progress(int(comp["autonomy_score"]) / 100)

    # --- TAB 2: BANDIT MATH ---
    with tab_bandit:
        st.markdown(f"##### UCB Math for Tier: `{machine_tier}`")
        ucb_data = resources["bandit"].calculate_ucb_scores(
            selected_op_id,
            machine_tier,
            exploration_override_c=0.0 if current_ecm["fatigue_gate_active"] else None,
        )
        bandit_rows = [
            {"Arm": arm, "UCB Score": stats["ucb_score"], "Mean Reward": stats["mean_reward"], "Weight": stats["weight"], "Pulls": stats["pull_count"]}
            for arm, stats in ucb_data.items()
        ]
        df_bandit = pd.DataFrame(bandit_rows)
        winning_arm = max(ucb_data.keys(), key=lambda k: ucb_data[k]["ucb_score"])
        st.info(f"🏆 **Active Policy**: `{winning_arm}` {'(Fatigue Exploit Mode)' if current_ecm['fatigue_gate_active'] else ''}")
        st.dataframe(df_bandit, use_container_width=True, hide_index=True)

    # --- TAB 3: SECTION 3.A ENVIRONMENTAL CONTEXT MATRIX (ECM) ---
    with tab_ecm:
        st.markdown("##### 🌐 Live Environmental Context Matrix (ECM)")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("Shift Progress", f"{current_ecm['hours_since_clock_in']}/{current_ecm['total_shift_hours']} h")
            st.metric("Fatigue Index", f"{current_ecm['fatigue_index']*100:.1f}%")
        with col_e2:
            st.metric("Shift Phase", current_ecm["shift_phase"])
            st.metric("Supervisor", "On-Site" if current_ecm["supervisor_available"] else "OFFLINE")

        st.write("")
        st.markdown("##### Active Logic Gates:")
        if current_ecm["fatigue_gate_active"]:
            st.error("🚨 **Fatigue Gate ON**: Exploration forced to 0.0 (Exploiting fastest format).")
        else:
            st.success("🟢 **Fatigue Gate OFF**: Standard exploration active.")

        if current_ecm["supervisor_gate_active"]:
            st.warning("🚨 **Supervisor Gate ON**: Prompt restricts Level 2 escalation suggestions.")
        else:
            st.success("🟢 **Supervisor Gate OFF**: Standard escalation permitted.")

    # --- TAB 4: SECTION 3.B MICRO-DEBRIEF STORE ---
    with tab_debrief:
        st.markdown("##### 📋 Micro-Debrief Records")
        st.caption("Turns probabilistic telemetry guesses into deterministic verified SOPs.")

        all_debriefs = resources["debrief"].debriefs
        if all_debriefs:
            df_deb = pd.DataFrame(all_debriefs)
            st.dataframe(
                df_deb[["debrief_id", "operator_id", "fault_code", "suspected_shortcut_title", "status"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No micro-debrief records in queue.")

    # --- TAB 5: ACTIVE PROCEDURAL MEMORY ---
    with tab_procedural:
        st.markdown("##### Active Verified Skill Library")
        all_trees = resources["procedural"].get_all_trees(operator_tier=machine_tier)
        for tree in all_trees:
            with st.expander(f"🌳 {tree.get('error_code')} - {tree.get('title')} ({tree.get('machine')})"):
                for rank, path in enumerate(tree.get("diagnostic_paths", []), 1):
                    prob = path.get("probability_score", 0.5) * 100
                    req_tag = f" `[Clearance: {path.get('min_tier_required')}]`" if path.get("min_tier_required") else ""
                    st.markdown(f"**Rank {rank}: {path.get('title')}**{req_tag} (`{prob:.1f}%` Prob | ~`{path.get('avg_execution_time_mins')}` min)")
                    st.progress(int(prob) / 100)

    # --- TAB 6: QUARANTINE DATABASE ---
    with tab_quarantine:
        st.markdown("##### 🧪 Quarantine Candidate Shortcuts")
        quarantine_trees = resources["procedural"].get_quarantined_trees()
        if quarantine_trees:
            for q_tree in quarantine_trees:
                st.markdown(f"**Alarm:** `{q_tree.get('error_code')}` — {q_tree.get('title')} ({q_tree.get('machine')})")
                for q_path in q_tree.get("diagnostic_paths", []):
                    validators = q_path.get("validated_by_senior_operators", [])
                    st.warning(
                        f"⚠️ **Candidate Shortcut:** {q_path.get('title')}\n\n"
                        f"• **Senior Expert Signatures:** `{len(validators)}/3` ({', '.join(validators) if validators else 'None'})\n\n"
                        f"• **Steps:** {q_path.get('resolution_steps')}"
                    )
                    if machine_tier == "Expert":
                        if st.button(f"✍️ Sign Off as Senior Operator ({op_profile.get('name', selected_op_id)})", key=f"val_{q_path.get('path_id')}", use_container_width=True):
                            val_res = resources["procedural"].validate_quarantine_sop(
                                error_code=q_tree.get("error_code"),
                                path_id=q_path.get("path_id"),
                                operator_id=selected_op_id,
                                operator_tier=machine_tier,
                            )
                            if val_res.get("promoted"):
                                st.success("🎉 Consensus reached! Promoted to Active Skill Library.")
                            else:
                                st.info(f"Signature recorded ({val_res.get('count')}/3).")
                            st.rerun()
        else:
            st.success("✅ Quarantine database is empty. All active SOPs are verified.")
