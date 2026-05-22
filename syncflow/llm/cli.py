"""Typer-based CLI for the multi-provider LLM abstraction."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .models import LLMResponse, Message, hash_messages
from .providers import PROVIDERS, ProviderError, get_provider

app = typer.Typer(
    help="SyncFlow LLM CLI — query multiple providers with token + cost tracking.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def _build_messages(prompt: str, system: Optional[str]) -> list[Message]:
    messages: list[Message] = []
    if system:
        messages.append(Message(role="system", content=system))
    messages.append(Message(role="user", content=prompt))
    return messages


def _summary_table(resp: LLMResponse) -> Table:
    table = Table(title="LLM call summary", show_header=False, expand=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Provider", resp.provider)
    table.add_row("Model", resp.model)
    table.add_row("Input tokens", f"{resp.input_tokens:,}")
    table.add_row("Output tokens", f"{resp.output_tokens:,}")
    table.add_row("Cost (USD)", f"${resp.cost_usd:.6f}")
    table.add_row("Latency", f"{resp.latency_ms:.1f} ms")
    table.add_row("Finish reason", resp.finish_reason)
    table.add_row("Prompt hash", resp.prompt_hash[:16] + "…")
    return table


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="The prompt to send to the model."),
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-p",
        help=f"Provider to use. One of: {', '.join(PROVIDERS)}.",
    ),
    model: str = typer.Option(
        "claude-sonnet-4-5", "--model", "-m", help="Model identifier."
    ),
    system: Optional[str] = typer.Option(
        None, "--system", "-s", help="Optional system prompt."
    ),
    stream: bool = typer.Option(
        False, "--stream", help="Stream the response as it is generated."
    ),
) -> None:
    """Send PROMPT to a model and print the answer plus a metrics table."""

    messages = _build_messages(prompt, system)

    try:
        client = get_provider(provider)
    except ProviderError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    try:
        if stream:
            _run_stream(client, messages, model, provider)
        else:
            resp = client.complete(messages, model)
            console.print(resp.text)
            console.print(_summary_table(resp))
    except ProviderError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)
    except Exception as exc:  # noqa: BLE001 - surface SDK errors cleanly
        err_console.print(f"[red]Request failed:[/red] {exc}")
        raise typer.Exit(code=1)


def _run_stream(client, messages, model, provider) -> None:
    final: LLMResponse | None = None
    console.print(f"[dim]{provider}:{model}[/dim]")
    for chunk in client.stream(messages, model):
        if chunk.text:
            console.print(chunk.text, end="", soft_wrap=True)
        if chunk.response is not None:
            final = chunk.response
    console.print()  # newline after stream

    if final is not None:
        console.print(_summary_table(final))
    else:  # provider returned no aggregated usage
        mini = Table(show_header=False)
        mini.add_column("Metric", style="cyan")
        mini.add_column("Value")
        mini.add_row("Provider", provider)
        mini.add_row("Model", model)
        mini.add_row("Prompt hash", hash_messages(messages)[:16] + "…")
        mini.add_row("Note", "[dim]usage totals unavailable for this stream[/dim]")
        console.print(mini)


if __name__ == "__main__":
    app()
