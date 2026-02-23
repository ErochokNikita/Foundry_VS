"""Concurrent Workflow using JobFinder and CVFinder agents in Microsoft Agent Framework
# Run this python script
> pip install agent-framework==1.0.0b260107 agent-framework-azure-ai==1.0.0b260107 azure-ai-agentserver-agentframework==1.0.0b10 azure-ai-agentserver-core==1.0.0b10 debugpy
> python <this-script-path>.py
"""

import asyncio
from typing import List

from agent_framework import (
    AgentExecutor,
    AgentExecutorResponse,
    ChatMessage,
    Executor,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from agent_framework.azure import AzureAIClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
from typing_extensions import Never

# Load environment variables
load_dotenv(override=True)

# User inputs for the conversation
USER_INPUTS = [
    "Find software engineering jobs and matching CVs for Python developers with 3+ years experience.",
]

class Dispatcher(Executor):
    """Dispatches the user query to both JobFinder and CVFinder agents for parallel processing."""

    @handler
    async def dispatch(self, messages: List[ChatMessage], ctx: WorkflowContext[str]) -> None:
        """Send the query to both agents."""
        # Extract the user message text
        user_text = messages[-1].text if messages else ""
        await ctx.send_message(user_text)

class Aggregator(Executor):
    """Aggregates results from JobFinder and CVFinder agents."""

    @handler
    async def aggregate(self, results: List[AgentExecutorResponse], ctx: WorkflowContext[Never, str]) -> None:
        """Combine the responses from both agents."""
        job_results = ""
        cv_results = ""
        for response in results:
            text = response.agent_response.text or ""
            if "job_finder" in str(response.executor_id):
                job_results = text
            elif "cv_finder" in str(response.executor_id):
                cv_results = text

        combined = f"Job Findings:\n{job_results}\n\nCV Findings:\n{cv_results}"
        await ctx.yield_output(combined)

async def create_workflow(client: AzureAIClient):
    """Create the concurrent workflow."""
    # Create JobFinder agent
    job_finder = AgentExecutor(
        client.create_agent(
            name="JobFinder",
            instructions=(
                "You are a job finder agent. Based on the user's query, find and list relevant job opportunities. "
                "Include job titles, companies, requirements, and why they match the query."
            ),
        ),
        id="job_finder_executor"
    )

    # Create CVFinder agent
    cv_finder = AgentExecutor(
        client.create_agent(
            name="CVFinder",
            instructions=(
                "You are a CV finder agent. Based on the user's query, find and list relevant CVs or candidate profiles. "
                "Include candidate names, skills, experience, and why they match the query."
            ),
        ),
        id="cv_finder_executor"
    )

    # Create dispatcher and aggregator
    dispatcher = Dispatcher(id="dispatcher")
    aggregator = Aggregator(id="aggregator")

    # Build the concurrent workflow: dispatcher -> fan-out to both agents -> fan-in to aggregator
    return (
        WorkflowBuilder(start_executor=dispatcher)
        .add_fan_out_edges(dispatcher, [job_finder, cv_finder])
        .add_fan_in_edges([job_finder, cv_finder], aggregator)
        .build()
        .as_agent()  # Convert to agent for server mode
    )

async def main() -> None:
    # Check if running in server mode
    import sys
    server_mode = "--server" in sys.argv

    async with (
        # Authentication
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint="https://neues-setup-resource.services.ai.azure.com/api/projects/neues-setup",
            credential=credential
        ) as project_client,
        # Create AzureAIClient
        AzureAIClient(
            project_client=project_client,
            model_deployment_name="gpt-5.2-chat",
            use_latest_version=True,
        ) as client,
    ):
        if server_mode:
            # Server mode
            from azure.ai.agentserver.agentframework import from_agent_framework
            agent = await create_workflow(client)
            await from_agent_framework(agent).run_async()
        else:
            # CLI mode
            workflow = await create_workflow(client)

            # Process user messages
            for user_input in USER_INPUTS:
                print(f"\n# User: '{user_input}'")
                messages = [ChatMessage(role=Role.USER, text=user_input)]
                async for event in workflow.run_stream(messages):
                    if hasattr(event, 'text') and event.text:
                        print(event.text, end="")
                    elif hasattr(event, 'data') and event.data:
                        print(f"Output: {event.data}")
                print("")

            print("\n--- All tasks completed successfully ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Program finished.")