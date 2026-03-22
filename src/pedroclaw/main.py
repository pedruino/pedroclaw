"""FastAPI application entrypoint with AgentOS integration."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.os import AgentOS
from agno.workflow import Workflow

from pedroclaw.agents.llm import get_model
from pedroclaw.agents.models import TriageOutput
from pedroclaw.agents.triage import _build_system_prompt
from pedroclaw.squad.xi import SquadXI, create_pedroclaw_full_review_workflow, create_squad_xi_workflow
from pedroclaw.config import settings
from pedroclaw.dashboard.router import router as dashboard_router
from pedroclaw.database import init_db
from pedroclaw.knowledge.agno_kb import get_knowledge_base
from pedroclaw.observability import setup_langfuse
from pedroclaw.webhooks.router import router as webhooks_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Pedroclaw starting", version="0.1.0", review_engine=settings.review_engine)
    await init_db()
    setup_langfuse()
    yield
    logger.info("Pedroclaw shutting down")


# Create agents for AgentOS
def create_agentos_agents() -> list[Agent | Workflow]:
    """Create agents and workflows for AgentOS from existing Pedroclaw agents."""
    agents = []
    
    # Triage Agent for AgentOS
    model_id = settings.triage.get("model")
    triage_agent = Agent(
        name="Triage",
        model=get_model(model_id=model_id),
        instructions=[_build_system_prompt()],
        output_schema=TriageOutput,
        knowledge=get_knowledge_base(),
        markdown=False,
        add_history_to_context=True,
        num_history_runs=3,
        add_datetime_to_context=True,
    )
    agents.append(triage_agent)
    
    # Squad XI Agent for AgentOS
    squad_xi_agent = SquadXI.create_agent()
    agents.append(squad_xi_agent)
    
    return agents


# Initialize AgentOS with existing app
def create_agentos_app() -> FastAPI:
    """Create the combined FastAPI app with AgentOS."""
    # Create the base FastAPI app first
    base_app = FastAPI(
        title="Pedroclaw",
        description="Workflow Claw — AI-powered GitLab pipeline automation with AgentOS",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add middleware
    base_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add existing routers
    base_app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
    base_app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

    # Serve frontend static files if built
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        base_app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    # Mount static files if directory exists
    static_dir = Path("static")
    if static_dir.exists():
        base_app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @base_app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "service": "pedroclaw"}

    # Create agents and workflows for AgentOS (Studio / os.agno.com list workflows here)
    agents = create_agentos_agents()
    workflows = [
        create_pedroclaw_full_review_workflow(),
        create_squad_xi_workflow(),
    ]

    # Initialize AgentOS with our base app
    agent_os = AgentOS(
        description="Pedroclaw - AI-powered GitLab pipeline automation with AgentOS",
        agents=agents,
        workflows=workflows,
        base_app=base_app,
    )
    
    # Get the combined app with both AgentOS and existing routes
    return agent_os.get_app()


# Create the final combined app
app = create_agentos_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
