from __future__ import annotations

from pathlib import Path
import re
import unittest


CODEX = Path.home() / ".codex"
DAUTIA = CODEX / "skills" / "dautia-project-cycle"
DOCS = CODEX / "skills" / "govern-project-documentation"
RYVEN = CODEX / "skills" / "ryven-release-closeout"
UI_UX = CODEX / "skills" / "ui-ux-designer"
FRONTEND = CODEX / "skills" / "frontend-developer"
CAPABILITY_GUIDE = CODEX / "guides" / "guia_invocacion_capacidades_codex.md"
TASK_DECOMPOSITION = CODEX / "skills" / "task-decomposition-expert"
SWIFTUI = CODEX / "skills" / "swiftui-pro"
CANVAS = CODEX / "skills" / "canvas-design"
SURFACE_VALUE = CODEX / "skills" / "user-surface-value-review"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class WorkflowContractTests(unittest.TestCase):
    def test_skills_are_load_once_complements(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        dautia = text(DAUTIA / "SKILL.md")
        self.assertIn("Una skill se lee completa una vez por objetivo", agents)
        self.assertIn("Load this file once per material objective", dautia)
        self.assertIn("zero delegation is healthy", dautia)
        self.assertIn("Telemetry is diagnostic, never a task stage or completion gate", dautia)
        self.assertIn("`computer-use`, solo si", agents)
        self.assertIn("skill especializada sin GUI", agents)

    def test_four_modes_and_integration_closeout_are_explicit(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        dautia = text(DAUTIA / "SKILL.md")
        for label in ("Descubrimiento", "Auditoria", "Implementacion", "Release"):
            self.assertIn(label, agents)
        for label in ("DISCOVERY", "AUDIT", "IMPLEMENTATION", "RELEASE"):
            self.assertIn(label, dautia)
        self.assertIn("authorizes that integration closeout", dautia)
        self.assertIn("No declarar cierre si el cambio solo quedo en una rama efimera", agents)

    def test_colima_is_forbidden_and_db_tests_use_staging(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        dautia = text(DAUTIA / "SKILL.md")
        cleanup = text(CODEX / "skills" / "macos-disk-cleanup" / "SKILL.md")
        self.assertIn("Colima se trata como no disponible", agents)
        self.assertIn("Toda prueba ejecutada localmente que necesite base de datos usa la DB de `staging`", agents)
        self.assertIn("Treat Colima as unavailable", dautia)
        self.assertIn("verified staging database", dautia)
        self.assertIn("must never be installed, started, restarted, configured, or used", cleanup)
        self.assertNotIn("Prefer stopping temporary stacks and Colima", cleanup)

    def test_documentation_skill_has_a_narrow_trigger(self) -> None:
        docs = text(DOCS / "SKILL.md")
        self.assertIn("not for ordinary project-doc reading", docs)
        self.assertIn("Use the smallest mode", docs)
        self.assertNotIn("Run the bundled audit first", docs)
        self.assertNotIn("rerun `scripts/audit_workspace.sh`", docs)

    def test_ryven_skill_is_release_only(self) -> None:
        ryven = text(RYVEN / "SKILL.md")
        self.assertIn("Use only for an explicit release closeout", ryven)
        self.assertIn("not for routine docs", ryven)
        self.assertIn("This is a release-boundary skill", ryven)

    def test_dautia_skills_and_reasoning_profiles_are_explicit(self) -> None:
        config = text(CODEX / "config.toml")
        root_model = re.search(r'^model = "([^"]+)"$', config, re.MULTILINE)
        self.assertIsNotNone(root_model)
        self.assertEqual(root_model.group(1), "gpt-5.6-sol")
        root_effort = re.search(r'^model_reasoning_effort = "(\w+)"$', config, re.MULTILINE)
        self.assertIsNotNone(root_effort)
        self.assertEqual(root_effort.group(1), "high")
        self.assertNotIn("[features.multi_agent_v2]", config)
        enabled = re.search(
            r'\[\[skills\.config\]\]\s+path = "[^"]*/\.codex/skills/dautia-project-cycle/SKILL\.md"\s+enabled = (\w+)',
            config,
        )
        self.assertIsNotNone(enabled)
        self.assertEqual(enabled.group(1), "true")
        delivery_enabled = re.search(
            r'\[\[skills\.config\]\]\s+path = "[^"]*/\.codex/skills/dautia-ci-cd/SKILL\.md"\s+enabled = (\w+)',
            config,
        )
        self.assertIsNotNone(delivery_enabled)
        self.assertEqual(delivery_enabled.group(1), "true")
        self.assertIn("max_concurrent_threads_per_session = 4", config)
        self.assertIn("max_depth = 1", config)
        self.assertNotIn("\nmax_threads =", config)
        expected_profiles = {
            "code_explorer": ("gpt-5.6-terra", "high"),
            "data_security": ("gpt-5.6-sol", "high"),
            "decision_gate": ("gpt-5.6-sol", "xhigh"),
            "documental": ("gpt-5.6-terra", "medium"),
            "implementer": ("gpt-5.6-terra", "medium"),
            "implementer_complex": ("gpt-5.6-sol", "high"),
            "independent_reviewer": ("gpt-5.6-sol", "high"),
            "product_discovery": ("gpt-5.6-sol", "high"),
            "qa_android": ("gpt-5.6-sol", "high"),
            "qa_e2e": ("gpt-5.6-sol", "high"),
            "qa_ios": ("gpt-5.6-sol", "high"),
            "qa_web": ("gpt-5.6-sol", "high"),
            "release_operator": ("gpt-5.6-sol", "high"),
            "ux_auditor": ("gpt-5.6-sol", "high"),
        }
        configured_profiles = {}
        for path in (CODEX / "agents").glob("*.toml"):
            profile = text(path)
            model = re.search(r'^model = "([^"]+)"$', profile, re.MULTILINE)
            effort = re.search(r'^model_reasoning_effort = "(\w+)"$', profile, re.MULTILINE)
            self.assertIsNotNone(model, path)
            self.assertIsNotNone(effort, path)
            configured_profiles[path.stem] = (model.group(1), effort.group(1))
        self.assertEqual(configured_profiles, expected_profiles)
        self.assertNotIn("gpt-5.6-luna", {model for model, _ in configured_profiles.values()})

        documental = text(CODEX / "agents" / "documental.toml")
        self.assertNotIn("before planning and at closeout", documental)

    def test_root_effort_is_not_conflated_with_bounded_roles(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        packaging = text(CODEX / "skills" / "codex-workflow-packaging-review" / "SKILL.md")
        self.assertIn("El perfil del host asigna modelos a roles", agents)
        self.assertIn("Este contrato rige igual en Codex y Cursor", agents)
        self.assertIn("Plugins externos son complementos", agents)
        self.assertIn("iguala aceptacion", agents)
        self.assertIn("reduce costo total", agents)
        self.assertIn("si falla, Sol", agents)
        self.assertIn("no conteos", agents)
        self.assertIn("Do not infer that the root orchestrator should be downgraded", packaging)
        self.assertIn("Use `medium` as the balanced baseline for bounded deterministic implementers", packaging)

    def test_product_ui_audit_routes_without_governance_detour(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        dautia = text(DAUTIA / "SKILL.md")
        docs = text(DOCS / "SKILL.md")
        packaging = text(CODEX / "skills" / "codex-workflow-packaging-review" / "SKILL.md")
        ui_ux = text(UI_UX / "SKILL.md")
        self.assertIn("Product and UI/UX audits route first", dautia)
        self.assertIn("never activate it alone", dautia)
        self.assertIn("product/UI audits that merely notice drift", docs)
        self.assertIn("Entregar As-Is, delta, To-Be, aceptacion y plan", agents)
        self.assertIn("El destino de Implementacion es la rama `integration_branch`", agents)
        self.assertIn("general computer-use, only when", dautia)
        self.assertIn("false-positive routing as a regression", packaging)
        self.assertIn("**AUDIT:**", ui_ux)
        self.assertIn("**CHANGE:**", ui_ux)
        self.assertIn("without implying authorization", ui_ux)

    def test_user_facing_quality_is_contextual_not_component_minimalism(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        dautia = text(DAUTIA / "SKILL.md")
        ui_ux = text(UI_UX / "SKILL.md")
        frontend = text(FRONTEND / "SKILL.md")
        surface_value = text(SURFACE_VALUE / "SKILL.md")

        self.assertIn("cada dato, copy, KPI, badge, tabla, icono o ayuda", agents)
        self.assertIn("role, task and domain", dautia)
        self.assertIn("Contextual value over visual minimalism", ui_ux)
        self.assertIn("A KPI belongs when it answers a business question", frontend)
        self.assertIn("apply `user-surface-value-review` inside validation", dautia)
        self.assertIn("Return `NOT_APPLICABLE` immediately", surface_value)
        self.assertIn("This verdict is advisory. It blocks nothing by itself", surface_value)
        self.assertIn("Judge by context, not component count", surface_value)
        self.assertFalse((CODEX / "skills" / "dautia-design-monster").exists())

    def test_retired_or_disabled_capabilities_do_not_compete_for_routing(self) -> None:
        retired = {
            "browser-harness",
            "codex-primary-runtime",
            "dautia-design-monster",
            "ios-app-intents",
            "ios-debugger-agent",
            "ios-ettrace-performance",
            "ios-memgraph-leaks",
            "react-best-practices",
            "spec-kit",
            "speckit-analyze",
            "speckit-checklist",
            "speckit-clarify",
            "speckit-constitution",
            "speckit-implement",
            "speckit-plan",
            "speckit-specify",
            "speckit-tasks",
            "speckit-taskstoissues",
            "swiftui-liquid-glass",
            "swiftui-performance-audit",
            "swiftui-ui-patterns",
            "swiftui-view-refactor",
        }
        skills_root = CODEX / "skills"
        for name in retired:
            with self.subTest(name=name):
                self.assertFalse((skills_root / name).exists())

        guide = text(CAPABILITY_GUIDE)
        self.assertIn("La lista de capacidades disponible en la sesion es la fuente de verdad", guide)
        self.assertNotIn("Build iOS Apps", guide)
        self.assertNotIn("dautia-design-monster", guide)
        self.assertNotIn("spec-kit", guide)

        task_decomposition = text(TASK_DECOMPOSITION / "SKILL.md")
        swiftui = text(SWIFTUI / "SKILL.md")
        canvas = text(CANVAS / "SKILL.md")
        self.assertIn("Use only when direct implementation would be ambiguous or risky", task_decomposition)
        self.assertIn("Do not invoke another skill merely to complete the plan", task_decomposition)
        self.assertIn("Do not search for or invoke another skill", swiftui)
        self.assertIn("Do not turn that direction into a separate deliverable", canvas)
        for contract in (task_decomposition, swiftui, canvas):
            self.assertNotIn("dautia-design-monster", contract)
            self.assertNotIn("frontend-skill", contract)
            self.assertNotIn("build-ios-apps:", contract)

    def test_visible_plans_keep_outcomes_and_hide_meta_ceremony(self) -> None:
        dautia = text(DAUTIA / "SKILL.md")
        self.assertIn("Use a visible plan only for three or more meaningful phases", dautia)
        self.assertIn("skill loading, memory review, instruction reading", dautia)

    def test_recent_friction_correctives_are_contractual(self) -> None:
        agents = text(CODEX / "AGENTS.md")
        dautia = text(DAUTIA / "SKILL.md")
        release = text(CODEX / "agents" / "release_operator.toml")
        agents_flat = " ".join(agents.split())
        dautia_flat = " ".join(dautia.split())
        release_flat = " ".join(release.split())
        self.assertIn("no obliga a consultar changelogs", agents_flat)
        self.assertIn("origin/<integration_branch>", agents_flat)
        self.assertIn("Dependency-only upgrades default", dautia_flat)
        self.assertIn("extra browsers/viewports", dautia_flat)
        self.assertIn("source revision, target, provider", release_flat)
        self.assertIn("nunca crea otro `release_operator`", agents_flat.lower())
        self.assertIn("stale_contract", agents_flat)
        self.assertIn("delegar por oleadas", agents_flat)
        self.assertIn("pruebas verdes no prueban aceptacion visual", agents_flat)
        self.assertIn("muestra representativa o contact sheet", agents_flat)
        self.assertIn("must never delegate to another release operator", dautia_flat)
        self.assertIn("delegate in waves", dautia_flat)
        self.assertIn("green technical tests do not prove visual acceptance", dautia_flat)
        self.assertIn("Never spawn agents", release_flat)
        self.assertIn("10.000 caracteres", agents_flat)

    def test_primary_process_contracts_stay_compact(self) -> None:
        paths = [
            CODEX / "AGENTS.md",
            DAUTIA / "SKILL.md",
            DOCS / "SKILL.md",
            RYVEN / "SKILL.md",
            CAPABILITY_GUIDE,
        ]
        budgets = {
            CODEX / "AGENTS.md": 1800,
            DAUTIA / "SKILL.md": 1200,
            DOCS / "SKILL.md": 1200,
            RYVEN / "SKILL.md": 600,
            CAPABILITY_GUIDE: 900,
        }
        for path in paths:
            with self.subTest(path=path):
                self.assertLessEqual(len(text(path).split()), budgets[path])

    def test_observability_labels_proxies_and_separates_waits(self) -> None:
        observability = text(DAUTIA / "references" / "observability.md")
        telemetry = text(DAUTIA / "scripts" / "dautia_cycle_telemetry.py")
        self.assertIn("separates task starts from completions", observability)
        self.assertIn("objective-level skill load", observability)
        self.assertIn(
            "Task-name and `(agent_type, task_name)` fingerprints are privacy-safe duplicate proxies",
            observability,
        )
        self.assertIn('"agent_waits"', telemetry)
        self.assertIn('"execution_waits"', telemetry)
        self.assertIn('"skill_objective_loads"', telemetry)
        self.assertIn('"skill_reload_turns"', telemetry)
        self.assertIn('"repository_closeouts"', telemetry)
        self.assertIn('"duplicate_delegation_fingerprints"', telemetry)
        self.assertIn('"unchanged_wait_results"', telemetry)
        self.assertIn("xhigh_without_evaluation_evidence", telemetry)
        self.assertIn("unbounded_token_totals_suppressed", telemetry)
        self.assertIn('"nested_release_operator_sessions"', telemetry)
        self.assertIn('"tool_output_chars"', telemetry)
        self.assertIn('"large_visual_tool_outputs"', telemetry)
        self.assertIn("large_text_tool_output_in_context", telemetry)
        self.assertIn("stale_workflow_contract", telemetry)

    def test_every_runtime_script_is_documented(self) -> None:
        contract = text(DAUTIA / "SKILL.md") + text(DAUTIA / "references" / "observability.md")
        scripts = sorted((DAUTIA / "scripts").glob("*.py"))
        self.assertTrue(scripts)
        for script in scripts:
            with self.subTest(script=script.name):
                self.assertIn(f"scripts/{script.name}", contract)


if __name__ == "__main__":
    unittest.main()
