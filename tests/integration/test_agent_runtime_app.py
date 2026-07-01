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

"""
Tests for agent_runtime_app (Vertex AI Agent Engine).

These tests require Google Cloud Application Default Credentials and a
valid GOOGLE_CLOUD_PROJECT environment variable to be set.
They are automatically skipped in local dev environments.
"""

import os
import pytest

# Skip entire module if no cloud credentials are configured.
# This prevents CI failures in local environments.
pytestmark = pytest.mark.skipif(
    os.environ.get("GOOGLE_CLOUD_PROJECT") is None,
    reason=(
        "GOOGLE_CLOUD_PROJECT is not set — skipping Vertex AI tests. "
        "To run these, set GOOGLE_CLOUD_PROJECT and configure ADC with: "
        "gcloud auth application-default login"
    ),
)


@pytest.fixture
def agent_app():
    """Fixture to create and set up AgentEngineApp instance."""
    os.environ["INTEGRATION_TEST"] = "TRUE"
    from app.agent_runtime_app import agent_runtime  # noqa: PLC0415
    agent_runtime.set_up()
    return agent_runtime


@pytest.mark.asyncio
async def test_agent_stream_query(agent_app) -> None:
    """Integration test for async_stream_query — requires cloud credentials."""
    from google.adk.events.event import Event  # noqa: PLC0415

    message = "Plan a 2-day trip to Paris."
    events = []
    async for event in agent_app.async_stream_query(message=message, user_id="test"):
        events.append(event)
    assert len(events) > 0, "Expected at least one chunk in response"

    has_text_content = any(
        Event.model_validate(e).content
        and Event.model_validate(e).content.parts
        and any(p.text for p in Event.model_validate(e).content.parts)
        for e in events
    )
    assert has_text_content, "Expected at least one event with text content"


def test_agent_feedback(agent_app) -> None:
    """Integration test for register_feedback — requires cloud credentials."""
    feedback_data = {
        "score": 5,
        "text": "Great response!",
        "user_id": "test-user-456",
        "session_id": "test-session-456",
    }
    agent_app.register_feedback(feedback_data)

    with pytest.raises(ValueError):
        agent_app.register_feedback(
            {
                "score": "invalid",
                "text": "Bad feedback",
                "user_id": "test-user-789",
                "session_id": "test-session-789",
            }
        )
