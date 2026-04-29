from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AgentRequest:
    prompt: str


@dataclass(frozen=True)
class AgentResponse:
    content: str


class AgentRunner(Protocol):
    async def run(self, request: AgentRequest) -> AgentResponse:
        """Run an agent task and return a stable response."""
        ...


class EchoAgentRunner:
    async def run(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(content=request.prompt)
