"""
Working Memory Module.
Constructs structured, dynamically formatted system prompts combining real-time SCADA telemetry,
Dynamic Procedural Memory (Bayesian Probabilistic Fault Trees), Environmental Context Matrix (ECM) Overrides,
historical failure/escalation warnings, safety hazard directives, and Contextual Bandit formatting constraints.
"""

from typing import List, Union, Optional, Dict, Any
from langchain_core.documents import Document


def build_prompt(
    safety_warnings: Union[List[str], str],
    bandit_format_instruction: str,
    retrieved_sops: List[Union[Document, Dict[str, Any], str]],
    user_query: str,
    operator_context: Optional[Dict[str, Any]] = None,
    procedural_fault_trees: Optional[List[Dict[str, Any]]] = None,
    procedural_context_text: Optional[str] = None,
    escalation_history: Optional[List[Dict[str, Any]]] = None,
    ecm_payload: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Assembles the complete working memory prompt for the LLM.
    
    Args:
        safety_warnings: Critical shopfloor hazards, PPE requirements, or lock-out/tag-out rules.
        bandit_format_instruction: Strict formatting guidelines dictated by the Contextual Bandit router.
        retrieved_sops: List of LangChain Document objects or strings retrieved via Hybrid Search.
        user_query: The immediate question, error description, or alarm query from the operator.
        operator_context: Metadata containing operator name, machine-specific derived tier, and autonomy score.
        procedural_fault_trees: Optional list of dynamic fault tree dicts with ranked diagnostic paths.
        procedural_context_text: Optional pre-formatted procedural memory text string.
        escalation_history: Optional list of past failed/escalated sessions for this operator on this fault.
        ecm_payload: Optional Environmental Context Matrix (ECM) payload with shift/fatigue and supervisor state.
        
    Returns:
        Structured system + user prompt string ready for LLM generation.
    """
    # 1. Format Safety Warnings
    if isinstance(safety_warnings, list):
        safety_text = "\n".join(f"- ⚠️ {w}" for w in safety_warnings) if safety_warnings else "- Standard OSHA & Shopfloor Safety protocols apply."
    else:
        safety_text = f"- ⚠️ {safety_warnings}" if safety_warnings else "- Standard OSHA & Shopfloor Safety protocols apply."

    # 2. Format ECM Overrides (The Supervisor Gate & Fatigue Awareness)
    ecm_section = ""
    if ecm_payload:
        sup_available = ecm_payload.get("supervisor_available", True)
        fatigue_idx = ecm_payload.get("fatigue_index", 0.0)
        hrs_in = ecm_payload.get("hours_since_clock_in", 2.0)
        tot_hrs = ecm_payload.get("total_shift_hours", 8.0)

        directives = []
        if not sup_available:
            directives.append(
                "🚨 **SYSTEM OVERRIDE (SUPERVISOR OFFLINE)**: Shift Supervisor is currently OFFLINE / Off-Site. "
                "Provide mandatory safety checks and do NOT suggest escalating to Level 2 Maintenance. "
                "Operator must resolve independently or safely halt production."
            )
        if fatigue_idx >= 0.80:
            directives.append(
                f"⏱️ **FATIGUE GATE ACTIVE**: Operator is at Hour {hrs_in}/{tot_hrs} of shift (Fatigue Index: {fatigue_idx*100:.0f}%). "
                "Output MUST be ultra-scannable and free of conversational filler."
            )

        if directives:
            ecm_section = "### ENVIRONMENTAL CONTEXT MATRIX (ECM) ACTIVE DIRECTIVES\n" + "\n".join(f"- {d}" for d in directives) + "\n"

    # 3. Format Historical Escalation Warnings (Section 2.C)
    escalation_section = ""
    if escalation_history:
        fail_count = len(escalation_history)
        op_name = operator_context.get("name", "This operator") if operator_context else "This operator"
        escalation_section = f"""### HISTORICAL ESCALATION WARNING & PROACTIVE DISPATCH PROTOCOL
- ⚠️ **SYSTEM ALERT**: {op_name} has historically experienced repeated difficulties and escalated this exact fault code ({fail_count} prior escalation(s) recorded in episodic logs).
- **CONVERSATIONAL DIRECTIVE**: Proactively acknowledge this persistent issue in your response. Along with standard guidance, explicitly offer to dispatch Level 2 Maintenance or open a CMMS work order early if the operator expresses frustration, confusion, or if the primary fix does not immediately clear the fault.
"""

    # 4. Format Dynamic Procedural Memory (Bayesian Fault Trees & Anti-Patterns)
    procedural_section = ""
    if procedural_context_text:
        procedural_section = f"""### DYNAMIC PROCEDURAL MEMORY (BAYESIAN FAULT TREES & RANKED SOLUTIONS)
{procedural_context_text}
"""
    elif procedural_fault_trees:
        tree_blocks = []
        for tree in procedural_fault_trees:
            paths = tree.get("diagnostic_paths", [])
            p_lines = [
                f"**Fault Tree: {tree.get('error_code')} - {tree.get('title')} ({tree.get('machine')})**"
            ]
            for rank, p in enumerate(paths, 1):
                prob_pct = p.get("probability_score", 0.5) * 100
                tag = "RECOMMENDED PRIMARY FIX" if rank == 1 else f"BACKUP FIX {rank}"
                p_lines.append(
                    f"[{tag}] {p.get('title')} (ID: {p.get('path_id')} | Historical Success: {prob_pct:.1f}% | Est: ~{p.get('avg_execution_time_mins')} min)\n"
                    f"• Description: {p.get('description')}\n"
                    f"• Steps:\n{p.get('resolution_steps')}\n"
                    f"• Prohibited: {p.get('prohibited_actions', 'None')}"
                )
            
            # Anti-patterns
            anti_patterns = tree.get("anti_patterns", [])
            if anti_patterns:
                p_lines.append("⚠️ **CRITICAL ANTI-PATTERNS (WHAT NOT TO DO)**:")
                for ap in anti_patterns:
                    p_lines.append(f"- ❌ DO NOT: {ap.get('action')} (Consequence: {ap.get('consequence')} | Risk: {ap.get('escalation_risk', 'High')})")

            tree_blocks.append("\n\n".join(p_lines))
        if tree_blocks:
            procedural_section = f"""### DYNAMIC PROCEDURAL MEMORY (BAYESIAN FAULT TREES & RANKED SOLUTIONS)
{chr(10).join(tree_blocks)}
"""

    # 5. Format Retrieved Grounding SOPs & Manual Documents
    sops_formatted = []
    for idx, doc in enumerate(retrieved_sops, 1):
        if isinstance(doc, Document):
            meta = doc.metadata
            doc_id = meta.get("id", f"DOC-{idx}")
            machine = meta.get("machine", "General")
            doc_type = meta.get("doc_type", "Reference")
            hazard = meta.get("hazard_level", "Standard")
            error_code = meta.get("error_code", "")
            
            header = f"[Source {idx}: {doc_id} | Machine: {machine} | Type: {doc_type}"
            if error_code:
                header += f" | Code: {error_code}"
            header += f" | Hazard: {hazard}]"
            
            sops_formatted.append(f"{header}\n{doc.page_content.strip()}")
        elif isinstance(doc, dict):
            sops_formatted.append(f"[Source {idx}: {doc.get('id', 'Ref')}]\n{doc.get('content', str(doc))}")
        else:
            sops_formatted.append(f"[Source {idx}]\n{str(doc).strip()}")

    grounding_corpus = "\n\n".join(sops_formatted) if sops_formatted else "Standard factory operating manuals apply."

    # 6. Format Operator Context
    op_info = ""
    if operator_context:
        op_name = operator_context.get("name", "Operator")
        op_tier = operator_context.get("derived_tier") or operator_context.get("tier", "Novice")
        machine_name = operator_context.get("machine_id", "Shopfloor Equipment")
        active_alarm = operator_context.get("active_alarm", "None")
        autonomy = operator_context.get("autonomy_score", 40.0)

        op_info = f"""### CURRENT OPERATOR & MACHINE CONTEXT (DECOUPLED COGNITIVE STATE)
- Operator: {op_name}
- Target Machine: {machine_name}
- Machine-Specific Autonomy Score: {autonomy:.1f}/100 (Learned Derived Tier: **{op_tier}**)
- Active SCADA Alarm: {active_alarm}
"""

    # Check for Emergency Severity-1 SOS Mode
    is_severity_1 = operator_context.get("is_severity_1", False) if operator_context else False
    sos_header = ""
    if is_severity_1 or "SOS_SHUTDOWN" in bandit_format_instruction:
        sos_header = """🚨 **CRITICAL EMERGENCY OVERRIDE: SOS SHUTDOWN PROTOCOL ACTIVE**
- SEVERITY-1 CRITICAL ALARM / E-STOP EVENT DETECTED.
- Standard troubleshooting is SUSPENDED.
- Provide ONLY deterministic emergency halt and isolation directives (E-Stop, LOTO, Level 2 Maintenance Emergency Dispatch).
"""

    # 7. Assemble Master Prompt (Strict Hierarchy: Safety -> Bandit -> RAG/Procedural)
    prompt = f"""You are the **Factory Operator Intelligent Assistant**, an expert shopfloor AI copilot supporting manufacturing operators in diagnosing, troubleshooting, and repairing CNC milling machines and Injection Molding equipment.

{sos_header}
{op_info}
### MANDATORY SAFETY PROTOCOLS & HAZARD WARNINGS (PRIORITY 1: SAFETY METADATA)
{safety_text}

{ecm_section}
{escalation_section}

### REQUIRED OUTPUT FORMATTING DIRECTIVE (PRIORITY 2: BANDIT STRATEGY)
{bandit_format_instruction}

{procedural_section}
### FACTORY REFERENCE MANUALS & AUTHORITATIVE GROUNDING (PRIORITY 3: RAG CORPUS)
{grounding_corpus}

### OPERATIONAL CONSTRAINTS & GROUNDING RULES:
1. **Dynamic Procedural Ranking**: Prioritize the highest-ranked Primary Fix first based on historical Bayesian success probability while presenting backup paths.
2. **Anti-Pattern Avoidance**: Strictly warn the operator against executing any documented Anti-Patterns (What Not To Do).
3. **Strict Truthfulness**: Base your troubleshooting guidance solely on the retrieved procedural fault trees and manuals above. Do NOT hallucinate unverified procedures.
4. **Safety First**: Highlight critical hazard cautions before recommending physical or electrical steps.
5. **Format Adherence**: Adhere strictly to the active formatting directive.
6. **Supervisor Offline Protocol**: If the supervisor is offline above, do NOT suggest escalating; guide operator through safe independent triage or safe shutdown.

---
### OPERATOR INQUIRY:
"{user_query}"

### ASSISTANT RESPONSE:
"""
    return prompt.strip()
