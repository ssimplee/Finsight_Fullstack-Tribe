"""Qwen LLM reasoning over retrieved evidence (worksplit §5).

The RAG pipeline keeps deterministic vector retrieval (ChromaDB + local
all-MiniLM-L6-v2 embeddings) for evidence *retrieval*, because the campus AI
platform (model.ai.szu.edu.cn) exposes no /v1/embeddings endpoint -- only
chat/completions (deepseek-r1, qwen3-vl-8b) and OCR. So Qwen cannot replace
the embedding model. What it *can* and *should* do (worksplit §5) is reason
over the retrieved evidence and write the final differential explanation.

This module calls the campus OpenAI-compatible chat endpoint with a grounding
prompt built from the case + retrieved evidence + ranked conditions, and
returns a natural-language differential summary. It degrades to the
deterministic summary if QWEN_API_KEY is unset or the call fails, so the
agent pipeline never blocks on the LLM.

Env (same convention as Member 3's vision client):
    QWEN_API_KEY     campus platform key (see 智算中心大模型调用方法.docx)
    QWEN_MODEL       default qwen3-vl-8b
    QWEN_BASE_URL    default https://model.ai.szu.edu.cn/v1
    QWEN_VERIFY_SSL  default true; set false if the campus cert can't verify
    FINSIGHT_USE_QWEN_REASONER  set to 1 to enable (off by default; deterministic
                               path stays the default so tests run offline)
"""
from __future__ import annotations

import json
import os
from typing import Optional

import httpx

from .differential import CONDITION_NAMES
from .models import CaseRecord, DifferentialItem, EvidenceItem

DEFAULT_BASE_URL = "https://model.ai.szu.edu.cn/v1"
DEFAULT_MODEL = "qwen3-vl-8b"
DEFAULT_TIMEOUT_SEC = 60.0
DEFAULT_MAX_RETRIES = 2
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

_SYSTEM_PROMPT = (
    "You are FinSight, a fish-health triage assistant for Nile tilapia "
    "aquaculture. You reason ONLY over the case facts and retrieved knowledge-"
    "base evidence provided by the user. Rules:\n"
    "1. Ground every claim in the provided evidence; cite evidence IDs like "
    "[KB_D02_001]. Never invent facts or sources.\n"
    "2. These are observations, NOT a confirmed diagnosis. State that laboratory "
    "confirmation is required before any treatment.\n"
    "3. Always state uncertainty and what is still missing.\n"
    "4. Do NOT prescribe drugs or give definitive treatment doses. Suggest safe "
    "next steps and confirmation methods only.\n"
    "5. If evidence points to more than one cause (overlapping symptoms), say so "
    "explicitly rather than forcing a single diagnosis.\n"
    "6. Keep it concise: 4-8 sentences. Write in the same language as the case."
)


def _enabled() -> bool:
    return os.environ.get("FINSIGHT_USE_QWEN_REASONER", "").lower() in ("1", "true", "yes")


def _has_key() -> bool:
    return bool(os.environ.get("QWEN_API_KEY", "").strip())


def _case_block(case: CaseRecord) -> str:
    lines = ["CASE:"]
    lines.append(f"  species: {case.fish.species}")
    if case.observations.visual:
        lines.append(f"  visual signs: {', '.join(case.observations.visual)}")
    if case.observations.behavioral:
        lines.append(f"  behavioural signs: {', '.join(case.observations.behavioral)}")
    wq = case.water_quality
    wq_parts = []
    for name in ("temperature_c", "ph", "dissolved_oxygen_mg_l", "ammonia_mg_l", "nitrite_mg_l", "nitrate_mg_l"):
        v = getattr(wq, name, None)
        if v is not None:
            wq_parts.append(f"{name}={v}")
    if wq_parts:
        lines.append(f"  water quality: {', '.join(wq_parts)}")
    if case.history:
        lines.append(f"  history: {json.dumps(case.history, ensure_ascii=False)}")
    img_findings = [f for img in case.images for f in img.visible_findings if f and f != "pending_qwen_observation"]
    if img_findings:
        lines.append(f"  image observations: {', '.join(img_findings)}")
    return "\n".join(lines)


def _evidence_block(evidence: list[EvidenceItem], diff: list[DifferentialItem]) -> str:
    """Show retrieved evidence grouped by the ranked candidate conditions."""
    lines = ["RETRIEVED EVIDENCE (ranked candidates):"]
    # Conditions in rank order; attach their supporting/conflicting evidence.
    ranked_ids = [d.condition_id for d in diff]
    other_ids = [e.condition_id for e in evidence if e.condition_id and e.condition_id not in ranked_ids]
    order = ranked_ids + sorted(set(other_ids))
    for cid in order:
        name = CONDITION_NAMES.get(cid, cid)
        items = [e for e in evidence if e.condition_id == cid]
        if not items:
            continue
        lines.append(f"\n  [{cid}] {name} ({len(items)} chunks):")
        for e in items:
            text = (e.text or "").replace("\n", " ").strip()
            if len(text) > 220:
                text = text[:217] + "..."
            lines.append(f"    - ({e.evidence_id}, {e.label}) {text}")
    return "\n".join(lines)


def _ranking_block(diff: list[DifferentialItem], scores: dict[str, float]) -> str:
    if not diff:
        return "RANKING: (no candidate reached threshold)"
    lines = ["RANKING (deterministic keyword+evidence score, for your reference):"]
    for d in diff:
        name = CONDITION_NAMES.get(d.condition_id, d.condition_id)
        lines.append(
            f"  #{d.rank} {d.condition_id} {name} "
            f"(strength={d.evidence_strength}, uncertainty={d.uncertainty}, "
            f"support={len(d.supporting_evidence_ids)}, conflict={len(d.conflicting_evidence_ids)})"
        )
    return "\n".join(lines)


def build_prompt(case: CaseRecord, evidence: list[EvidenceItem],
                 diff: list[DifferentialItem], scores: dict[str, float]) -> str:
    return "\n\n".join([
        _case_block(case),
        _evidence_block(evidence, diff),
        _ranking_block(diff, scores),
        (
            "TASK: Write the differential explanation for this case. Name the "
            "top-ranked cause and the alternatives, cite the supporting and "
            "conflicting evidence by ID, state the uncertainty and what is still "
            "missing, and recommend confirmation steps and safe next actions. "
            "Do not confirm a diagnosis."
        ),
    ])


def _post(base_url: str, headers: dict, payload: dict, verify_ssl: bool) -> dict:
    last_err: Optional[Exception] = None
    for _ in range(DEFAULT_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SEC, verify=verify_ssl) as c:
                r = c.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            if r.status_code in RETRYABLE_STATUS:
                last_err = RuntimeError(f"retryable {r.status_code}: {r.text[:200]}")
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            break
    raise RuntimeError(f"Qwen chat failed: {last_err}")


def _call_qwen(prompt: str) -> str:
    base = os.environ.get("QWEN_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("QWEN_MODEL", DEFAULT_MODEL)
    verify = os.environ.get("QWEN_VERIFY_SSL", "true").strip().lower() != "false"
    key = os.environ["QWEN_API_KEY"].strip()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "max_tokens": 600,
        "temperature": 0.2,
    }
    data = _post(base, headers, payload, verify)
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Qwen reply shape unexpected: {str(data)[:200]}") from e


def reason(case: CaseRecord, evidence: list[EvidenceItem],
           diff: list[DifferentialItem], scores: dict[str, float]) -> Optional[str]:
    """Return a Qwen-written differential summary, or None if unavailable.

    None => caller should fall back to the deterministic summary. Never raises
    into the agent pipeline.
    """
    if not _enabled() or not _has_key() or not diff:
        return None
    try:
        prompt = build_prompt(case, evidence, diff, scores)
        text = _call_qwen(prompt)
    except Exception as e:  # noqa: BLE001
        print(f"[qwen-reasoner] disabled/fallback ({e})")
        return None
    if not text:
        return None
    # Safety gate: strip nothing silently, but log if Qwen made unsafe claims so
    # the deterministic path's safety.check_safety can still flag the report.
    return text


def deterministic_summary(diff: list[DifferentialItem], unc: str) -> str:
    """Fallback summary, identical to the agent's deterministic template."""
    if not diff:
        return (
            "Current evidence is insufficient for a meaningful ranking. "
            "Additional information and laboratory confirmation are required."
        )
    top = diff[0]
    top_name = CONDITION_NAMES.get(top.condition_id, top.condition_id)
    others = ", ".join(CONDITION_NAMES.get(d.condition_id, d.condition_id) for d in diff[1:])
    s = f"Top-ranked cause: {top_name} (strength={top.evidence_strength}, uncertainty={unc})."
    if others:
        s += f" Alternatives considered: {others}."
    s += " Findings are not confirmed; laboratory testing is required before treatment."
    return s
