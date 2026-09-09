"""Infraestrutura mínima para o uso de ferramentas pelo agente."""

from __future__ import annotations

import ast
import io
import json
import inspect
from contextlib import redirect_stdout
from typing import Callable

TOOL_SYSTEM_PROMPT = """You have access to the tools below.

{tools}

To use a tool, reply only with a JSON object in this format:
{{"name": "tool_name", "arguments": {{"argument_name": "value"}}}}

The result will be returned in a message with the `tool` role.
Use at most one tool at a time.
When you know the answer, reply with plain text instead of JSON."""

# Tipos Python traduzidos para os nomes usados no esquema.
_TYPE_NAMES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def tool(fn: Callable) -> Callable:
    """Anexa fn.tool_schema por introspecção e devolve a própria função.

    A função continua chamável normalmente e recebe um atributo tool_schema.
    """
    doc = inspect.getdoc(fn)
    if not doc:
        raise ValueError(f"A ferramenta {fn.__name__} precisa de docstring.")
    signature = inspect.signature(fn)
    parameters: dict[str, dict] = {}
    required: list[str] = []
    for name, parameter in signature.parameters.items():
        if parameter.annotation is inspect.Parameter.empty:
            raise ValueError(f"O parâmetro {name} de {fn.__name__} precisa de anotação de tipo.")
        parameters[name] = {"type": _TYPE_NAMES.get(parameter.annotation, "string")}
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
        else:
            parameters[name]["default"] = parameter.default
    fn.tool_schema = {
        "name": fn.__name__,
        "description": doc.strip().split("\n")[0],
        "parameters": parameters,
        "required": required,
    }
    return fn


# O estado do interpretador do agente. As variáveis criadas em uma chamada
# continuam disponíveis na seguinte, como acontece entre células de um notebook.
PYTHON_STATE: dict = {}


@tool
def run_python(code: str) -> str:
    """Run Python code and return what it printed, or the value of the last expression.

    A única ferramenta pronta do pacote, porque executar código é o que permite a
    um agente resolver o que nenhuma ferramenta específica cobre.
    """
    buffer = io.StringIO()
    try:
        block = ast.parse(code)
        # O exec não devolve valor, então a última expressão é avaliada à parte.
        # Sem isso o modelo escreve `total` esperando ver o número, não vê nada e
        # completa a lacuna com um valor inventado.
        last = block.body.pop() if block.body else None
        value = None
        with redirect_stdout(buffer):
            exec(compile(block, "<agente>", "exec"), PYTHON_STATE)
            if isinstance(last, ast.Expr):
                value = eval(compile(ast.Expression(last.value), "<agente>", "eval"), PYTHON_STATE)
            elif last is not None:
                exec(compile(ast.Module([last], type_ignores=[]), "<agente>", "exec"), PYTHON_STATE)
    except Exception as error:
        return f"{type(error).__name__}: {error}"
    printed = buffer.getvalue().strip()
    # Observação longa demais ocupa o contexto sem informar.
    return (printed or ("" if value is None else repr(value)) or "ok")[:400]


def render_tools(tools: list[Callable]) -> str:
    """Descreve as ferramentas em texto, uma por linha, para entrar no prompt."""
    lines = []
    for fn in tools:
        schema = fn.tool_schema
        args = ", ".join(f"{name}: {spec['type']}" for name, spec in schema["parameters"].items())
        lines.append(f"- {schema['name']}({args}): {schema['description']}")
    return "\n".join(lines)


def parse_tool_call(text: str) -> dict | None:
    """Extrai a chamada de ferramenta do texto do modelo.

    Devolve None quando não há chamada, e esse None é o sinal de que o texto é a
    resposta final.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data.get("name"), str):
        return None
    arguments = data.get("arguments", {})
    return {"name": data["name"], "arguments": arguments if isinstance(arguments, dict) else {}}


def run_tool(call: dict, tools: dict) -> str:
    """Executa a chamada e devolve o resultado como texto.

    Este é o único ponto do pacote que captura exceção ampla, e a captura existe
    porque o erro precisa voltar ao modelo como observação, não interromper o
    laço do agente. Ferramenta desconhecida recebe o mesmo tratamento, já que o
    nome também vem do modelo.
    """
    fn = tools.get(call.get("name", ""))
    if fn is None:
        return f"ferramenta desconhecida: {call.get('name', '')}"
    try:
        return str(fn(**call.get("arguments", {})))
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
