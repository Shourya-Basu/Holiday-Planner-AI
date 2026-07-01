# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any
import re
import json
import datetime
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk import Event
from google.adk.workflow import Workflow, FunctionNode, START
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context

from app.config import config

# -----------------------------------------------------------------------------
# Initialize Model
# -----------------------------------------------------------------------------
model_instance = Gemini(model=config.model)

# -----------------------------------------------------------------------------
# Initialize MCP Toolset
# -----------------------------------------------------------------------------
from mcp import StdioServerParameters

travel_mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "app.mcp_server"],
        )
    )
)

# -----------------------------------------------------------------------------
# Specialized Sub-Agents
# -----------------------------------------------------------------------------
itinerary_agent = Agent(
    name="itinerary_agent",
    model=model_instance,
    instruction=(
        "You are a specialized travel itinerary planner. Your goal is to design a detailed, "
        "day-by-day travel itinerary based on the user's travel preferences. "
        "Use the weather, attractions, and packing checklist tools to personalize the plan. "
        "Analyze their interests (e.g., adventure, culture, food, shopping), travel dates, "
        "duration, and any special requirements (e.g., kids, seniors, accessibility). "
        "Suggest specific activities, sights, and dining options for each day. "
        "If there is previous feedback from the user, revise the itinerary to address their concerns."
    ),
    tools=[travel_mcp_toolset]
)

budget_agent = Agent(
    name="budget_agent",
    model=model_instance,
    instruction=(
        "You are a specialized travel budget estimator. Your goal is to calculate a detailed "
        "budget breakdown (covering transport, accommodation, food, activities, and emergency/miscellaneous) "
        "based on the user's budget, destination, travel dates, and group size. "
        "Use the currency conversion tool to provide accurate currency details. "
        "Provide realistic cost estimates, budget optimization tips, and recommendations to get the best value."
    ),
    tools=[travel_mcp_toolset]
)

# -----------------------------------------------------------------------------
# Orchestrator Agent
# -----------------------------------------------------------------------------
orchestrator_agent = Agent(
    name="orchestrator_agent",
    model=model_instance,
    instruction=(
        "You are the Holiday Planner Orchestrator. Your role is to coordinate with the "
        "itinerary_agent and budget_agent to build a complete, cohesive holiday plan. "
        "First, call the budget_agent to get a detailed cost breakdown and budget optimization tips. "
        "Next, call the itinerary_agent to design a personalized day-by-day itinerary. "
        "Combine their outputs into a single, cohesive, and beautiful holiday proposal. "
        "If the user has provided feedback (found in the conversation history or state), "
        "you must explicitly instruct the sub-agents to revise their plans based on that feedback."
    ),
    tools=[
        AgentTool(budget_agent),
        AgentTool(itinerary_agent)
    ]
)

# -----------------------------------------------------------------------------
# Workflow Function Nodes
# -----------------------------------------------------------------------------
def security_checkpoint(ctx: Context, node_input: Any) -> Event:
    """Checks the user input for security and safety concerns (PII, Prompt Injection, Domain Safety)."""
    user_message = ""
    if isinstance(node_input, str):
        user_message = node_input
    elif hasattr(node_input, "text"):
        user_message = node_input.text
    elif isinstance(node_input, dict) and "request" in node_input:
        user_message = str(node_input["request"])
    else:
        user_message = str(node_input)

    # 1. Prompt Injection Detection
    injection_keywords = [
        "ignore previous instructions", 
        "system prompt", 
        "bypass security", 
        "dan mode", 
        "developer mode"
    ]
    injection_detected = any(kw in user_message.lower() for kw in injection_keywords)

    if injection_detected:
        audit_log = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event": "security_violation",
            "severity": "CRITICAL",
            "reason": "Prompt injection attempt detected",
            "input_preview": user_message[:100]
        }
        print(f"[AUDIT LOG] {json.dumps(audit_log)}")
        return Event(
            output="Security Checkpoint Flagged: Prompt injection detected.",
            route="flagged"
        )

    # 2. Domain-Specific Rule: High-Risk Destination Check
    # Safety filter: Block travel planning to extremely high-risk or sanctioned zones
    high_risk_destinations = ["north korea", "syria", "yemen", "somalia", "libya"]
    destination_flagged = any(dest in user_message.lower() for dest in high_risk_destinations)
    
    if destination_flagged:
        audit_log = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event": "domain_policy_violation",
            "severity": "WARNING",
            "reason": "High-risk or sanctioned destination requested",
            "input_preview": user_message[:100]
        }
        print(f"[AUDIT LOG] {json.dumps(audit_log)}")
        return Event(
            output="Security Checkpoint Flagged: Travel to this destination is restricted for safety reasons.",
            route="flagged"
        )

    # 3. PII Scrubbing
    scrubbed_message = user_message
    scrub_targets = []

    # Email addresses
    email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    if re.search(email_regex, scrubbed_message):
        scrubbed_message = re.sub(email_regex, "[EMAIL_REDACTED]", scrubbed_message)
        scrub_targets.append("email")

    # Credit Card numbers
    cc_regex = r"\b(?:\d[ -]*?){13,16}\b"
    if re.search(cc_regex, scrubbed_message):
        scrubbed_message = re.sub(cc_regex, "[CREDIT_CARD_REDACTED]", scrubbed_message)
        scrub_targets.append("credit_card")

    # Phone numbers
    phone_regex = r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b"
    if re.search(phone_regex, scrubbed_message):
        scrubbed_message = re.sub(phone_regex, "[PHONE_REDACTED]", scrubbed_message)
        scrub_targets.append("phone")

    # Passport numbers
    passport_regex = r"\b[A-Z0-9]{6,9}\b"
    if re.search(passport_regex, scrubbed_message):
        scrubbed_message = re.sub(passport_regex, "[PASSPORT_REDACTED]", scrubbed_message)
        scrub_targets.append("passport")

    # 4. Success Logging
    audit_log = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event": "input_validation",
        "severity": "INFO",
        "pii_scrubbed": scrub_targets,
        "status": "SAFE"
    }
    print(f"[AUDIT LOG] {json.dumps(audit_log)}")

    # Store clean input in state
    ctx.state["clean_input"] = scrubbed_message
    return Event(
        output=scrubbed_message,
        route="safe"
    )

async def human_approval(ctx: Context, node_input: Any) -> Any:
    """Pauses the workflow to get human approval on the draft holiday plan."""
    # Store the draft plan in state so we don't lose it across runs
    if node_input:
        ctx.state["draft_plan"] = str(node_input)

    draft_plan = ctx.state.get("draft_plan", "No draft plan available.")
    interrupt_id = "itinerary_approval"
    user_response = ctx.resume_inputs.get(interrupt_id)

    if user_response is None:
        # Yield RequestInput to pause execution and ask the user for feedback
        yield RequestInput(
            interrupt_id=interrupt_id,
            message=(
                f"Here is your draft holiday plan:\n\n{draft_plan}\n\n"
                "Do you approve this plan? (Reply 'yes' to approve, or describe any changes you want)."
            ),
            response_schema=str
        )
        return

    # Process user response
    response_text = str(user_response).strip()
    if response_text.lower() in ["yes", "y", "approve", "approved", "looks good"]:
        ctx.state["approval_status"] = "Approved"
        yield Event(output=draft_plan, route="approved")
    else:
        ctx.state["approval_status"] = "Needs Revision"
        # Store feedback in state so orchestrator can read it
        ctx.state["user_feedback"] = response_text
        yield Event(output=response_text, route="needs_revision")

def generate_final_itinerary(ctx: Context, node_input: Any) -> str:
    """Formats and generates the final holiday plan with travel reminders."""
    draft = ctx.state.get("draft_plan", "")
    final_output = (
        "# 🌴 YOUR FINAL HOLIDAY PLAN 🌴\n\n"
        f"{draft}\n\n"
        "--- \n"
        "### 📋 Travel Reminders:\n"
        "- 🛂 Ensure your visa and travel documents are up to date.\n"
        "- 💵 Double check local currency and exchange rates.\n"
        "- 📦 Pack according to the weather and activities planned.\n\n"
        "Have an amazing and safe trip! 🎉✈️"
    )
    return final_output

def security_event(ctx: Context, node_input: Any) -> str:
    """Terminal node for security violations."""
    return "Access Denied: The security check failed. Your input has been flagged."

# -----------------------------------------------------------------------------
# Workflow Graph Definition
# -----------------------------------------------------------------------------
# Convert Python functions to FunctionNode objects with appropriate settings
security_checkpoint_node = FunctionNode(func=security_checkpoint, name="security_checkpoint")
human_approval_node = FunctionNode(func=human_approval, name="human_approval", rerun_on_resume=True)
generate_final_itinerary_node = FunctionNode(func=generate_final_itinerary, name="generate_final_itinerary")
security_event_node = FunctionNode(func=security_event, name="security_event")

workflow = Workflow(
    name="holiday_planner_workflow",
    edges=[
        (START, security_checkpoint_node),
        (security_checkpoint_node, {"safe": orchestrator_agent, "flagged": security_event_node}),
        (orchestrator_agent, human_approval_node),
        (human_approval_node, {"needs_revision": orchestrator_agent, "approved": generate_final_itinerary_node})
    ]
)

# -----------------------------------------------------------------------------
# App Wrapper
# -----------------------------------------------------------------------------
app = App(
    root_agent=workflow,
    name="app",
)

root_agent = workflow

