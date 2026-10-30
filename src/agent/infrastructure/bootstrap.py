"""Composition root: conecta cada puerto del dominio con su implementación.

Arranque: uv run uvicorn agent.infrastructure.bootstrap:create_app --factory --reload
"""

import logging

from fastapi import FastAPI

from agent.application.chat_service import ChatService
from agent.domain.ports import ChatModel
from agent.infrastructure.api.routes import build_router
from agent.infrastructure.config.settings import Settings
from agent.infrastructure.llm.credentials import build_credential
from agent.infrastructure.llm.foundry_chat_model import FoundryChatModel
from agent.infrastructure.persistence.in_memory_store import InMemoryConversationStore
from agent.infrastructure.prompts.loader import load_prompt

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None, chat_model: ChatModel | None = None) -> FastAPI:
    settings = settings or Settings()
    if chat_model is None:
        credential = build_credential(
            provider=settings.foundry.auth_provider,
            api_key=settings.foundry.api_key,
        )
        chat_model = FoundryChatModel(
            endpoint=settings.foundry.endpoint,
            credential=credential,
            deployment=settings.foundry.deployment,
            timeout_s=settings.foundry.timeout_s,
            max_retries=settings.foundry.max_retries,
        )
    service = ChatService(
        model=chat_model,
        store=InMemoryConversationStore(),
        system_prompt=load_prompt(settings.domain),
        max_turns=settings.max_turns,
    )

    app = FastAPI(title=f"agent-{settings.domain}")
    app.include_router(build_router(service))
    return app
