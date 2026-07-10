"""Schemas for advanced interview tool orchestration."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InterviewToolDefinition(BaseModel):
    """Declarative metadata for an interview analysis tool."""

    id: str
    name: str
    category: str
    purpose: str
    complexity_weight: int = Field(ge=1, le=10)
    estimated_latency_seconds: int = Field(ge=5, le=1800)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    activation_signals: List[str] = Field(default_factory=list)
    guardrails: List[str] = Field(default_factory=list)


class WorkflowStageDefinition(BaseModel):
    """Single stage in a workflow blueprint."""

    id: str
    name: str
    description: str
    tool_ids: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    failure_strategy: str = "degrade-to-partial-signal"


class WorkflowBlueprint(BaseModel):
    """High-level multi-stage workflow blueprint."""

    id: str
    name: str
    intent: str
    persona: str
    complexity_tier: str
    estimated_duration_minutes: int = Field(ge=1, le=240)
    tool_ids: List[str] = Field(default_factory=list)
    entry_conditions: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    stages: List[WorkflowStageDefinition] = Field(default_factory=list)


class OrchestrationStatusResponse(BaseModel):
    """Operational overview of the orchestration module."""

    enabled: bool
    available: bool
    total_tools: int
    total_workflows: int
    complexity_ceiling: int = Field(ge=1)
    recommended_modes: List[str] = Field(default_factory=list)


class OrchestrationPlanRequest(BaseModel):
    """Request payload for generating a personalized workflow plan."""

    resume_data: Dict[str, Any] = Field(default_factory=dict)
    workflow_ids: List[str] = Field(default_factory=list)
    target_role: Optional[str] = None
    job_description: Optional[str] = None


class PlannedWorkflowStage(BaseModel):
    """Stage plus resolved tools for a generated plan."""

    id: str
    name: str
    description: str
    depends_on: List[str] = Field(default_factory=list)
    tools: List[InterviewToolDefinition] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)


class PlannedWorkflow(BaseModel):
    """Resolved workflow with personalized stages."""

    id: str
    name: str
    intent: str
    persona: str
    complexity_tier: str
    estimated_duration_minutes: int
    tools: List[InterviewToolDefinition] = Field(default_factory=list)
    stages: List[PlannedWorkflowStage] = Field(default_factory=list)


class OrchestrationPlanResponse(BaseModel):
    """Generated interview orchestration plan."""

    success: bool = True
    target_role: str
    primary_domain: str
    experience_level: str
    recommended_tools: List[InterviewToolDefinition] = Field(default_factory=list)
    workflows: List[PlannedWorkflow] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    total_estimated_duration_minutes: int = 0
    complexity_score: int = 0
    generated_at: str
