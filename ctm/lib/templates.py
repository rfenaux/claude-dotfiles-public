"""
Task Templates Module (CTM v3.0 - Phase 6)

Provides YAML-based task templates for spawning pre-configured tasks
with phases, dependencies, and default settings.
"""

import os
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import get_ctm_dir


TEMPLATES_DIR = "templates"


@dataclass
class TemplatePhase:
    """A phase within a template."""
    id: str
    title: str
    steps: List[str] = field(default_factory=list)
    progress_weight: int = 20
    blocked_by: List[str] = field(default_factory=list)


@dataclass
class TemplateDefaults:
    """Default values for tasks spawned from template."""
    priority_value: float = 0.5
    priority_urgency: float = 0.5
    key_files: List[str] = field(default_factory=list)


@dataclass
class Template:
    """A task template definition."""
    name: str
    description: str = ""
    defaults: TemplateDefaults = field(default_factory=TemplateDefaults)
    phases: List[TemplatePhase] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        """Parse template from dictionary (loaded from YAML)."""
        defaults_data = data.get("defaults", {})
        defaults = TemplateDefaults(
            priority_value=defaults_data.get("priority", {}).get("value", 0.5),
            priority_urgency=defaults_data.get("priority", {}).get("urgency", 0.5),
            key_files=defaults_data.get("key_files", [])
        )

        phases = []
        for phase_data in data.get("phases", []):
            phase = TemplatePhase(
                id=phase_data.get("id", ""),
                title=phase_data.get("title", ""),
                steps=phase_data.get("steps", []),
                progress_weight=phase_data.get("progress_weight", 20),
                blocked_by=phase_data.get("blocked_by", [])
            )
            phases.append(phase)

        return cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            defaults=defaults,
            phases=phases,
            tags=data.get("tags", [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for YAML export."""
        return {
            "name": self.name,
            "description": self.description,
            "defaults": {
                "priority": {
                    "value": self.defaults.priority_value,
                    "urgency": self.defaults.priority_urgency
                },
                "key_files": self.defaults.key_files
            },
            "phases": [
                {
                    "id": p.id,
                    "title": p.title,
                    "steps": p.steps,
                    "progress_weight": p.progress_weight,
                    "blocked_by": p.blocked_by
                }
                for p in self.phases
            ],
            "tags": self.tags
        }


def get_templates_dir() -> Path:
    """Get the templates directory, creating if needed."""
    ctm_dir = get_ctm_dir()
    templates_dir = ctm_dir / TEMPLATES_DIR
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir


def list_templates() -> List[str]:
    """List available template names."""
    templates_dir = get_templates_dir()
    templates = []

    for path in templates_dir.glob("*.yaml"):
        templates.append(path.stem)
    for path in templates_dir.glob("*.yml"):
        templates.append(path.stem)

    return sorted(set(templates))


def load_template(name: str) -> Optional[Template]:
    """Load a template by name."""
    templates_dir = get_templates_dir()

    # Try .yaml first, then .yml
    for ext in [".yaml", ".yml"]:
        path = templates_dir / f"{name}{ext}"
        if path.exists():
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                    return Template.from_dict(data)
            except Exception:
                return None

    return None


def save_template(template: Template, name: Optional[str] = None) -> Path:
    """Save a template to disk."""
    templates_dir = get_templates_dir()
    filename = name or template.name.lower().replace(" ", "-")
    path = templates_dir / f"{filename}.yaml"

    with open(path, 'w') as f:
        yaml.dump(template.to_dict(), f, default_flow_style=False, sort_keys=False)

    return path


def validate_template(template: Template) -> List[str]:
    """Validate a template, returning list of errors."""
    errors = []

    if not template.name:
        errors.append("Template must have a name")

    # Check phase IDs are unique
    phase_ids = [p.id for p in template.phases]
    if len(phase_ids) != len(set(phase_ids)):
        errors.append("Phase IDs must be unique")

    # Check blocked_by references exist
    for phase in template.phases:
        for dep in phase.blocked_by:
            if dep not in phase_ids:
                errors.append(f"Phase '{phase.id}' references unknown dependency '{dep}'")

    # Check progress weights sum to ~100
    total_weight = sum(p.progress_weight for p in template.phases)
    if template.phases and (total_weight < 90 or total_weight > 110):
        errors.append(f"Progress weights sum to {total_weight}, should be ~100")

    return errors


def get_template_info(name: str) -> Optional[Dict[str, Any]]:
    """Get summary info about a template."""
    template = load_template(name)
    if not template:
        return None

    return {
        "name": template.name,
        "description": template.description,
        "phases": len(template.phases),
        "total_steps": sum(len(p.steps) for p in template.phases),
        "tags": template.tags
    }


def create_template_from_agent(agent: "Agent", name: str) -> Template:
    """Create a template from an existing agent."""
    # Extract phases from agent context if structured
    phases = []
    context = agent.context or {}

    # Check if agent has phase structure
    agent_phases = context.get("phases", [])
    if agent_phases:
        for i, phase_data in enumerate(agent_phases):
            if isinstance(phase_data, dict):
                phase = TemplatePhase(
                    id=phase_data.get("id", f"phase_{i+1}"),
                    title=phase_data.get("title", f"Phase {i+1}"),
                    steps=phase_data.get("steps", []),
                    progress_weight=phase_data.get("progress_weight", 20),
                    blocked_by=phase_data.get("blocked_by", [])
                )
                phases.append(phase)

    # If no phases, create single phase from current step
    if not phases:
        current_step = agent.state.get("current_step", "")
        phases = [TemplatePhase(
            id="main",
            title="Main Work",
            steps=[current_step] if current_step else [],
            progress_weight=100
        )]

    # Build template
    template = Template(
        name=name,
        description=f"Template created from [{agent.id}] {agent.task.get('title', '')}",
        defaults=TemplateDefaults(
            priority_value=agent.priority.get("value", 0.5),
            priority_urgency=agent.priority.get("urgency", 0.5),
            key_files=context.get("key_files", [])
        ),
        phases=phases,
        tags=context.get("tags", [])
    )

    return template


def apply_template_to_agent(agent: "Agent", template: Template) -> None:
    """Apply template defaults and structure to an agent."""
    # Set priority defaults
    agent.priority["value"] = template.defaults.priority_value
    agent.priority["urgency"] = template.defaults.priority_urgency

    # Initialize context if needed
    if not agent.context:
        agent.context = {}

    # Set key files
    if template.defaults.key_files:
        agent.context["key_files"] = template.defaults.key_files

    # Set tags
    if template.tags:
        agent.context["tags"] = template.tags

    # Store phase structure
    agent.context["phases"] = [
        {
            "id": p.id,
            "title": p.title,
            "steps": p.steps,
            "progress_weight": p.progress_weight,
            "blocked_by": p.blocked_by,
            "status": "pending",
            "completed_steps": []
        }
        for p in template.phases
    ]

    # Set template reference
    agent.context["template"] = template.name

    # Set first phase as current if phases exist
    if template.phases:
        first_phase = template.phases[0]
        agent.state["current_phase"] = first_phase.id
        if first_phase.steps:
            agent.state["current_step"] = first_phase.steps[0]
