"""O laço do agente.

Uma classe só. A sequência precisa ser legível de cima para baixo: pergunta,
chamada ao modelo, ferramenta, observação, nova chamada, resposta final.
"""

from __future__ import annotations

from .model import LLM
from .tools import run_tool


class Agent:
    """Modelo com ferramentas ligadas e o laço que alterna chamada e execução.

    Usa o protocolo de ferramentas do template de conversa do modelo. Um passo
    é uma ferramenta, então max_steps limita quantas chamadas cabem antes da
    resposta final.
    """

    def __init__(self, llm: LLM, tools: list, max_steps: int = 5) -> None:
        self.llm = llm.bind_tools(tools)
        self.tools = {fn.tool_schema["name"]: fn for fn in tools}
        self.max_steps = max_steps

    def run(self, input: str | list[dict]) -> list[dict]:
        """Responde à pergunta, ou continua a conversa, e devolve o histórico.

        O modelo pode pedir várias ferramentas na mesma mensagem, e aí uma
        chamada não enxerga o resultado da outra: a que depende do retorno da
        primeira chega com um valor inventado no argumento. O laço executa uma
        por passo e descarta o resto, antes de anexar a mensagem, porque um
        tool_call sem a mensagem tool correspondente quebra a renderização do
        template no passo seguinte. O que foi descartado o modelo pede de novo,
        agora com a observação da primeira chamada no contexto.
        """
        messages = [{"role": "user", "content": input}] if isinstance(input, str) else list(input)
        for _ in range(self.max_steps):
            message = self.llm.invoke(messages)
            if "tool_calls" in message:
                message = {**message, "tool_calls": message["tool_calls"][:1]}
            messages.append(message)
            if "tool_calls" not in message:
                return messages
            call = message["tool_calls"][0]
            observation = run_tool(call, self.tools)
            messages.append({"role": "tool", "name": call["name"], "content": observation})
        return messages + [{"role": "assistant", "content": "limite de passos atingido"}]
