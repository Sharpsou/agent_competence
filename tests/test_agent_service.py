import anyio

from app.agents.service import AgentRequest, EchoAgentRunner


def test_echo_agent_runner_returns_prompt_content() -> None:
    runner = EchoAgentRunner()

    response = anyio.run(runner.run, AgentRequest(prompt="hello"))

    assert response.content == "hello"
