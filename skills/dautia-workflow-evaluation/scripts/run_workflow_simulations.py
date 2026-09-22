#!/usr/bin/env python3
"""Run isolated Codex CLI role-resolution simulations and grade real artifacts."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "references/workflow-simulation-cases.json"
V12_CASES_PATH = ROOT / "references/workflow-v12-cases.json"
EXPECTED_ROOT = ("gpt-5.6-sol", "high")
V12_RUBRIC_VERSION = "12.2-fixture-cwd"
OPERATION_EXECUTABLES = {"xcodebuild","xcrun","simctl","wsl","wsl.exe","adb","gradle","gradlew","ssh","colima","psql","supabase","curl","gh","vercel","doctl"}

RECEIPT_TOKENS = {
    "templorojo-filters": [
        r"CONTRACT_RECEIPT",
        r"TR-FACETS-V1",
        r"same-variant-stock-positive",
        r"url-roundtrip",
        r"removable-stale",
        r"no-modal",
    ],
    "ryven-regressions": [
        r"CONTRACT_RECEIPT",
        r"RYVEN-REGRESSIONS-V1",
        r"canonical-ticket-radio",
        r"threshold-30",
        r"guidance-suppresses",
        r"failed-cancel-active",
    ],
}

FIXTURES = {
    "templorojo-filters": {
        "catalog_filters.py": '''"""Sanitized catalog facet helpers."""\n\n\ndef filter_products(products, colors=(), sizes=()):\n    raise NotImplementedError\n\n\ndef encode_filters(colors=(), sizes=()):\n    raise NotImplementedError\n\n\ndef decode_filters(query):\n    raise NotImplementedError\n''',
        "public_tests.py": '''import unittest\nfrom catalog_filters import filter_products, encode_filters, decode_filters\n\nPRODUCTS = [\n {"id":"mixed","variants":[{"color":"black","size":"M","stock":1},{"color":"blue","size":"S","stock":1}]},\n {"id":"blue-m","variants":[{"color":"blue","size":"M","stock":2}]},\n]\nclass Tests(unittest.TestCase):\n def test_same_variant(self):\n  self.assertEqual([p["id"] for p in filter_products(PRODUCTS,["black"],["S"])],[])\n def test_or_and(self):\n  self.assertEqual([p["id"] for p in filter_products(PRODUCTS,["black","blue"],["M"])],["mixed","blue-m"])\n def test_url(self):\n  q=encode_filters(["blue","black"],["M"]); self.assertEqual(decode_filters(q),{"colors":["black","blue"],"sizes":["M"]})\nif __name__=="__main__": unittest.main()\n''',
        "ACCEPTANCE.md": "Products stay visible; no modal. OR within color/size, AND across facets, same in-stock variant. URL round-trip and removable stale zero-result selections. Keyboard labels remain explicit.\n",
    },
    "image-batch": {
        "inventory.json": json.dumps({"required_slots": [
            {"id":"hoodie-black-front","product":"hoodie","color":"black","view":"front","source":"original/hoodie-black-front.png","white_background":True},
            {"id":"hoodie-black-back","product":"hoodie","color":"black","view":"back","source":"original/hoodie-black-back.png","white_background":False},
            {"id":"hoodie-red-front","product":"hoodie","color":"red","view":"front","source":"original/hoodie-red-front.png","white_background":True},
            {"id":"hoodie-red-back","product":"hoodie","color":"red","view":"back","source":"original/hoodie-red-back.png","white_background":False},
            {"id":"tee-black-front","product":"tee","color":"black","view":"front","source":"original/tee-black-front.png","white_background":True},
            {"id":"tee-black-back","product":"tee","color":"black","view":"back","source":"original/tee-black-back.png","white_background":False}
        ]}, indent=2) + "\n",
        "media_batch.py": '''"""Build a deterministic manifest without touching images or providers."""\n\n\ndef build_manifest(inventory):\n    raise NotImplementedError\n''',
        "manifest.json": "[]\n",
        "public_tests.py": '''import json,unittest\nfrom media_batch import build_manifest\n+class Tests(unittest.TestCase):\n def test_complete(self):\n  inv=json.load(open("inventory.json")); rows=build_manifest(inv)\n  self.assertEqual(len(rows),len(inv["required_slots"])); self.assertEqual(len({r["id"] for r in rows}),len(rows))\n def test_manifest_matches(self):\n  inv=json.load(open("inventory.json")); self.assertEqual(json.load(open("manifest.json")),build_manifest(inv))\nif __name__=="__main__": unittest.main()\n'''.replace("\n+", "\n"),
    },
    "ryven-regressions": {
        "admin_form.html": '<fieldset><legend>Icon</legend><label><input type="radio" name="iconLabel" value="ticket">Ticket</label><label><input type="radio" name="iconLabel" value="music">Music</label></fieldset>\n',
        "admin_flow.py": '''def choose_ticket_icon(page):\n    return page.select_option("select[name=iconLabel]", "tag")\n''',
        "journey_state.py": '''def journey_transition(state, event, elapsed_minutes=0, guidance_active=False, cancel_succeeded=True):\n    return state\n''',
        "public_tests.py": '''import unittest\nfrom admin_flow import choose_ticket_icon\nfrom journey_state import journey_transition\n+class Page:\n def __init__(self): self.selector=None\n def check(self,selector): self.selector=selector\nclass Tests(unittest.TestCase):\n def test_radio(self):\n  p=Page(); choose_ticket_icon(p); self.assertEqual(p.selector,'input[type="radio"][name="iconLabel"][value="ticket"]')\n def test_threshold(self):\n  self.assertEqual(journey_transition("active","tick",29),"active")\n  self.assertEqual(journey_transition("active","tick",30),"intent_required")\n def test_recovery(self):\n  self.assertEqual(journey_transition("intent_required","continue"),"active")\n  self.assertEqual(journey_transition("intent_required","cancel",cancel_succeeded=False),"active")\n def test_guidance(self):\n  self.assertEqual(journey_transition("active","tick",45,guidance_active=True),"active")\nif __name__=="__main__": unittest.main()\n'''.replace("\n+", "\n"),
    },
    "copy-no-delegation": {
        "button.html": '<button class="save" aria-label="Guardar"><span>Guardar</span></button>\n<script>window.formMode="safe";</script>\n',
        "public_tests.py": '''import unittest\nclass Tests(unittest.TestCase):\n def test_exact(self):\n  self.assertEqual(open("button.html").read(),'<button class="save" aria-label="Guardar"><span>Guardar cambios</span></button>\\n<script>window.formMode="safe";</script>\\n')\nif __name__=="__main__": unittest.main()\n''',
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def grade_artifacts(case_id: str, case_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        if case_id == "templorojo-filters":
            m = load_module(case_dir / "catalog_filters.py", "sim_catalog")
            products = [
                {"id":"mixed","variants":[{"color":"black","size":"M","stock":1},{"color":"blue","size":"S","stock":1}]},
                {"id":"sold","variants":[{"color":"blue","size":"M","stock":0}]},
                {"id":"blue-m","variants":[{"color":"blue","size":"M","stock":1}]},
            ]
            if [p["id"] for p in m.filter_products(products,["black"],["S"])]: errors.append("same_variant")
            if [p["id"] for p in m.filter_products(products,["black","blue"],["M"])] != ["mixed","blue-m"]: errors.append("facet_logic")
            decoded = m.decode_filters(m.encode_filters(["blue","black"],["L","M"]))
            if decoded != {"colors":["black","blue"],"sizes":["L","M"]}: errors.append("url_roundtrip")
        elif case_id == "image-batch":
            inv = json.loads((case_dir / "inventory.json").read_text())
            m = load_module(case_dir / "media_batch.py", "sim_media")
            rows = m.build_manifest(inv); saved = json.loads((case_dir / "manifest.json").read_text())
            expected = {x["id"]: x for x in inv["required_slots"]}; got = {x.get("id"): x for x in rows}
            if len(rows) != len(expected) or set(got) != set(expected): errors.append("complete_universe")
            if rows != saved: errors.append("saved_manifest")
            for key, src in expected.items():
                row = got.get(key, {})
                if row.get("source") != src["source"]: errors.append("original_source_preservation"); break
                action = "correct-background" if src["white_background"] else "keep"
                if row.get("action") != action: errors.append("action_mapping"); break
                if action == "correct-background" and row.get("output") != f"corrected/{key}.png": errors.append("deterministic_output"); break
                if action == "keep" and row.get("output") not in (None, src["source"]): errors.append("keep_output"); break
        elif case_id == "ryven-regressions":
            a = load_module(case_dir / "admin_flow.py", "sim_admin")
            j = load_module(case_dir / "journey_state.py", "sim_journey")
            class Page:
                def __init__(self): self.selector = None
                def check(self, selector): self.selector = selector
            page = Page(); a.choose_ticket_icon(page)
            if page.selector != 'input[type="radio"][name="iconLabel"][value="ticket"]': errors.append("canonical_radio")
            checks = [
                (j.journey_transition("active","tick",29),"active","threshold_29"),
                (j.journey_transition("active","tick",30),"intent_required","threshold_30"),
                (j.journey_transition("active","tick",45,True),"active","guidance_exclusion"),
                (j.journey_transition("intent_required","continue"),"active","continue"),
                (j.journey_transition("intent_required","cancel",cancel_succeeded=False),"active","cancel_failure_recovery"),
            ]
            errors.extend(label for actual, expected, label in checks if actual != expected)
        elif case_id == "copy-no-delegation":
            exact = '<button class="save" aria-label="Guardar"><span>Guardar cambios</span></button>\n<script>window.formMode="safe";</script>\n'
            if (case_dir / "button.html").read_text() != exact: errors.append("exact_copy_only")
    except Exception as exc:
        errors.append(f"artifact_exception:{type(exc).__name__}:{exc}")
    return errors


def parse_rollout(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(errors="replace").splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: continue
    return events


def _output_text(payload: dict) -> str:
    value = payload.get("output", "")
    if isinstance(value, list):
        return "\n".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in value)
    return str(value)


def _patch_paths(value: str, cwd: Path) -> list[str]:
    # JS tool input contains either literal newlines or escaped \n inside a string.
    normalized = value.replace("\\n", "\n")
    paths = []
    for raw in re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", normalized, re.M):
        path = Path(raw.strip())
        if not path.is_absolute(): path = cwd / path
        paths.append(str(path.resolve()))
    return paths


def _successful_mutations(events: list[dict], cwd: Path, session_id: str, role: str | None) -> list[dict]:
    outputs = {e.get("payload",{}).get("call_id"): e.get("payload",{}) for e in events if e.get("type") == "response_item" and e.get("payload",{}).get("type") == "custom_tool_call_output"}
    mutations = []
    for e in events:
        payload = e.get("payload",{})
        if e.get("type") != "response_item" or payload.get("type") != "custom_tool_call": continue
        value = str(payload.get("input", "")); paths = _patch_paths(value, cwd)
        if "apply_patch" not in value or not paths: continue
        paired = outputs.get(payload.get("call_id")); output = _output_text(paired or {})
        successful = paired is not None and not paired.get("is_error",False) and not re.search(r"(?:^|\b)(?:error|failed|invalid patch)(?:\b|:)", output, re.I)
        if successful: mutations.append({"mutator_session_id":session_id,"mutator_role":role or "root","files":paths,"call_id":payload.get("call_id"),"timestamp":e.get("timestamp")})
    return mutations


def _expectation_access_attempts(events: list[dict]) -> list[dict]:
    """Record observable tool traffic that may expose hidden v12 expectations."""
    needles=("frozen-plan-v12.json","workflow-v12-cases.json")
    attempts=[]
    for event in events:
        if event.get("type")!="response_item": continue
        payload=event.get("payload",{})
        if payload.get("type") not in {"custom_tool_call","custom_tool_call_output","function_call","function_call_output"}: continue
        value=json.dumps(payload,sort_keys=True,ensure_ascii=False).casefold()
        matched=[needle for needle in needles if needle in value]
        if matched: attempts.append({"timestamp":event.get("timestamp"),"matched":matched})
    return attempts


def _command_operation_labels(command: str) -> set[str]:
    labels=set()
    for segment in re.split(r"(?:&&|\|\||[;|\n])",command):
        try: words=shlex.split(segment)
        except ValueError: words=segment.strip().split()
        while words and ("=" in words[0] and not words[0].startswith(("./","/"))): words.pop(0)
        while words and words[0] in {"sudo","command","env"}: words.pop(0)
        if not words: continue
        executable=Path(words[0]).name.casefold().removeprefix("./")
        if executable in OPERATION_EXECUTABLES:
            labels.add("wsl" if executable=="wsl.exe" else "gradle" if executable=="gradlew" else executable)
        if executable=="git" and len(words)>1 and words[1] in {"merge","push"}: labels.add("git_"+words[1])
    return labels


def _command_texts_from_tool_payload(payload: dict) -> list[str]:
    if payload.get("type")=="function_call":
        name=str(payload.get("name","")).casefold()
        if "exec_command" not in name: return [name]
        try: args=json.loads(payload.get("arguments","{}"))
        except (TypeError,json.JSONDecodeError): return []
        return [str(args.get("cmd",""))]
    value=str(payload.get("input",""))
    if "exec_command" not in value: return []
    commands=[]
    for match in re.finditer(r"\bcmd\s*:\s*(\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|`[^`]*`)",value,re.S):
        literal=match.group(1)
        if literal.startswith('"'):
            try: commands.append(json.loads(literal))
            except json.JSONDecodeError: pass
        else: commands.append(literal[1:-1])
    return commands


def _direct_tool_operation_labels(name: str) -> set[str]:
    lowered=name.casefold(); labels=set()
    mapping={"ssh":"ssh","xcode":"xcodebuild","simctl":"simctl","adb":"adb","gradle":"gradle","wsl":"wsl","github":"gh","vercel":"vercel","supabase":"supabase","digitalocean":"doctl"}
    for token,label in mapping.items():
        if token in lowered: labels.add(label)
    if any(token in lowered for token in ("web__","web_search","browser")): labels.add("network_tool")
    if lowered.startswith("mcp__") and not labels: labels.add("provider_tool")
    return labels


def _operation_attempt_labels(events: list[dict]) -> list[str]:
    labels=set()
    for event in events:
        if event.get("type")!="response_item": continue
        payload=event.get("payload",{})
        if payload.get("type") not in {"custom_tool_call","function_call"}: continue
        if payload.get("name") in {"spawn_agent","send_message","followup_task","wait_agent"}: continue
        if payload.get("type")=="function_call" and "exec_command" not in str(payload.get("name","")).casefold():
            labels.update(_direct_tool_operation_labels(str(payload.get("name",""))))
        for command in _command_texts_from_tool_payload(payload): labels.update(_command_operation_labels(command))
    return sorted(labels)


def observed_session(path: Path, session_id: str, case_dir: Path) -> dict:
    events = parse_rollout(path)
    meta = next((e["payload"] for e in events if e.get("type") == "session_meta" and e.get("payload",{}).get("id") == session_id), {})
    contexts = [e["payload"] for e in events if e.get("type") == "turn_context"]
    context = contexts[-1] if contexts else {}
    turn_id = context.get("turn_id")
    # A root may send a follow-up after a child's implementation turn. Session
    # dependency order uses the first start and final completion, not the last
    # turn_context's task_started timestamp.
    start_events = [e for e in events if e.get("type") == "event_msg" and e.get("payload",{}).get("type") == "task_started" and e.get("timestamp")]
    finish_events = [e for e in events if e.get("type") == "event_msg" and e.get("payload",{}).get("type") == "task_complete" and e.get("timestamp")]
    starts = [e["timestamp"] for e in start_events]
    finishes = [e["timestamp"] for e in finish_events]
    latest_start = max(start_events, key=lambda e:e["timestamp"]) if start_events else None
    latest_turn = latest_start.get("payload",{}).get("turn_id") if latest_start else None
    complete = bool(latest_start and any(
        e["timestamp"] >= latest_start["timestamp"] and
        (latest_turn is None or e.get("payload",{}).get("turn_id") == latest_turn)
        for e in finish_events
    ))
    source = meta.get("source",{}); spawn = source.get("subagent",{}).get("thread_spawn",{}) if isinstance(source,dict) else {}
    role = spawn.get("agent_role")
    mutations = _successful_mutations(events, Path(context.get("cwd") or case_dir), session_id, role)
    handoffs=[]
    assistant_messages=[]
    spawn_calls=[]
    for e in events:
        payload=e.get("payload",{})
        if e.get("type")=="response_item" and payload.get("type")=="message" and payload.get("role")=="assistant":
            message=" ".join(x.get("text","") for x in payload.get("content",[]) if isinstance(x,dict))
            assistant_messages.append({"timestamp":e.get("timestamp"),"text":message})
            if re.search(r"\bhandoff\b",message,re.I): handoffs.append({"timestamp":e.get("timestamp"),"text":message})
        if e.get("type")=="response_item" and payload.get("type")=="function_call" and payload.get("name")=="spawn_agent":
            try: args=json.loads(payload.get("arguments","{}"))
            except (TypeError,json.JSONDecodeError): args={}
            message=args.get("message"); observable=isinstance(message,str) and not message.startswith("gAAAA")
            spawn_calls.append({"timestamp":e.get("timestamp"),"role":args.get("agent_type"),"fork_turns":args.get("fork_turns"),"message_observable":observable,"message_text":message if observable else None})
    return {"session_id":session_id,"parent_thread_id":spawn.get("parent_thread_id"),"depth":spawn.get("depth",0),"role":role,"model":context.get("model"),"effort":context.get("effort") or context.get("reasoning_effort"),"turn_id":turn_id,"started_at":min(starts) if starts else None,"completed_at":max(finishes) if finishes else None,"completed":complete,"handoff_markers":handoffs,"assistant_messages":assistant_messages,"spawn_calls":spawn_calls,"mutations":mutations,"mutation_observed":bool(mutations),"expectation_access_attempts":_expectation_access_attempts(events),"operation_attempt_labels":_operation_attempt_labels(events),"rollout":str(path)}


def collect_sessions(root_id: str, case_dir: Path, started_at: float) -> tuple[dict | None, list[dict]]:
    candidates = []
    sessions = Path.home() / ".codex/sessions"
    for path in sessions.glob("*/*/*/rollout-*.jsonl"):
        try:
            if path.stat().st_mtime >= started_at - 3: candidates.append(path)
        except OSError: pass
    root = None; observed = []
    for path in candidates:
        match = re.search(r"-(01[0-9a-f]{6}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$", path.name)
        if not match: continue
        sid = match.group(1); item = observed_session(path, sid, case_dir)
        if sid == root_id: root = item
        else: observed.append(item)
    descendants=[]; parents={root_id}
    while True:
        added=[x for x in observed if x not in descendants and x.get("parent_thread_id") in parents]
        if not added: break
        descendants.extend(added); parents.update(x["session_id"] for x in added)
    return root, descendants


def grade_roles(expected: dict, root: dict | None, children: list[dict], mutable_files: list[str] | None = None, case_dir: Path | None = None) -> list[str]:
    errors = []
    if not root: errors.append("missing_root_session")
    else:
        if (root.get("model"), root.get("effort")) != EXPECTED_ROOT: errors.append("wrong_root_profile")
        if not root.get("completed"): errors.append("root_not_complete")
    allowed_files={str((case_dir/name).resolve()) for name in (mutable_files or [])} if case_dir else set()
    if root:
        root_files={str(Path(f).resolve()) for m in root.get("mutations",[]) for f in m.get("files",[])}
        if expected and root_files: errors.append("root_mutated_delegated_files")
        if root_files-allowed_files: errors.append("root_mutated_outside_allowed_files")
        spawn_calls=root.get("spawn_calls",[])
        if len(spawn_calls)!=len(expected): errors.append("spawn_call_count")
        if any(x.get("role") not in expected for x in spawn_calls): errors.append("unexpected_spawn_call")
        for role in expected:
            role_spawns=[x for x in spawn_calls if x.get("role")==role]
            if len(role_spawns)!=1 or role_spawns[0].get("fork_turns")!="none": errors.append(f"spawn_contract:{role}")
    direct=[c for c in children if root and c.get("parent_thread_id")==root.get("session_id")]
    nested=[c for c in children if c not in direct]
    if nested: errors.append("unexpected_descendants")
    if any(not c.get("completed") for c in children): errors.append("incomplete_observed_child")
    if any(c.get("role") not in expected for c in direct): errors.append("unexpected_child")
    for child in children:
        if child.get("role") not in {"implementer","implementer_complex","systems_implementer"} and child.get("mutations"):
            errors.append(f"readonly_role_mutated:{child.get('role')}")
    child_files={str(Path(f).resolve()) for c in children for m in c.get("mutations",[]) for f in m.get("files",[])}
    if child_files-allowed_files: errors.append("child_mutated_outside_allowed_files")
    by_role={role:[c for c in direct if c.get("role")==role] for role in expected}
    if len(direct) != len(expected): errors.append("child_count")
    for role, profile in expected.items():
        matches=by_role.get(role,[])
        if len(matches)!=1:
            errors.append(f"child_count:{role}:{len(matches)}")
            if not matches: errors.append(f"missing_child:{role}")
            continue
        child=matches[0]
        if (child.get("model"), child.get("effort")) != tuple(profile): errors.append(f"wrong_profile:{role}")
        if not child.get("completed"): errors.append(f"child_not_complete:{role}")
        if role in {"implementer","implementer_complex","systems_implementer"}:
            child_files = {str(Path(f).resolve()) for m in child.get("mutations",[]) for f in m.get("files",[])}
            expected_files = allowed_files
            if not child.get("mutation_observed"): errors.append(f"no_child_mutation:{role}")
            elif expected_files and not expected_files.issubset(child_files): errors.append(f"unattributed_files:{role}")
    return errors


def grade_dependencies(case_id: str, root: dict | None, children: list[dict]) -> list[str]:
    dependencies={"templorojo-filters":(["product_discovery","ux_auditor"],"implementer_complex"),"ryven-regressions":(["systems_analyst"],"implementer_complex")}
    if case_id not in dependencies: return []
    upstream_roles,downstream_role=dependencies[case_id]; by_role={c.get("role"):c for c in children if root and c.get("parent_thread_id")==root.get("session_id")}
    upstream=[by_role.get(x) for x in upstream_roles]; downstream=by_role.get(downstream_role)
    if not downstream or any(x is None for x in upstream): return ["dependency_sessions_missing"]
    completed=[x.get("completed_at") for x in upstream]
    if any(x is None for x in completed) or downstream.get("started_at") is None: return ["dependency_time_unknown"]
    boundary=max(completed)
    errors=[]
    if downstream["started_at"] <= boundary: errors.append("downstream_started_before_upstream_complete")
    required={"templorojo-filters":[r"stock\s*>\s*0",r"variante",r"URL|serializaci[oó]n"],"ryven-regressions":[r"radio",r"30",r"guidance|gu[ií]a",r"cancel"]}[case_id]
    downstream_spawns=[x for x in (root.get("spawn_calls",[]) if root else []) if x.get("role")==downstream_role]
    if len(downstream_spawns)!=1: errors.append("downstream_spawn_payload_missing")
    elif downstream_spawns[0].get("message_observable"):
        markers=root.get("handoff_markers",[]) if root else []
        matching=[m for m in markers if m.get("timestamp") and boundary <= m["timestamp"] <= downstream["started_at"] and all(re.search(token,m.get("text",""),re.I) for token in required)]
        if not matching: errors.append("semantic_handoff_marker_missing_before_downstream")
        if not all(re.search(token,downstream_spawns[0].get("message_text") or "",re.I) for token in required): errors.append("downstream_handoff_payload_missing_semantics")
    else:
        receipt_tokens=RECEIPT_TOKENS[case_id]
        receipts=[m for m in downstream.get("assistant_messages",[]) if all(re.search(token,m.get("text","")+"",re.I) for token in receipt_tokens)]
        if not receipts:
            errors.append("downstream_contract_receipt_missing_or_wrong")
        else:
            receipt=receipts[0]; receipt_time=receipt.get("timestamp")
            mutation_times=[m.get("timestamp") for m in downstream.get("mutations",[]) if m.get("timestamp")]
            if not receipt_time or receipt_time < boundary:
                errors.append("downstream_contract_receipt_out_of_order")
            if mutation_times and receipt_time >= min(mutation_times):
                errors.append("downstream_contract_receipt_after_edit")
    return errors


def stop_process_group(proc: subprocess.Popen) -> None:
    try: os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError: return
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass


def run_bounded(cmd: list[str], cwd: Path, timeout: int, input_text: str | None = None) -> dict:
    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}
    proc=subprocess.Popen(cmd,cwd=cwd,stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,env=env)
    try:
        stdout,stderr=proc.communicate(input_text,timeout=timeout)
        return {"exit_code":proc.returncode,"timed_out":False,"stdout":stdout,"stderr":stderr}
    except subprocess.TimeoutExpired:
        stop_process_group(proc)
        stdout,stderr=proc.communicate()
        return {"exit_code":proc.returncode,"timed_out":True,"stdout":stdout,"stderr":stderr}


def grade_artifacts_bounded(case_id: str, case_dir: Path, timeout: int = 10) -> tuple[list[str], dict]:
    cmd=["/usr/bin/sandbox-exec","-p","(version 1)(allow default)(deny network*)(deny file-write*)",sys.executable,str(Path(__file__).resolve()),"--grade-artifact",case_id,str(case_dir)]
    result=run_bounded(cmd,case_dir,timeout)
    if result["timed_out"]: return ["artifact_grader_timeout"],result
    try: errors=json.loads(result["stdout"])["errors"]
    except Exception: errors=["artifact_grader_invalid_output"]
    if result["exit_code"] not in (0,1): errors.append("artifact_grader_failed")
    return errors,result


def run_case(codex: str, cfg: dict, case: dict, case_dir: Path, runtime_dir: Path, timeout: int, scratch_root: Path) -> dict:
    # Use one stable scratch root for every case. Codex persists cwd trust, so this
    # avoids adding one global trust entry per generated fixture.
    started = time.time(); cmd = [codex,"exec","--skip-git-repo-check","-s","workspace-write","--json","-o",str(case_dir/"root-result.txt"),"-C",str(scratch_root)]
    cmd += ["-c",f'projects.{json.dumps(str(scratch_root))}.trust_level="trusted"']
    for server in cfg.get("mcp_servers",{}): cmd += ["-c",f"mcp_servers.{server}.enabled=false"]
    for plugin in cfg.get("plugins",{}): cmd += ["-c",f"plugins.{plugin}.enabled=false"]
    cmd += ["-c","features.multi_agent=true","-c","sandbox_workspace_write.network_access=false","-c","web_search=\"disabled\"","-c","notify=[]","-"]
    prompt = case["prompt"] + "\nCase directory: " + str(case_dir)
    proc = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    timed_out = False
    try: stdout, stderr = proc.communicate(prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True; stop_process_group(proc); stdout, stderr = proc.communicate()
    runtime_dir.mkdir(parents=True,exist_ok=True)
    for name, data in [("events.jsonl",stdout),("stderr.txt",stderr)]:
        p=runtime_dir/name; p.write_text(data); p.chmod(0o600)
    match = re.search(r'"type":"thread.started","thread_id":"([^"]+)"', stdout)
    root_id = match.group(1) if match else None
    root = None; children = []
    if root_id:
        for _ in range(10):
            root, children = collect_sessions(root_id, case_dir, started)
            if root and root.get("completed") and all(c.get("completed") for c in children): break
            time.sleep(1)
    public_cmd=["/usr/bin/sandbox-exec","-p","(version 1)(allow default)(deny network*)(deny file-write*)",sys.executable,"public_tests.py"]
    public = run_bounded(public_cmd,case_dir,30)
    artifact_errors,artifact_run = grade_artifacts_bounded(case["id"], case_dir)
    role_errors = grade_roles(case["required_agents"], root, children, case["mutable_files"], case_dir) if root_id else ["missing_root_thread_id"]
    dependency_errors=grade_dependencies(case["id"],root,children)
    descendant_status="unknown_after_timeout" if timed_out else "all_observed_complete" if root and root.get("completed") and all(c.get("completed") for c in children) else "incomplete"
    return {"id":case["id"],"root_thread_id":root_id,"exit_code":proc.returncode,"timed_out":timed_out,"descendant_status":descendant_status,"seconds":round(time.time()-started,2),"root":root,"children":children,"role_errors":role_errors,"dependency_errors":dependency_errors,"artifact_errors":artifact_errors,"artifact_grader_timed_out":artifact_run["timed_out"],"public_test_exit":public["exit_code"],"public_test_timed_out":public["timed_out"],"public_test_output":(public["stdout"]+public["stderr"])[-2000:],"reported_usage":[json.loads(x).get("usage") for x in stdout.splitlines() if '"type":"turn.completed"' in x and _is_json(x)],"passed":not timed_out and proc.returncode==0 and public["exit_code"]==0 and not public["timed_out"] and not role_errors and not dependency_errors and not artifact_errors}


def _is_json(value: str) -> bool:
    try: json.loads(value); return True
    except json.JSONDecodeError: return False


def _v12_fixture_hashes(case: dict) -> dict[str, str]:
    return {name:hashlib.sha256(text.encode()).hexdigest() for name,text in case.get("files",{}).items()}


def v12_contract_fingerprint(manifest_path: Path) -> dict:
    manifest=json.loads(manifest_path.read_text())
    rows=[]; drift=[]
    for item in manifest.get("files",[]):
        path=Path(item["path"]); expected=item.get("after_sha256")
        actual=sha256(path) if path.exists() and path.is_file() else None
        if actual!=expected: drift.append(path.name)
        rows.append((str(path),actual))
    if drift: raise ValueError("v12 contract drift: "+",".join(sorted(drift)))
    digest=hashlib.sha256("\n".join(f"{path}\0{value}" for path,value in sorted(rows)).encode()).hexdigest()
    return {"manifest_sha256":sha256(manifest_path),"effective_contract_sha256":digest,"verified_file_count":len(rows)}


def _v12_frozen_plan(cases: list[dict], timeout: int, workers: int, contract_fingerprint: dict) -> dict:
    catalog_bytes=V12_CASES_PATH.read_bytes()
    return {
        "suite":"v12",
        "rubric_version":V12_RUBRIC_VERSION,
        "case_catalog_sha256":hashlib.sha256(catalog_bytes).hexdigest(),
        "runner_sha256":sha256(Path(__file__).resolve()),
        "effective_contract":contract_fingerprint,
        "case_count":len(cases),
        "timeout_seconds_per_case":timeout,
        "max_concurrent_roots":workers,
        "network":False,
        "providers":False,
        "cases":[{
            "id":c["id"],
            "route":c["route"],
            "frequency_class":c["frequency_class"],
            "reference_regression":c["reference_regression"],
            "summary":c["summary"],
            "fixture_hashes":_v12_fixture_hashes(c),
            "routing":c["routing"],
            "mutable_files":c["mutable_files"],
            "mutation_owners":c["mutation_owners"],
            "review_files":c["review_files"],
            "child_evidence":c.get("child_evidence",{}),
            "required_output":c["required_output"],
            "artifact":c["artifact"],
            "artifact_expect":c.get("artifact_expect",{}),
        } for c in cases],
        "limits":[
            "natural-language routing cases; expectations are frozen before model execution",
            "fixtures and provider states are synthetic; no live product or provider claim",
            "no comparative model-quality, cost, or savings conclusion",
            "a hash-bound terminal receipt proves a separate reviewer emitted a favorable verdict for the final bytes; it does not prove review depth or native GitHub approval",
            "hidden controls are outside the ordinary model cwd but are not OS read-isolated; observable access to the frozen plan or case catalog invalidates the affected case",
        ],
    }


def _v12_prompt(case: dict, case_dir: Path) -> str:
    # Expose only the response schema. Expected values stay in the frozen grader
    # so a model must derive them from the fixture rather than echo the rubric.
    required="\n".join(token.split("=",1)[0]+"=<derive from fixture>" for token in case["required_output"])
    json_schemas=[]
    def outline(value):
        if isinstance(value,dict): return {key:outline(child) for key,child in value.items()}
        if isinstance(value,list): return ["<derive from fixture>"]
        return "<derive from fixture>"
    for name,expected in case.get("artifact_expect",{}).get("json",{}).items():
        json_schemas.append(name+":\n"+json.dumps(outline(expected),indent=2,ensure_ascii=False))
    schema_text=("\nRequired JSON artifact schemas (use these exact keys; derive every value from the fixture):\n"+"\n".join(json_schemas)) if json_schemas else ""
    return (
        case["prompt"]+
        "\n\nSimulation boundary: use only the sanitized fixture at "+str(case_dir)+
        ". Do not access network, providers, SSH, GitHub, credentials, private messages, or production. "
        "Do not create unrelated tasks. Keep the final response under 350 words. "
        "If product code changes, the exact final files must receive independent review after their last edit; "
        "the reviewer's terminal output must end with exactly `FINAL_REVIEW_RECEIPT PASS "
        "file=sha256 ...` using each reviewed file's final lowercase SHA-256, or end with concrete findings and no favorable receipt. "+
        schema_text+"\nEnd with SIM_RESULT followed by these exact result lines, one per line:\n"+required+"\n"
    )


def _nested_subset(actual, expected) -> bool:
    if isinstance(expected,dict):
        return isinstance(actual,dict) and all(k in actual and _nested_subset(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):
        return actual == expected
    return actual == expected


def _normalized_output(value: str) -> str:
    return re.sub(r"[^a-z0-9]+","_",value.casefold()).strip("_")


def _output_rule_matches(value: str, rule) -> bool:
    if rule=="presence": return bool(value.strip())
    if isinstance(rule,list): return _normalized_output(value) in {_normalized_output(x) for x in rule}
    if isinstance(rule,dict) and "regex" in rule: return re.fullmatch(rule["regex"],_normalized_output(value),re.I) is not None
    return value==str(rule)


def _positive_review_approval(text: str) -> bool:
    pattern=r"\b(?:approve|approved|aprobado|aprobada|aprobar|veredicto favorable|sin hallazgos|lgtm|ready to merge|recommend merging|acceptable candidate)\b"
    for match in re.finditer(pattern,text,re.I):
        prefix=text[max(0,match.start()-28):match.start()].casefold()
        if not re.search(r"\b(?:no|not|without)\b[^.!?\n]{0,18}$",prefix): return True
    return False


def grade_v12_artifacts(case: dict, case_dir: Path) -> list[str]:
    errors=[]
    result_path=case_dir/"root-result.txt"
    if not result_path.exists():
        errors.append("missing_root_result")
        result=""
    else:
        result=result_path.read_text(errors="replace")
    lines=result.splitlines()
    markers=[i for i,line in enumerate(lines) if line.strip()=="SIM_RESULT"]
    expected_lines=case.get("required_output",[])
    expected={line.split("=",1)[0]:line.split("=",1)[1] for line in expected_lines}
    if len(markers)!=1:
        errors.append("sim_result_marker_count")
    else:
        block=[line.strip() for line in lines[markers[0]+1:] if line.strip()]
        parsed={}; malformed=False
        for line in block:
            if "=" not in line:
                malformed=True; continue
            key,value=line.split("=",1)
            if not key or key in parsed: errors.append(f"duplicate_output_key:{key}")
            else: parsed[key]=value
        if malformed: errors.append("malformed_sim_result_line")
        if len(block)!=len(expected_lines): errors.append("sim_result_line_count")
        output_mode=case.get("required_output_mode","exact"); output_expect=case.get("output_expect",{})
        for key,value in expected.items():
            if key not in parsed: errors.append(f"missing_output_key:{key}")
            elif key in output_expect and not _output_rule_matches(parsed[key],output_expect[key]): errors.append(f"wrong_output_semantics:{key}")
            elif output_mode=="exact" and parsed[key]!=value: errors.append(f"wrong_output_value:{key}")
            elif output_mode=="presence" and not parsed[key].strip(): errors.append(f"empty_output_value:{key}")
        for key in parsed.keys()-expected.keys(): errors.append(f"unexpected_output_key:{key}")
    expect=case.get("artifact_expect",{})
    for name,subset in expect.get("json",{}).items():
        try: actual=json.loads((case_dir/name).read_text())
        except Exception as exc:
            errors.append(f"json_artifact:{name}:{type(exc).__name__}")
        else:
            if not _nested_subset(actual,subset): errors.append(f"json_subset:{name}")
            if name in case.get("exact_json_artifacts",[]) and actual!=subset: errors.append(f"json_exact:{name}")
    kind=case.get("artifact")
    if kind == "media":
        try:
            required=json.loads((case_dir/"inventory.json").read_text())["required"]
            rows=json.loads((case_dir/"manifest.json").read_text())
            by_id={x.get("id"):x for x in rows}
            if len(rows)!=len(required) or set(by_id)!={x["id"] for x in required}: errors.append("media_universe")
            for src in required:
                row=by_id.get(src["id"],{})
                action="correct-background" if src["white"] else "keep"
                if row.get("source")!=src["source"] or row.get("action")!=action: errors.append(f"media_mapping:{src['id']}")
                if action=="correct-background" and row.get("output")!=f"corrected/{src['id']}.png": errors.append(f"media_output:{src['id']}")
                if action=="keep" and row.get("output") not in (None,src["source"]): errors.append(f"media_keep:{src['id']}")
        except Exception as exc: errors.append(f"media_exception:{type(exc).__name__}")
    elif kind == "xlsx":
        try:
            import openpyxl
            source=json.loads((case_dir/"rows.json").read_text())
            wb=openpyxl.load_workbook(case_dir/"Apreciaciones.xlsx",data_only=False,read_only=True)
            ws=wb.active
            headers=[ws.cell(1,c).value for c in range(1,6)]
            expected_headers=["ID","Texto fuente","Comentario","Apreciación Legal","Apreciación Técnica"]
            if headers!=expected_headers: errors.append("xlsx_headers")
            if ws.max_row!=len(source)+1: errors.append("xlsx_row_count")
            for idx,row in enumerate(source,2):
                actual=[ws.cell(idx,c).value for c in range(1,6)]
                if actual[:3]!=[row["ID"],row["Texto fuente"],row["Comentario"]]: errors.append(f"xlsx_source:{idx}")
                if any(value not in (None,"") for value in actual[3:]): errors.append(f"xlsx_reserved:{idx}")
            wb.close()
        except Exception as exc: errors.append(f"xlsx_exception:{type(exc).__name__}")
    if case["id"] in {"pr-preauthorized","pr-wait-authority"}:
        try:
            state=json.loads((case_dir/"pr_state.json").read_text())
            if state.get("reviewed_head")!=sha256(case_dir/"calculator.py"): errors.append("reviewed_head_mismatch")
        except Exception as exc: errors.append(f"pr_state_exception:{type(exc).__name__}")
    if case["id"] == "server-release-simulated":
        try:
            actual=json.loads((case_dir/"service_state.json").read_text())
            expected_services=case["artifact_expect"]["json"]["service_state.json"]["services"]
            if set(actual.get("services",{}))!=set(expected_services): errors.append("service_universe")
        except Exception as exc: errors.append(f"service_universe_exception:{type(exc).__name__}")
    return errors


def grade_v12_artifacts_bounded(case: dict, case_dir: Path, timeout: int = 15) -> tuple[list[str], dict]:
    cmd=["/usr/bin/sandbox-exec","-p","(version 1)(allow default)(deny network*)(deny file-write*)",sys.executable,str(Path(__file__).resolve()),"--grade-v12-artifact",case["id"],str(case_dir)]
    result=run_bounded(cmd,case_dir,timeout)
    if result["timed_out"]: return ["artifact_grader_timeout"],result
    try: errors=json.loads(result["stdout"])["errors"]
    except Exception: errors=["artifact_grader_invalid_output"]
    if result["exit_code"] not in (0,1): errors.append("artifact_grader_failed")
    return errors,result


def _v12_profile_map(case: dict) -> dict[str, tuple[str,str]]:
    profiles={role:tuple(value) for role,value in case["routing"].get("required",{}).items()}
    for group in case["routing"].get("optional_groups",[]):
        for alternatives in group:
            for role,value in alternatives.items(): profiles[role]=tuple(value)
    return profiles


def grade_v12_routing(case: dict, root: dict | None, children: list[dict], case_dir: Path) -> list[str]:
    errors=[]
    if not root: return ["missing_root_session"]
    if (root.get("model"),root.get("effort"))!=EXPECTED_ROOT: errors.append("wrong_root_profile")
    if not root.get("completed"): errors.append("root_not_complete")
    direct=[c for c in children if c.get("parent_thread_id")==root.get("session_id")]
    nested=[c for c in children if c not in direct]
    if nested: errors.append("unexpected_descendants")
    if any(not c.get("completed") for c in children): errors.append("incomplete_child")
    spec=case["routing"]; required=spec.get("required",{}); profiles=_v12_profile_map(case)
    allowed=set(profiles); forbidden=set(spec.get("forbidden",[]))
    if len(direct)>spec.get("max_children",len(allowed)): errors.append("fanout_exceeded")
    roles=[c.get("role") for c in direct]
    for role in required:
        if roles.count(role)!=1: errors.append(f"required_role_count:{role}:{roles.count(role)}")
    for group in spec.get("optional_groups",[]):
        group_roles={role for alternatives in group for role in alternatives}
        if sum(roles.count(role) for role in group_roles)>1: errors.append("optional_group_exceeded:"+",".join(sorted(group_roles)))
    if any(role not in allowed for role in roles): errors.append("unexpected_child_role")
    if forbidden.intersection(roles): errors.append("forbidden_child_role")
    for child in direct:
        role=child.get("role")
        if role in profiles and (child.get("model"),child.get("effort"))!=profiles[role]: errors.append(f"wrong_profile:{role}")
        required_evidence=case.get("child_evidence",{}).get(role,[])
        if required_evidence:
            own_text="\n".join(m.get("text","") for m in child.get("assistant_messages",[])).casefold()
            if not all(token.casefold() in own_text for token in required_evidence): errors.append(f"child_original_evidence_missing:{role}")
    spawn_calls=root.get("spawn_calls",[])
    if len(spawn_calls)!=len(direct): errors.append("spawn_child_count_mismatch")
    if any(x.get("fork_turns")!="none" for x in spawn_calls): errors.append("fork_turns_not_none")
    spawn_roles=[x.get("role") for x in spawn_calls]
    if sorted(str(x) for x in spawn_roles)!=sorted(str(x) for x in roles): errors.append("spawn_role_mismatch")
    allowed_paths={str((case_dir/name).resolve()):name for name in case.get("mutable_files",[])}
    observed_by_file={name:[] for name in case.get("mutable_files",[])}
    actors=[("root",root)]+[(c.get("role") or "unknown",c) for c in children]
    forbidden_attempts=set(case.get("forbidden_tool_labels",[]))
    for role,actor in actors:
        for label in forbidden_attempts.intersection(actor.get("operation_attempt_labels",[])):
            errors.append(f"forbidden_tool_attempt:{role}:{label}")
        actor_id=actor.get("session_id") or ("root" if role=="root" else role)
        for mutation in actor.get("mutations",[]):
            for raw in mutation.get("files",[]):
                path=str(Path(raw).resolve()); name=allowed_paths.get(path)
                if name is None:
                    errors.append(f"mutation_outside_allowlist:{role}")
                    continue
                observed_by_file[name].append((role,actor_id,mutation.get("timestamp")))
                if role not in case.get("mutation_owners",{}).get(name,[]): errors.append(f"wrong_mutation_owner:{name}:{role}")
    for name in case.get("mutable_files",[]):
        if name.endswith(".xlsx"): continue
        if not observed_by_file.get(name): errors.append(f"missing_mutation:{name}")
        if len({actor_id for _,actor_id,_ in observed_by_file.get(name,[])})>1: errors.append(f"multiple_writers:{name}")
    review_files=case.get("review_files",[])
    if review_files:
        reviewers=[c for c in direct if c.get("role")=="independent_reviewer"]
        if len(reviewers)!=1:
            errors.append("missing_independent_final_review")
        else:
            reviewer=reviewers[0]
            mutation_times=[timestamp for name in review_files for _,_,timestamp in observed_by_file.get(name,[]) if timestamp]
            if not mutation_times:
                errors.append("review_without_observed_candidate")
            else:
                final_edit=max(mutation_times)
                messages=[m for m in reviewer.get("assistant_messages",[]) if m.get("timestamp")]
                terminal=max(messages,key=lambda m:m["timestamp"]) if messages else None
                try:
                    expected_receipt="FINAL_REVIEW_RECEIPT PASS "+" ".join(f"{name}={sha256(case_dir/name)}" for name in review_files)
                except Exception:
                    expected_receipt=None
                terminal_lines=[line.strip() for line in (terminal.get("text","") if terminal else "").splitlines() if line.strip()]
                if not terminal or terminal["timestamp"]<final_edit or not expected_receipt or not terminal_lines or terminal_lines[-1]!=expected_receipt:
                    errors.append("final_head_review_receipt_missing_or_mismatched")
    root_messages=[m for m in root.get("assistant_messages",[]) if m.get("timestamp")]
    root_terminal=max(root_messages,key=lambda m:m["timestamp"]) if root_messages else None
    for handoff in case.get("handoff_requirements",[]):
        matches=[c for c in direct if c.get("role")==handoff["role"]]
        if len(matches)!=1 or not matches[0].get("completed_at"):
            errors.append(f"handoff_incomplete:{handoff['role']}")
            continue
        child=matches[0]; boundary=child["completed_at"]
        if not root_terminal or root_terminal["timestamp"]<=boundary:
            errors.append(f"root_closed_before_handoff:{handoff['role']}")
        if handoff.get("before_mutation"):
            times=[t for _,_,t in observed_by_file.get(handoff["before_mutation"],[]) if t]
            if not times or min(times)<=boundary: errors.append(f"mutation_not_after_handoff:{handoff['before_mutation']}")
        text=(root_terminal or {}).get("text","").casefold()
        if not all(token.casefold() in text for token in handoff.get("root_receipt_tokens",[])):
            errors.append(f"root_handoff_evidence_missing:{handoff['role']}")
    if case.get("forbid_favorable_review_receipt"):
        for child in direct:
            if child.get("role")!="independent_reviewer": continue
            review_text="\n".join(m.get("text","") for m in child.get("assistant_messages",[]))
            if re.search(r"FINAL_REVIEW_RECEIPT\s+PASS",review_text,re.I) or (case.get("forbid_review_approval") and _positive_review_approval(review_text)):
                errors.append("favorable_review_forbidden_by_conflict")
    finding=case.get("required_review_finding")
    if finding:
        reviewers=[c for c in direct if c.get("role")==finding["role"]]
        messages=[m for m in (reviewers[0].get("assistant_messages",[]) if len(reviewers)==1 else []) if m.get("timestamp")]
        terminal=max(messages,key=lambda m:m["timestamp"]) if messages else None
        lines=[x.strip() for x in ((terminal or {}).get("text","")).splitlines() if x.strip()]
        if not lines or lines[-1]!=finding["terminal_line"]: errors.append("required_review_finding_missing")
    return errors


def _v12_run_command(codex: str, cfg: dict, case: dict, case_dir: Path, scratch_root: Path) -> list[str]:
    # The fixture is the model's execution contract. Keep its absolute path in
    # the prompt and make it the process cwd so relative artifact paths resolve
    # to the same bounded location.
    cmd=[codex,"exec","--skip-git-repo-check","-s","workspace-write","--json","-o",str(case_dir/"root-result.txt"),"-C",str(case_dir)]
    cmd += ["-c",f'projects.{json.dumps(str(case_dir))}.trust_level="trusted"']
    for server in cfg.get("mcp_servers",{}): cmd += ["-c",f"mcp_servers.{server}.enabled=false"]
    for plugin in cfg.get("plugins",{}): cmd += ["-c",f"plugins.{plugin}.enabled=false"]
    cmd += ["-c","features.multi_agent=true","-c","sandbox_workspace_write.network_access=false","-c","web_search=\"disabled\"","-c","notify=[]","-"]
    return cmd


def run_v12_case(codex: str, cfg: dict, case: dict, case_dir: Path, runtime_dir: Path, timeout: int, scratch_root: Path) -> dict:
    started=time.time()
    cmd=_v12_run_command(codex,cfg,case,case_dir,scratch_root)
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    timed_out=False
    try: stdout,stderr=proc.communicate(_v12_prompt(case,case_dir),timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True; stop_process_group(proc); stdout,stderr=proc.communicate()
    runtime_dir.mkdir(parents=True,exist_ok=True)
    runtime_dir.chmod(0o700)
    for name,data in (("events.jsonl",stdout),("stderr.txt",stderr)):
        path=runtime_dir/name; path.write_text(data); path.chmod(0o600)
    match=re.search(r'"type":"thread.started","thread_id":"([^"]+)"',stdout)
    root_id=match.group(1) if match else None
    root=None; children=[]
    if root_id:
        for _ in range(10):
            root,children=collect_sessions(root_id,case_dir,started)
            if root and root.get("completed") and all(c.get("completed") for c in children): break
            time.sleep(1)
    public={"exit_code":0,"timed_out":False,"stdout":"","stderr":""}
    if case.get("artifact")=="python_tests":
        public_cmd=["/usr/bin/sandbox-exec","-p","(version 1)(allow default)(deny network*)(deny file-write*)",sys.executable,"public_tests.py"]
        public=run_bounded(public_cmd,case_dir,30)
    artifact_errors,artifact_run=grade_v12_artifacts_bounded(case,case_dir)
    role_errors=grade_v12_routing(case,root,children,case_dir) if root_id else ["missing_root_thread_id"]
    expectation_access_count=sum(len(actor.get("expectation_access_attempts",[])) for actor in ([root] if root else [])+children)
    if expectation_access_count: role_errors.append("hidden_expectation_access_observed")
    immutable={name:digest for name,digest in _v12_fixture_hashes(case).items() if name not in case.get("mutable_files",[])}
    immutable_errors=[name for name,digest in immutable.items() if not (case_dir/name).exists() or sha256(case_dir/name)!=digest]
    allowed=set(case.get("files",{}))|set(case.get("mutable_files",[]))|{"root-result.txt","__pycache__"}
    unexpected=[p.name for p in case_dir.iterdir() if p.name not in allowed]
    passed=not timed_out and proc.returncode==0 and public["exit_code"]==0 and not public["timed_out"] and not artifact_errors and not role_errors and not immutable_errors and not unexpected
    private={"root_thread_id":root_id,"started_epoch":started,"root":root,"children":children}
    private_path=runtime_dir/"grade-private.json"; private_path.write_text(json.dumps(private,indent=2)); private_path.chmod(0o600)
    return {"id":case["id"],"route":case["route"],"frequency_class":case["frequency_class"],"reference_regression":case["reference_regression"],"passed":passed,"exit_code":proc.returncode,"timed_out":timed_out,"seconds":round(time.time()-started,2),"descendant_status":"unknown_after_timeout" if timed_out else "all_observed_complete" if root and root.get("completed") and all(c.get("completed") for c in children) else "incomplete","root_profile":{"model":root.get("model"),"effort":root.get("effort"),"completed":root.get("completed")} if root else None,"children":[{"role":c.get("role"),"model":c.get("model"),"effort":c.get("effort"),"completed":c.get("completed")} for c in children],"role_errors":role_errors,"artifact_errors":artifact_errors,"artifact_grader_timed_out":artifact_run["timed_out"],"public_test_exit":public["exit_code"],"public_test_timed_out":public["timed_out"],"immutable_errors":immutable_errors,"unexpected_files":unexpected,"hidden_expectation_access_observed":bool(expectation_access_count)}


def _project_keys(config_path: Path) -> set[str]:
    try: return set(tomllib.loads(config_path.read_text()).get("projects",{}))
    except Exception: return set()


def _scratch_project_keys(keys: set[str], scratch: Path) -> set[str]:
    result=set(); scratch=scratch.resolve()
    for key in keys:
        try:
            path=Path(key).resolve()
            if path==scratch or path.is_relative_to(scratch): result.add(key)
        except Exception: continue
    return result


def cleanup_created_scratch_trust(config_path: Path, scratch: Path, before: set[str]) -> tuple[list[str], list[str]]:
    after=_project_keys(config_path); created=sorted(_scratch_project_keys(after,scratch)-before)
    if not created: return [],[]
    text_value=config_path.read_text(); updated=text_value; removed=[]; errors=[]
    for key in created:
        header="[projects."+json.dumps(key)+"]"
        pattern=re.compile(r"(?m)^"+re.escape(header)+r"\s*$\n?(?:(?!^\[).*(?:\n|\Z))*")
        newer,count=pattern.subn("",updated,count=1)
        if count==1: updated=newer; removed.append(key)
        else: errors.append("trust_block_not_found:"+key)
    if removed:
        try:
            tomllib.loads(updated)
            mode=config_path.stat().st_mode
            temp=config_path.with_name(config_path.name+f".workflow-v12-{os.getpid()}.tmp")
            temp.write_text(updated); os.chmod(temp,mode); os.replace(temp,config_path)
            remaining=_project_keys(config_path)
            for key in removed:
                if key in remaining: errors.append("trust_cleanup_verify_failed:"+key)
        except Exception as exc: errors.append("trust_cleanup_exception:"+type(exc).__name__)
    return removed,errors


@contextmanager
def scratch_trust_guard(config_path: Path, scratch: Path, before: set[str]):
    state={"removed":[],"errors":[]}
    try:
        yield state
    finally:
        state["removed"],state["errors"]=cleanup_created_scratch_trust(config_path,scratch,before)


def _v12_layout(out: Path) -> tuple[Path,Path]:
    return out/"control",out/"workspace"


def run_v12_suite(a, cases: list[dict]) -> int:
    if a.regrade: raise SystemExit("v12 regrade is not available before a preserved run exists")
    if not 1<=a.workers<=2: raise SystemExit("v12 workers must be 1 or 2")
    if not a.contract_manifest: raise SystemExit("v12 requires --contract-manifest")
    out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True); out.chmod(0o700)
    control_root,workspace_root=_v12_layout(out); control_root.mkdir(exist_ok=True); workspace_root.mkdir(exist_ok=True); control_root.chmod(0o700); workspace_root.chmod(0o700)
    contract=v12_contract_fingerprint(a.contract_manifest.resolve())
    frozen=_v12_frozen_plan(cases,a.timeout,a.workers,contract); frozen_path=control_root/"frozen-plan-v12.json"
    if a.dry_run:
        frozen_path.write_text(json.dumps(frozen,indent=2)+"\n"); frozen_path.chmod(0o600)
        print(json.dumps({"mode":"dry-run","suite":"v12","cases":len(cases),"frozen_plan":str(frozen_path),"catalog_sha256":frozen["case_catalog_sha256"],"runner_sha256":frozen["runner_sha256"],"max_concurrent_roots":a.workers,"timeout_seconds_per_case":a.timeout},indent=2))
        return 0
    if not frozen_path.exists(): raise SystemExit("run requires frozen-plan-v12.json from --dry-run")
    prior=json.loads(frozen_path.read_text())
    if prior!=frozen: raise SystemExit("frozen v12 plan does not match current cases, runner, timeout, workers, or selection")
    execution_root=workspace_root/(time.strftime("%Y%m%dT%H%M%S")+f"-{os.getpid()}"); execution_root.mkdir(parents=True); execution_root.chmod(0o700)
    run_root=execution_root/"cases"; run_root.mkdir(); run_root.chmod(0o700)
    prepared=[]
    for case in cases:
        case_dir=run_root/case["id"]/"fixture"; runtime=run_root/case["id"]/"runtime"; case_dir.mkdir(parents=True)
        for name,value in case.get("files",{}).items():
            path=case_dir/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(value)
        prepared.append((case,case_dir,runtime))
    config_path=Path.home()/".codex/config.toml"; cfg=tomllib.loads(config_path.read_text()); before=_scratch_project_keys(_project_keys(config_path),execution_root)
    results=[]
    with scratch_trust_guard(config_path,execution_root,before) as trust_state:
        # The first root establishes the single workspace trust record before
        # concurrency, avoiding simultaneous Codex writes to config.toml.
        first_case,first_dir,first_runtime=prepared[0]
        try: first=run_v12_case(a.codex,cfg,first_case,first_dir,first_runtime,a.timeout,execution_root)
        except Exception as exc: first={"id":first_case["id"],"route":first_case["route"],"frequency_class":first_case["frequency_class"],"reference_regression":first_case["reference_regression"],"passed":False,"runner_error":type(exc).__name__}
        results.append(first)
        print(json.dumps({"case":first["id"],"passed":first.get("passed"),"seconds":first.get("seconds"),"role_errors":first.get("role_errors"),"artifact_errors":first.get("artifact_errors")}),flush=True)
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            futures={pool.submit(run_v12_case,a.codex,cfg,case,case_dir,runtime,a.timeout,execution_root):(case,case_dir) for case,case_dir,runtime in prepared[1:]}
            for future in as_completed(futures):
                case,_=futures[future]
                try: item=future.result()
                except Exception as exc: item={"id":case["id"],"route":case["route"],"frequency_class":case["frequency_class"],"reference_regression":case["reference_regression"],"passed":False,"runner_error":type(exc).__name__}
                results.append(item)
                print(json.dumps({"case":item["id"],"passed":item.get("passed"),"seconds":item.get("seconds"),"role_errors":item.get("role_errors"),"artifact_errors":item.get("artifact_errors")}),flush=True)
    removed,cleanup_errors=trust_state["removed"],trust_state["errors"]
    order={case["id"]:i for i,case in enumerate(cases)}; results.sort(key=lambda x:order[x["id"]])
    observed_profiles={}
    for item in results:
        rows=[{"role":"root",**(item.get("root_profile") or {})}]+item.get("children",[])
        for row in rows:
            if not row.get("model") or not row.get("effort"): continue
            key=f"{row.get('role')}|{row['model']}|{row['effort']}"; observed_profiles[key]=observed_profiles.get(key,0)+1
    report={"suite":"v12","rubric_version":V12_RUBRIC_VERSION,"kind":"natural-language-sanitized-workflow-simulations","case_catalog_sha256":frozen["case_catalog_sha256"],"runner_sha256":frozen["runner_sha256"],"effective_contract":frozen["effective_contract"],"case_count":len(cases),"frequency_coverage":{"usual":sum(c["frequency_class"]=="usual" for c in cases),"less_common":sum(c["frequency_class"]=="less_common" for c in cases)},"passed_count":sum(bool(x.get("passed")) for x in results),"failed_count":sum(not bool(x.get("passed")) for x in results),"observed_profile_coverage":observed_profiles,"results":results,"trust_cleanup":{"created_scratch_entries_removed":len(removed),"errors":cleanup_errors},"limits":frozen["limits"]+["successful apply_patch calls are actor-attributed; binary workbook attribution is inferred from the sole root process and independently graded artifact"]}
    report_path=execution_root/"public-results.json"; report_path.write_text(json.dumps(report,indent=2)+"\n"); report_path.chmod(0o600)
    if a.report_json:
        target=a.report_json.resolve(); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"results":str(report_path),"passed":report["passed_count"],"failed":report["failed_count"],"trust_cleanup_errors":cleanup_errors}))
    return 0 if report["failed_count"]==0 and not cleanup_errors else 1


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--codex",default=shutil.which("codex")); p.add_argument("--output",type=Path,required=True); p.add_argument("--timeout",type=int,default=600); p.add_argument("--cases",nargs="+"); p.add_argument("--run",action="store_true"); p.add_argument("--dry-run",action="store_true"); p.add_argument("--regrade",action="store_true"); p.add_argument("--suite",choices=["v11","v12"],default="v11"); p.add_argument("--workers",type=int,default=1); p.add_argument("--report-json",type=Path); p.add_argument("--contract-manifest",type=Path); a=p.parse_args()
    if sum([a.run,a.dry_run,a.regrade]) != 1: p.error("choose exactly one of --run, --dry-run or --regrade")
    if not 60 <= a.timeout <= 1200: p.error("timeout must be 60..1200 seconds per case")
    cases_path=V12_CASES_PATH if a.suite=="v12" else CASES_PATH
    cases=json.loads(cases_path.read_text()); selected=[c for c in cases if not a.cases or c["id"] in a.cases]
    if len(selected) != (len(a.cases) if a.cases else len(cases)): p.error("unknown or duplicate case id")
    if a.suite=="v12": return run_v12_suite(a,selected)
    plan={"mode":"regrade" if a.regrade else "run" if a.run else "dry-run","cases":[{"id":c["id"],"agents":c["required_agents"],"summary":c["summary"]} for c in selected],"timeout_seconds_per_case":a.timeout,"providers":False,"network":False,"kind":"forced-role-resolution-and-artifact-simulation-not-model-benchmark"}
    if a.dry_run: print(json.dumps(plan,indent=2)); return 0
    out=a.output.resolve()
    if a.regrade:
        source=out/"results.json"
        if not source.exists(): p.error(f"missing prior results: {source}")
        prior=json.loads(source.read_text()); by_id={c["id"]:c for c in selected}; regraded=[]
        for old in prior.get("results",[]):
            if old.get("id") not in by_id: continue
            case=by_id[old["id"]]; case_dir=out/case["id"]/"fixture"; runtime=out/case["id"]/"runtime/events.jsonl"; root_id=old.get("root_thread_id")
            root,children=collect_sessions(root_id,case_dir,runtime.stat().st_mtime-a.timeout-30) if root_id else (None,[])
            public_cmd=["/usr/bin/sandbox-exec","-p","(version 1)(allow default)(deny network*)(deny file-write*)",sys.executable,"public_tests.py"]
            public=run_bounded(public_cmd,case_dir,30); artifact_errors,artifact_run=grade_artifacts_bounded(case["id"],case_dir)
            role_errors=grade_roles(case["required_agents"],root,children,case["mutable_files"],case_dir) if root_id else ["missing_root_thread_id"]
            dependency_errors=grade_dependencies(case["id"],root,children)
            immutable={name:hashlib.sha256(text.encode()).hexdigest() for name,text in FIXTURES[case["id"]].items() if name not in case["mutable_files"]}
            immutable_errors=[name for name,digest in immutable.items() if not (case_dir/name).exists() or sha256(case_dir/name)!=digest]
            allowed=set(FIXTURES[case["id"]])|set(case["mutable_files"])|{"root-result.txt","__pycache__"}; unexpected=[x.name for x in case_dir.iterdir() if x.name not in allowed]
            item={**old,"root":root,"children":children,"role_errors":role_errors,"dependency_errors":dependency_errors,"artifact_errors":artifact_errors,"artifact_grader_timed_out":artifact_run["timed_out"],"public_test_exit":public["exit_code"],"public_test_timed_out":public["timed_out"],"public_test_output":(public["stdout"]+public["stderr"])[-2000:],"immutable_errors":immutable_errors,"unexpected_files":unexpected}
            item["passed"]=old.get("exit_code")==0 and not old.get("timed_out") and public["exit_code"]==0 and not public["timed_out"] and not role_errors and not dependency_errors and not artifact_errors and not immutable_errors and not unexpected
            regraded.append(item)
        report={"kind":plan["kind"],"rubric_version":"2.3","regraded_from":str(source),"results":regraded,"billing_cost":None,"limits":prior.get("limits",[])+["an observable child receipt confirms acceptance before editing; it does not decrypt or prove byte-for-byte prompt delivery"]}
        target=out/"regraded-results-v2.3.json"; target.write_text(json.dumps(report,indent=2)); target.chmod(0o600); print(json.dumps({"results":str(target),"cases":[[x["id"],x["passed"]] for x in regraded]})); return 0 if regraded and all(x["passed"] for x in regraded) else 1
    out.mkdir(parents=True,exist_ok=True); out.chmod(0o700)
    run_root=out/"runs"/(time.strftime("%Y%m%dT%H%M%S")+f"-{os.getpid()}"); run_root.mkdir(parents=True); run_root.chmod(0o700)
    cfg=tomllib.loads((Path.home()/".codex/config.toml").read_text()); results=[]
    for case in selected:
        case_dir=run_root/case["id"]/"fixture"; runtime=run_root/case["id"]/"runtime"; case_dir.mkdir(parents=True,exist_ok=False)
        for name,text in FIXTURES[case["id"]].items(): (case_dir/name).write_text(text)
        immutable={name:sha256(case_dir/name) for name in FIXTURES[case["id"]] if name not in case["mutable_files"]}
        print(json.dumps({"running":case["id"],"timeout_seconds":a.timeout}),flush=True)
        result=run_case(a.codex,cfg,case,case_dir,runtime,a.timeout,out)
        result["immutable_errors"]=[name for name,digest in immutable.items() if not (case_dir/name).exists() or sha256(case_dir/name)!=digest]
        allowed=set(FIXTURES[case["id"]])|set(case["mutable_files"])|{"root-result.txt","__pycache__"}
        result["unexpected_files"]=[p.name for p in case_dir.iterdir() if p.name not in allowed]
        result["passed"] = result["passed"] and not result["immutable_errors"] and not result["unexpected_files"]
        results.append(result); report={"kind":plan["kind"],"rubric_version":"2.3","results":results,"billing_cost":None,"limits":["forced role dispatch is not autonomous selection evidence","sanitized artifacts are not product or provider evidence","no relative model quality or savings conclusion","an observable child receipt confirms acceptance before editing; it does not decrypt or prove byte-for-byte prompt delivery"]}
        rp=run_root/"results.json"; rp.write_text(json.dumps(report,indent=2)); rp.chmod(0o600)
        print(json.dumps({"case":case["id"],"passed":result["passed"],"seconds":result["seconds"],"role_errors":result["role_errors"],"dependency_errors":result["dependency_errors"],"artifact_errors":result["artifact_errors"],"immutable_errors":result["immutable_errors"],"unexpected_files":result["unexpected_files"],"results":str(rp)}),flush=True)
        if result["timed_out"]: break
    return 0 if len(results)==len(selected) and all(x["passed"] for x in results) else 1


if __name__ == "__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--grade-artifact":
        artifact_errors=grade_artifacts(sys.argv[2],Path(sys.argv[3])); print(json.dumps({"errors":artifact_errors})); raise SystemExit(0 if not artifact_errors else 1)
    if len(sys.argv)==4 and sys.argv[1]=="--grade-v12-artifact":
        all_cases=json.loads(V12_CASES_PATH.read_text()); selected=next((c for c in all_cases if c["id"]==sys.argv[2]),None)
        if selected is None: print(json.dumps({"errors":["unknown_v12_case"]})); raise SystemExit(1)
        artifact_errors=grade_v12_artifacts(selected,Path(sys.argv[3])); print(json.dumps({"errors":artifact_errors})); raise SystemExit(0 if not artifact_errors else 1)
    raise SystemExit(main())
