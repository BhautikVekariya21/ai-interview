"""Advanced interview tool catalog and workflow orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Sequence

from app.schemas.orchestration_schemas import (
    InterviewToolDefinition,
    OrchestrationPlanResponse,
    OrchestrationStatusResponse,
    PlannedWorkflow,
    PlannedWorkflowStage,
    WorkflowBlueprint,
    WorkflowStageDefinition,
)


class InterviewOrchestrator:
    """Build inspectable multi-stage interview workflows."""

    def __init__(self) -> None:
        self._tools = self._build_tools()
        self._workflows = self._build_workflows()

    def list_tools(self) -> List[InterviewToolDefinition]:
        return list(self._tools.values())

    def list_workflows(self) -> List[WorkflowBlueprint]:
        return list(self._workflows.values())

    def get_status(self) -> OrchestrationStatusResponse:
        return OrchestrationStatusResponse(
            enabled=True,
            available=True,
            total_tools=len(self._tools),
            total_workflows=len(self._workflows),
            complexity_ceiling=sum(tool.complexity_weight for tool in self._tools.values()),
            recommended_modes=["targeted-screen", "deep-dive", "staff-plus-loop"],
        )

    def build_plan(
        self,
        resume_data: Dict,
        workflow_ids: Sequence[str] | None = None,
        target_role: str | None = None,
        job_description: str | None = None,
    ) -> OrchestrationPlanResponse:
        experience_level = self._normalize_text(resume_data.get("experience_level"), "junior")
        primary_domain = self._normalize_text(resume_data.get("primary_domain"), "software engineering")
        resolved_role = self._normalize_text(target_role, primary_domain)
        focus_areas = self._collect_focus_areas(resume_data, job_description)

        selected_workflows = self._resolve_workflows(
            workflow_ids=workflow_ids,
            experience_level=experience_level,
            primary_domain=primary_domain,
            focus_areas=focus_areas,
        )

        recommended_tools = self._collect_recommended_tools(selected_workflows, focus_areas, experience_level)
        planned_workflows = [
            self._materialize_workflow(workflow, focus_areas)
            for workflow in selected_workflows
        ]

        risk_flags = self._build_risk_flags(
            experience_level=experience_level,
            focus_areas=focus_areas,
            workflow_count=len(planned_workflows),
            job_description=job_description,
        )
        execution_order = [
            stage.id
            for workflow in planned_workflows
            for stage in workflow.stages
        ]
        total_duration = sum(w.estimated_duration_minutes for w in planned_workflows)
        complexity_score = sum(
            tool.complexity_weight
            for tool in recommended_tools
        ) + len(risk_flags) * 2

        return OrchestrationPlanResponse(
            target_role=resolved_role,
            primary_domain=primary_domain,
            experience_level=experience_level,
            recommended_tools=recommended_tools,
            workflows=planned_workflows,
            focus_areas=focus_areas,
            risk_flags=risk_flags,
            execution_order=execution_order,
            total_estimated_duration_minutes=total_duration,
            complexity_score=complexity_score,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _build_tools(self) -> Dict[str, InterviewToolDefinition]:
        tool_defs = [
            InterviewToolDefinition(
                id="resume-forensics",
                name="Resume Forensics",
                category="evidence",
                purpose="Break claimed achievements into verifiable technical anchors and measurable proof points.",
                complexity_weight=6,
                estimated_latency_seconds=45,
                inputs=["resume_data", "job_description"],
                outputs=["claim_map", "evidence_gaps"],
                dependencies=["parsed_resume"],
                activation_signals=["high-claim-density", "senior-scope", "leadership-language"],
                guardrails=["Do not invent projects or metrics.", "Flag unverifiable claims explicitly."],
            ),
            InterviewToolDefinition(
                id="claim-anchor-mapper",
                name="Claim Anchor Mapper",
                category="evidence",
                purpose="Maps resume claims to question prompts, follow-ups, and contradiction checks.",
                complexity_weight=5,
                estimated_latency_seconds=30,
                inputs=["resume_data"],
                outputs=["anchor_graph", "probe_targets"],
                dependencies=["resume-forensics"],
                activation_signals=["project-heavy-profile", "multi-role-history"],
                guardrails=["Prefer exact resume entities over generic topics."],
            ),
            InterviewToolDefinition(
                id="stack-depth-probe",
                name="Stack Depth Probe",
                category="technical",
                purpose="Converts listed skills into layered depth checks from fundamentals to failure modes.",
                complexity_weight=7,
                estimated_latency_seconds=60,
                inputs=["skills", "projects", "job_description"],
                outputs=["depth_questions", "topic_ladders"],
                dependencies=["claim-anchor-mapper"],
                activation_signals=["broad-skill-surface", "platform-engineering", "ml-systems"],
                guardrails=["Balance breadth and depth across no more than five core stacks."],
            ),
            InterviewToolDefinition(
                id="architecture-stressor",
                name="Architecture Stressor",
                category="systems",
                purpose="Generates scale, latency, cost, and failure-pressure scenarios around real projects.",
                complexity_weight=8,
                estimated_latency_seconds=75,
                inputs=["projects", "work_experience", "job_description"],
                outputs=["stress_scenarios", "tradeoff_prompts"],
                dependencies=["resume-forensics"],
                activation_signals=["distributed-systems", "microservices", "data-platform"],
                guardrails=["Anchor stress tests to stated scale; avoid fantasy traffic numbers."],
            ),
            InterviewToolDefinition(
                id="tradeoff-simulator",
                name="Tradeoff Simulator",
                category="systems",
                purpose="Forces explicit prioritization between speed, reliability, team cost, and product outcomes.",
                complexity_weight=7,
                estimated_latency_seconds=50,
                inputs=["projects", "job_description"],
                outputs=["tradeoff_branches", "decision_audits"],
                dependencies=["architecture-stressor"],
                activation_signals=["senior", "staff", "cross-functional-role"],
                guardrails=["Every tradeoff branch must surface a sacrificed dimension."],
            ),
            InterviewToolDefinition(
                id="incident-rewind",
                name="Incident Rewind",
                category="operations",
                purpose="Replays outage or degradation narratives to inspect debugging sequence and operational judgment.",
                complexity_weight=8,
                estimated_latency_seconds=70,
                inputs=["work_experience", "projects"],
                outputs=["incident_timelines", "diagnostic_prompts"],
                dependencies=["architecture-stressor"],
                activation_signals=["devops", "sre", "backend", "platform"],
                guardrails=["Prompt for timeline, blast radius, rollback, and learning loops."],
            ),
            InterviewToolDefinition(
                id="behavioral-contradiction-check",
                name="Behavioral Contradiction Check",
                category="behavioral",
                purpose="Cross-checks leadership and collaboration claims against concrete examples and tradeoffs.",
                complexity_weight=6,
                estimated_latency_seconds=40,
                inputs=["work_experience", "achievements"],
                outputs=["behavioral_probes", "consistency_flags"],
                dependencies=["claim-anchor-mapper"],
                activation_signals=["leadership-language", "team-impact", "mentorship"],
                guardrails=["Probe for actions and outcomes, not personality labels."],
            ),
            InterviewToolDefinition(
                id="communication-pressure-loop",
                name="Communication Pressure Loop",
                category="communication",
                purpose="Tests how clearly the candidate can compress complexity for different audiences under time pressure.",
                complexity_weight=5,
                estimated_latency_seconds=35,
                inputs=["projects", "job_description"],
                outputs=["audience_shifts", "clarity_probes"],
                dependencies=["tradeoff-simulator"],
                activation_signals=["senior", "stakeholder-facing", "product-collaboration"],
                guardrails=["Use audience changes that reflect the target role."],
            ),
            InterviewToolDefinition(
                id="leadership-signal-amplifier",
                name="Leadership Signal Amplifier",
                category="leadership",
                purpose="Escalates from individual contribution into org-level influence, delegation, and strategy prompts.",
                complexity_weight=8,
                estimated_latency_seconds=65,
                inputs=["work_experience", "achievements", "job_description"],
                outputs=["leadership_threads", "scope-tests"],
                dependencies=["behavioral-contradiction-check"],
                activation_signals=["staff", "principal", "manager", "director"],
                guardrails=["Do not infer people management if the resume does not support it."],
            ),
            InterviewToolDefinition(
                id="cross-functional-translation",
                name="Cross Functional Translation",
                category="leadership",
                purpose="Builds scenarios that require aligning engineering decisions with product, design, finance, or compliance.",
                complexity_weight=7,
                estimated_latency_seconds=55,
                inputs=["projects", "job_description"],
                outputs=["stakeholder_scenarios", "alignment_checks"],
                dependencies=["communication-pressure-loop"],
                activation_signals=["platform", "payments", "healthcare", "enterprise"],
                guardrails=["Ground scenarios in the domain and regulated constraints when relevant."],
            ),
        ]
        return {tool.id: tool for tool in tool_defs}

    def _build_workflows(self) -> Dict[str, WorkflowBlueprint]:
        workflows = [
            WorkflowBlueprint(
                id="deep-signal-screen",
                name="Deep Signal Screen",
                intent="Turn resume claims into layered evidence-backed technical probes.",
                persona="senior-ic",
                complexity_tier="advanced",
                estimated_duration_minutes=32,
                tool_ids=["resume-forensics", "claim-anchor-mapper", "stack-depth-probe"],
                entry_conditions=["Resume includes named stacks, projects, or measurable impact."],
                success_metrics=["At least three anchored questions per top skill cluster.", "Every major claim has one verification path."],
                stages=[
                    WorkflowStageDefinition(
                        id="deep-signal-screen.claim-decomposition",
                        name="Claim Decomposition",
                        description="Extract high-signal claims and convert them into proof obligations.",
                        tool_ids=["resume-forensics", "claim-anchor-mapper"],
                        outputs=["claim_map", "anchor_graph"],
                    ),
                    WorkflowStageDefinition(
                        id="deep-signal-screen.depth-threads",
                        name="Depth Threads",
                        description="Create technical depth ladders per focus area.",
                        tool_ids=["stack-depth-probe"],
                        depends_on=["deep-signal-screen.claim-decomposition"],
                        outputs=["depth_questions", "topic_ladders"],
                    ),
                ],
            ),
            WorkflowBlueprint(
                id="failure-cascade-drill",
                name="Failure Cascade Drill",
                intent="Stress the candidate's architecture and incident handling under realistic degradation paths.",
                persona="systems-engineer",
                complexity_tier="expert",
                estimated_duration_minutes=41,
                tool_ids=["architecture-stressor", "tradeoff-simulator", "incident-rewind"],
                entry_conditions=["Resume references distributed systems, production traffic, or reliability work."],
                success_metrics=["Candidate can articulate blast radius, rollback, and recovery sequencing.", "Tradeoffs stay consistent under pressure."],
                stages=[
                    WorkflowStageDefinition(
                        id="failure-cascade-drill.system-pressure",
                        name="System Pressure Setup",
                        description="Build domain-specific scale and failure constraints.",
                        tool_ids=["architecture-stressor"],
                        outputs=["stress_scenarios"],
                    ),
                    WorkflowStageDefinition(
                        id="failure-cascade-drill.decision-collapse",
                        name="Decision Collapse",
                        description="Change constraints midstream and inspect tradeoff reasoning.",
                        tool_ids=["tradeoff-simulator"],
                        depends_on=["failure-cascade-drill.system-pressure"],
                        outputs=["tradeoff_branches", "decision_audits"],
                    ),
                    WorkflowStageDefinition(
                        id="failure-cascade-drill.incident-rewind",
                        name="Incident Rewind",
                        description="Replay the operational response with emphasis on diagnosis and communication.",
                        tool_ids=["incident-rewind"],
                        depends_on=["failure-cascade-drill.decision-collapse"],
                        outputs=["incident_timelines", "diagnostic_prompts"],
                    ),
                ],
            ),
            WorkflowBlueprint(
                id="stakeholder-pressure-lab",
                name="Stakeholder Pressure Lab",
                intent="Inspect communication clarity and cross-functional judgment while constraints keep shifting.",
                persona="senior-collaborator",
                complexity_tier="advanced",
                estimated_duration_minutes=29,
                tool_ids=[
                    "behavioral-contradiction-check",
                    "communication-pressure-loop",
                    "cross-functional-translation",
                ],
                entry_conditions=["Target role requires product, stakeholder, or cross-team alignment."],
                success_metrics=["Candidate can reframe the same problem for multiple audiences.", "Behavioral claims remain concrete under pressure."],
                stages=[
                    WorkflowStageDefinition(
                        id="stakeholder-pressure-lab.consistency-check",
                        name="Consistency Check",
                        description="Verify collaboration and ownership claims with concrete evidence.",
                        tool_ids=["behavioral-contradiction-check"],
                        outputs=["behavioral_probes", "consistency_flags"],
                    ),
                    WorkflowStageDefinition(
                        id="stakeholder-pressure-lab.audience-switch",
                        name="Audience Switch",
                        description="Force the explanation to change shape for engineers, PMs, and executives.",
                        tool_ids=["communication-pressure-loop", "cross-functional-translation"],
                        depends_on=["stakeholder-pressure-lab.consistency-check"],
                        outputs=["audience_shifts", "stakeholder_scenarios"],
                    ),
                ],
            ),
            WorkflowBlueprint(
                id="executive-calibration-matrix",
                name="Executive Calibration Matrix",
                intent="Push beyond implementation into strategy, delegation, portfolio tradeoffs, and org-level leverage.",
                persona="staff-plus",
                complexity_tier="staff-plus",
                estimated_duration_minutes=37,
                tool_ids=[
                    "leadership-signal-amplifier",
                    "tradeoff-simulator",
                    "cross-functional-translation",
                ],
                entry_conditions=["Resume suggests staff, principal, manager, lead, or executive scope."],
                success_metrics=["Candidate distinguishes team-level from org-level leverage.", "Strategy answers include sequencing and risk management."],
                stages=[
                    WorkflowStageDefinition(
                        id="executive-calibration-matrix.scope-expansion",
                        name="Scope Expansion",
                        description="Expand from direct execution into systems of teams, constraints, and delegation.",
                        tool_ids=["leadership-signal-amplifier"],
                        outputs=["leadership_threads", "scope-tests"],
                    ),
                    WorkflowStageDefinition(
                        id="executive-calibration-matrix.strategy-fork",
                        name="Strategy Fork",
                        description="Introduce conflicting business goals and require explicit prioritization.",
                        tool_ids=["tradeoff-simulator", "cross-functional-translation"],
                        depends_on=["executive-calibration-matrix.scope-expansion"],
                        outputs=["decision_audits", "alignment_checks"],
                    ),
                ],
            ),
        ]
        return {workflow.id: workflow for workflow in workflows}

    def _resolve_workflows(
        self,
        workflow_ids: Sequence[str] | None,
        experience_level: str,
        primary_domain: str,
        focus_areas: Sequence[str],
    ) -> List[WorkflowBlueprint]:
        if workflow_ids:
            selected = [
                self._workflows[workflow_id]
                for workflow_id in workflow_ids
                if workflow_id in self._workflows
            ]
            if selected:
                return selected

        selected_ids = ["deep-signal-screen"]
        if any(term in primary_domain for term in ("backend", "platform", "data", "infrastructure", "distributed", "machine learning")):
            selected_ids.append("failure-cascade-drill")
        if any(term in " ".join(focus_areas) for term in ("leadership", "product", "stakeholder", "compliance", "payments")):
            selected_ids.append("stakeholder-pressure-lab")
        if any(level in experience_level for level in ("senior", "lead", "executive", "principal", "staff", "manager")):
            selected_ids.append("executive-calibration-matrix")
        elif "mid" in experience_level:
            selected_ids.append("stakeholder-pressure-lab")

        deduped_ids = list(dict.fromkeys(selected_ids))
        return [self._workflows[workflow_id] for workflow_id in deduped_ids]

    def _collect_focus_areas(self, resume_data: Dict, job_description: str | None) -> List[str]:
        focus = []

        def push(value: str) -> None:
            cleaned = value.strip()
            if cleaned and cleaned.lower() not in {item.lower() for item in focus}:
                focus.append(cleaned)

        for skill in (resume_data.get("top_skills") or [])[:6]:
            push(str(skill))

        for project in (resume_data.get("projects") or [])[:3]:
            if isinstance(project, dict):
                push(str(project.get("title") or ""))
                for tech in (project.get("technologies") or [])[:2]:
                    push(str(tech))

        domain = self._normalize_text(resume_data.get("primary_domain"), "")
        if domain:
            push(domain)

        work_items = resume_data.get("work_experience") or []
        if work_items:
            first_role = work_items[0]
            if isinstance(first_role, dict):
                push(str(first_role.get("role") or ""))
                push(str(first_role.get("company") or ""))

        if job_description:
            for marker in ("payments", "compliance", "stakeholder", "architecture", "roadmap", "incident"):
                if marker in job_description.lower():
                    push(marker)

        return focus[:10] or ["general engineering judgment"]

    def _collect_recommended_tools(
        self,
        workflows: Iterable[WorkflowBlueprint],
        focus_areas: Sequence[str],
        experience_level: str,
    ) -> List[InterviewToolDefinition]:
        tool_ids = []
        for workflow in workflows:
            tool_ids.extend(workflow.tool_ids)

        if any(term in " ".join(focus_areas).lower() for term in ("kafka", "kubernetes", "incident", "latency")):
            tool_ids.append("incident-rewind")
        if any(level in experience_level for level in ("lead", "senior", "staff", "principal", "manager", "executive")):
            tool_ids.append("communication-pressure-loop")

        ordered = []
        seen = set()
        for tool_id in tool_ids:
            if tool_id in self._tools and tool_id not in seen:
                ordered.append(self._tools[tool_id])
                seen.add(tool_id)
        return ordered

    def _materialize_workflow(
        self,
        workflow: WorkflowBlueprint,
        focus_areas: Sequence[str],
    ) -> PlannedWorkflow:
        tools = [self._tools[tool_id] for tool_id in workflow.tool_ids if tool_id in self._tools]
        stages = []
        for stage in workflow.stages:
            stage_tools = [self._tools[tool_id] for tool_id in stage.tool_ids if tool_id in self._tools]
            stages.append(
                PlannedWorkflowStage(
                    id=stage.id,
                    name=stage.name,
                    description=stage.description,
                    depends_on=stage.depends_on,
                    tools=stage_tools,
                    outputs=stage.outputs,
                    focus_areas=list(focus_areas[:4]),
                )
            )
        return PlannedWorkflow(
            id=workflow.id,
            name=workflow.name,
            intent=workflow.intent,
            persona=workflow.persona,
            complexity_tier=workflow.complexity_tier,
            estimated_duration_minutes=workflow.estimated_duration_minutes,
            tools=tools,
            stages=stages,
        )

    def _build_risk_flags(
        self,
        experience_level: str,
        focus_areas: Sequence[str],
        workflow_count: int,
        job_description: str | None,
    ) -> List[str]:
        flags = []
        joined_focus = " ".join(focus_areas).lower()
        if workflow_count >= 3:
            flags.append("High cognitive load: schedule deliberate interviewer transitions between workflow families.")
        if any(level in experience_level for level in ("staff", "principal", "executive", "lead")):
            flags.append("Staff-plus calibration active: weak strategy answers will surface faster than implementation gaps.")
        if any(term in joined_focus for term in ("payments", "compliance", "security")):
            flags.append("Domain-sensitive scenarios enabled: answers should address risk, auditability, or blast radius.")
        if job_description and len(job_description.split()) > 120:
            flags.append("Job description is dense: prioritize the highest-signal requirements before adding exploratory branches.")
        return flags

    @staticmethod
    def _normalize_text(value: object, default: str) -> str:
        if value is None:
            return default
        if hasattr(value, "value"):
            value = getattr(value, "value")
        text = str(value).strip()
        return text or default


_orchestrator_instance: InterviewOrchestrator | None = None


def get_interview_orchestrator() -> InterviewOrchestrator:
    """Singleton orchestration registry."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InterviewOrchestrator()
    return _orchestrator_instance
