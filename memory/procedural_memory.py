"""
Procedural Memory & Dynamic Probabilistic Fault Trees Module.
Manages:
1. Active Dynamic Skill Library (data/procedural_fault_trees.json).
2. Quarantined Candidate Shortcuts (data/quarantine_sops.json) with Consensus Validation.
Enforces safety guardrails: Quarantined procedures are strictly excluded from RAG retrieval,
and promoted expert shortcuts are restricted by clearance level (min_tier_required: 'Expert').
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def calculate_branch_probability(
    successes: int,
    failures: int,
    alpha: float = 1.0,
    beta: float = 1.0,
) -> float:
    """
    Computes dynamic probability score using Bayesian Beta-Binomial updating (Laplace smoothing).
    Formula: P(Success) = (successes + alpha) / (successes + failures + alpha + beta)
    """
    total = successes + failures + alpha + beta
    if total <= 0:
        return 0.5
    prob = (successes + alpha) / total
    return round(float(prob), 4)


class ProceduralMemory:
    """
    Dynamic Procedural Memory with dual storage (Active & Quarantine) and Consensus Validation.
    """

    def __init__(
        self,
        data_file: Optional[str] = None,
        quarantine_file: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.data_file = Path(data_file) if data_file else base_dir / "data" / "procedural_fault_trees.json"
        self.quarantine_file = Path(quarantine_file) if quarantine_file else base_dir / "data" / "quarantine_sops.json"

        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.quarantine_file.parent.mkdir(parents=True, exist_ok=True)

        self.fault_trees: List[Dict[str, Any]] = []
        self.quarantine_trees: List[Dict[str, Any]] = []

        self.load_from_file()

    def load_from_file(self) -> None:
        """Loads both active fault trees and quarantined SOPs from disk."""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.fault_trees = json.load(f)
            except Exception as e:
                print(f"[ProceduralMemory] Error loading active fault trees: {e}")
                self.fault_trees = []

        if self.quarantine_file.exists():
            try:
                with open(self.quarantine_file, "r", encoding="utf-8") as f:
                    self.quarantine_trees = json.load(f)
            except Exception as e:
                print(f"[ProceduralMemory] Error loading quarantine trees: {e}")
                self.quarantine_trees = []

    def save_to_file(self) -> None:
        """Serializes both active and quarantined fault trees to disk."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.fault_trees, f, indent=2)

        with open(self.quarantine_file, "w", encoding="utf-8") as f:
            json.dump(self.quarantine_trees, f, indent=2)

    # --- 1. ACTIVE PROCEDURAL STORE METHODS ---
    def get_all_trees(self, operator_tier: str = "Expert") -> List[Dict[str, Any]]:
        """Returns all active fault trees with dynamically computed probabilities, filtered by operator tier."""
        enriched = []
        for tree in self.fault_trees:
            enriched.append(self._enrich_and_sort_tree(tree, operator_tier=operator_tier))
        return enriched

    def get_fault_tree(
        self,
        error_code: str,
        machine: Optional[str] = None,
        operator_tier: str = "Expert",
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves an active fault tree by error code, calculates dynamic Bayesian probabilities,
        sorts diagnostic paths descending by probability score, and filters out paths exceeding operator_tier.
        """
        error_clean = error_code.strip().lower()
        for tree in self.fault_trees:
            tree_code = tree.get("error_code", "").strip().lower()
            if tree_code == error_clean or error_clean in tree_code or tree_code in error_clean:
                if machine and tree.get("machine") and machine.lower() not in tree.get("machine", "").lower():
                    continue
                return self._enrich_and_sort_tree(tree, operator_tier=operator_tier)
        return None

    def search(
        self,
        query: str,
        machine: Optional[str] = None,
        operator_tier: str = "Novice",
    ) -> List[Dict[str, Any]]:
        """
        Searches active procedural fault trees.
        SAFETY RULE: Strictly excludes quarantined SOPs and filters out Expert-only shortcuts for Novice/Intermediate users.
        """
        q_lower = query.lower()
        matches = []
        for tree in self.fault_trees:
            tree_str = f"{tree.get('error_code', '')} {tree.get('title', '')} {tree.get('machine', '')}".lower()
            if any(term in tree_str for term in q_lower.split()) or any(term in q_lower for term in tree.get('error_code', '').lower().split()):
                if machine and tree.get("machine") and machine.lower() not in tree.get("machine", "").lower():
                    continue
                enriched = self._enrich_and_sort_tree(tree, operator_tier=operator_tier)
                if enriched.get("diagnostic_paths"):
                    matches.append(enriched)
        return matches

    def _enrich_and_sort_tree(
        self,
        tree: Dict[str, Any],
        operator_tier: str = "Expert",
    ) -> Dict[str, Any]:
        """
        Enriches diagnostic paths with Bayesian probability scores, filters out paths requiring
        higher clearance than operator_tier, and sorts descending.
        """
        tree_copy = dict(tree)
        paths = []
        for path in tree.get("diagnostic_paths", []):
            # Clearance check: if path requires Expert and operator is not Expert, omit it for safety
            min_tier = path.get("min_tier_required")
            if min_tier == "Expert" and operator_tier != "Expert":
                continue

            p_copy = dict(path)
            s_count = int(p_copy.get("success_count", 0))
            f_count = int(p_copy.get("failure_count", 0))
            p_score = calculate_branch_probability(s_count, f_count)
            p_copy["probability_score"] = p_score
            paths.append(p_copy)

        paths.sort(key=lambda p: p["probability_score"], reverse=True)
        tree_copy["diagnostic_paths"] = paths
        return tree_copy

    def update_path_telemetry(
        self,
        error_code: str,
        path_id: str,
        success: bool,
    ) -> Optional[Dict[str, Any]]:
        """Increments success/failure counts on active fault tree paths and recalculates probability."""
        error_clean = error_code.strip().lower()
        for tree in self.fault_trees:
            tree_code = tree.get("error_code", "").strip().lower()
            if tree_code == error_clean or error_clean in tree_code or tree_code in error_clean:
                for path in tree.get("diagnostic_paths", []):
                    if path.get("path_id") == path_id:
                        if success:
                            path["success_count"] = path.get("success_count", 0) + 1
                        else:
                            path["failure_count"] = path.get("failure_count", 0) + 1

                        path["probability_score"] = calculate_branch_probability(
                            path["success_count"], path["failure_count"]
                        )
                        self.save_to_file()
                        return path
        return None

    # --- 2. QUARANTINE DATABASE & CONSENSUS PROMOTION METHODS ---
    def get_quarantined_trees(self) -> List[Dict[str, Any]]:
        """Returns all quarantined fault trees pending senior operator consensus validation."""
        return list(self.quarantine_trees)

    def add_to_quarantine(
        self,
        error_code: str,
        machine: str,
        title: str,
        path_payload: Dict[str, Any],
        operator_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saves an unverified shortcut or shopfloor procedure exclusively to the quarantine database.
        """
        # Ensure validation tracking array exists
        path_copy = dict(path_payload)
        validators = path_copy.get("validated_by_senior_operators", [])
        if operator_id and operator_id not in validators:
            validators.append(operator_id)
        path_copy["validated_by_senior_operators"] = validators

        # Find or create quarantine fault tree
        found_tree = None
        for tree in self.quarantine_trees:
            if tree.get("error_code", "").lower() == error_code.lower() and tree.get("machine", "").lower() == machine.lower():
                found_tree = tree
                break

        if not found_tree:
            found_tree = {
                "error_code": error_code,
                "machine": machine,
                "title": title,
                "hazard_level": "WARNING",
                "required_role": "Expert",
                "diagnostic_paths": [path_copy],
            }
            self.quarantine_trees.append(found_tree)
        else:
            found_tree["diagnostic_paths"].append(path_copy)

        self.save_to_file()
        return path_copy

    def validate_quarantine_sop(
        self,
        error_code: str,
        path_id: str,
        operator_id: str,
        operator_tier: str,
    ) -> Dict[str, Any]:
        """
        Records a validation signature by a Senior/Expert operator on a quarantined shortcut.
        If >= 3 unique Expert operators have validated the shortcut, it is automatically promoted
        to the active procedural store with min_tier_required: 'Expert'.
        
        Returns:
            Dict containing validation status, current validator list, and promotion flag.
        """
        if operator_tier != "Expert":
            return {
                "status": "REJECTED_NON_EXPERT",
                "message": "Only Senior/Expert operators can sign off on quarantined shortcut procedures.",
                "promoted": False,
            }

        target_tree = None
        target_path = None
        for tree in self.quarantine_trees:
            if error_code.lower() in tree.get("error_code", "").lower() or tree.get("error_code", "").lower() in error_code.lower():
                for path in tree.get("diagnostic_paths", []):
                    if path.get("path_id") == path_id:
                        target_tree = tree
                        target_path = path
                        break

        if not target_path:
            return {
                "status": "NOT_FOUND",
                "message": f"Quarantined SOP path {path_id} not found.",
                "promoted": False,
            }

        # Add validator ID if not already present
        validators = target_path.get("validated_by_senior_operators", [])
        if operator_id not in validators:
            validators.append(operator_id)
            target_path["validated_by_senior_operators"] = validators

        unique_validators = list(set(validators))
        promoted = False

        # Consensus Threshold Check (>= 3 unique Senior/Expert operators)
        if len(unique_validators) >= 3:
            promoted = True
            # Tag with clearance requirement
            target_path["min_tier_required"] = "Expert"
            target_path["promoted_date"] = "2026-08-20"

            # 1. Add to Active Procedural Store
            active_matched_tree = None
            for tree in self.fault_trees:
                if tree.get("error_code", "").lower() == target_tree.get("error_code", "").lower() and tree.get("machine", "").lower() == target_tree.get("machine", "").lower():
                    active_matched_tree = tree
                    break

            if active_matched_tree:
                # Add branch if not already present
                if not any(p.get("path_id") == target_path.get("path_id") for p in active_matched_tree.get("diagnostic_paths", [])):
                    active_matched_tree["diagnostic_paths"].append(target_path)
            else:
                new_active_tree = dict(target_tree)
                new_active_tree["diagnostic_paths"] = [target_path]
                self.fault_trees.append(new_active_tree)

            # 2. Remove from Quarantine Tree
            target_tree["diagnostic_paths"] = [
                p for p in target_tree.get("diagnostic_paths", []) if p.get("path_id") != path_id
            ]
            if not target_tree["diagnostic_paths"]:
                self.quarantine_trees = [t for t in self.quarantine_trees if t != target_tree]

        self.save_to_file()

        return {
            "status": "VALIDATED",
            "path_id": path_id,
            "validated_by": unique_validators,
            "count": len(unique_validators),
            "promoted": promoted,
            "message": (
                f"Consensus threshold reached (3 unique experts: {unique_validators})! SOP promoted to Active Library with min_tier_required: 'Expert'."
                if promoted
                else f"Validated by {operator_id} ({len(unique_validators)}/3 Expert signatures collected)."
            ),
        }

    def format_procedural_context(self, fault_trees: List[Dict[str, Any]]) -> str:
        """Formats active procedural fault trees into structured grounding text for LLM prompts."""
        if not fault_trees:
            return ""

        sections = []
        for tree in fault_trees:
            tree_header = (
                f"### DYNAMIC FAULT TREE: {tree.get('error_code')} - {tree.get('title')} "
                f"({tree.get('machine', 'General')}) [Hazard: {tree.get('hazard_level', 'NOTE')}]"
            )
            paths_text = []
            for rank, path in enumerate(tree.get("diagnostic_paths", []), 1):
                prob_pct = path.get("probability_score", 0.5) * 100
                time_mins = path.get("avg_execution_time_mins", 10)
                rank_label = f"RECOMMENDED PRIMARY FIX (Rank {rank})" if rank == 1 else f"SECONDARY / BACKUP FIX (Rank {rank})"
                
                req_tag = f" [Clearance Required: {path.get('min_tier_required')}]" if path.get("min_tier_required") else ""
                path_block = (
                    f"#### [{rank_label}]{req_tag} {path.get('title')} ({path.get('path_id')})\n"
                    f"- **Historical Success Probability**: {prob_pct:.1f}% "
                    f"({path.get('success_count', 0)} Solves / {path.get('failure_count', 0)} Failures)\n"
                    f"- **Estimated Triage Time**: ~{time_mins} minutes\n"
                    f"- **Description**: {path.get('description')}\n"
                    f"- **Action Steps**:\n{path.get('resolution_steps')}\n"
                    f"- **Prohibited Actions**: {path.get('prohibited_actions', 'None')}"
                )
                paths_text.append(path_block)

            if paths_text:
                sections.append(f"{tree_header}\n\n" + "\n\n".join(paths_text))

        return "\n\n".join(sections)
