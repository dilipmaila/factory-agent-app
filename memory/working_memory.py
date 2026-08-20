"""
Working Memory Module.
Constructs structured, dynamically formatted system prompts combining real-time SCADA telemetry,
retrieved SOP / manual excerpts, safety hazard directives, and Contextual Bandit formatting constraints.
"""

from typing import List, Union, Optional, Dict, Any
from langchain_core.documents import Document


def build_prompt(
    safety_warnings: Union[List[str], str],
    bandit_format_instruction: str,
    retrieved_sops: List[Union[Document, Dict[str, Any], str]],
    user_query: str,
    operator_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Assembles the complete working memory prompt for the LLM.
    
    Args:
        safety_warnings: Critical shopfloor hazards, PPE requirements, or lock-out/tag-out rules.
        bandit_format_instruction: Strict formatting guidelines dictated by the Contextual Bandit router.
        retrieved_sops: List of LangChain Document objects or strings retrieved via Hybrid Search.
        user_query: The immediate question, error description, or alarm query from the operator.
        operator_context: Optional metadata containing operator name, tier, and machine state.
        
    Returns:
        Structured system + user prompt string ready for LLM generation.
    """
    # 1. Format Safety Warnings
    if isinstance(safety_warnings, list):
        safety_text = "\n".join(f"- ⚠️ {w}" for w in safety_warnings) if safety_warnings else "- Standard OSHA & Shopfloor Safety protocols apply."
    else:
        safety_text = f"- ⚠️ {safety_warnings}" if safety_warnings else "- Standard OSHA & Shopfloor Safety protocols apply."

    # 2. Format Retrieved Grounding SOPs & Manual Documents
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

    grounding_corpus = "\n\n".join(sops_formatted) if sops_formatted else "No specific SOP found. Rely on factory general safety best practices."

    # 3. Format Operator Context
    op_info = ""
    if operator_context:
        op_name = operator_context.get("name", "Operator")
        op_tier = operator_context.get("tier", "Novice")
        machine_name = operator_context.get("machine_id", "Shopfloor Equipment")
        active_alarm = operator_context.get("active_alarm", "None")
        autonomy = operator_context.get("autonomy_score", 40.0)

        op_info = f"""
### CURRENT OPERATOR & MACHINE CONTEXT
- Operator: {op_name} (Skill Tier: {op_tier} | Autonomy Score: {autonomy:.1f}/100)
- Target Machine: {machine_name}
- Active SCADA Alarm: {active_alarm}
"""

    # 4. Assemble Master Prompt with Strict Cognitive Instructions
    prompt = f"""You are the **Factory Operator Intelligent Assistant**, an expert shopfloor AI copilot supporting manufacturing operators in diagnosing, troubleshooting, and repairing CNC milling machines and Injection Molding equipment.

{op_info}
### MANDATORY SAFETY PROTOCOLS & HAZARD WARNINGS
{safety_text}

### AUTHORITATIVE SHOPFLOOR KNOWLEDGE BASE (GROUNDING SOURCES)
{grounding_corpus}

### REQUIRED OUTPUT FORMATTING DIRECTIVE (CONTEXTUAL BANDIT POLICY)
{bandit_format_instruction}

### OPERATIONAL CONSTRAINTS & GROUNDING RULES:
1. **Strict Truthfulness**: Base your troubleshooting guidance solely on the retrieved SOPs and manuals above. Do NOT hallucinate unverified electrical or mechanical procedures.
2. **Safety First**: If a step carries high hazard (e.g. 120VAC, hydraulic high pressure, pinch point), explicitly highlight caution before the action step.
3. **Format Adherence**: You MUST strictly adhere to the formatting directive specified above.
4. **Actionable Resolution**: Provide clear diagnostic checks to help the operator verify the issue or perform the correct reset sequence.

---
### OPERATOR INQUIRY:
"{user_query}"

### ASSISTANT RESPONSE:
"""
    return prompt.strip()
