# Streaming Data Source Tools — Full Implementation Reference

Streaming tools turn continuous data sources (WebSocket, SSE, log tails) into Agent Loop-consumable interfaces. This reference covers complete implementation, lifecycle management, error recovery, and production patterns.

---

## Complete Base Class

```python
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional


@dataclass
class ToolResult:
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    token_estimate: int = 0  # caller fills this for budget tracking

    def __post_init__(self):
        if not self.token_estimate:
            self.token_estimate = len(self.output) // 4  # rough 4-char/token estimate


class StreamingTool(ABC):
    """
    Base class for streaming data source tools.

    Two-mode design:
    - call()   → snapshot (last N items). Used for initial context fill at session start.
    - stream() → live feed (async generator). Used inside Agent Loop main cycle.

    Lifecycle: __init__ → call() / stream() → close()
    Always call close() when Agent stops (use try/finally in Agent Loop).
    """

    def __init__(self):
        self._closed = False
        self._reconnect_attempts = 0
        self._max_reconnects = 3

    @abstractmethod
    async def call(self, input: dict) -> ToolResult:
        """Snapshot: fetch recent N items without opening a stream."""
        ...

    @abstractmethod
    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        """Live feed: yield ToolResult chunks until closed or error."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Tear down underlying connection. Must be idempotent."""
        ...

    async def health_check(self) -> bool:
        """Optional: override to probe connection liveness."""
        return not self._closed
```

---

## Implementation Examples

### 1. Real-Time Transcription (WebSocket + Deepgram)

```python
import json
from typing import AsyncGenerator

import websockets


class TranscriptionStreamTool(StreamingTool):
    """
    Wraps Deepgram real-time WebSocket transcription into Agent Loop chunks.

    Key design decisions:
    1. Buffer partial transcripts internally — don't yield until is_final=True
    2. Batch by time OR sentence count, not by WebSocket message
    3. Queue decouples WebSocket callbacks from Agent Loop pace
    """

    DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen?punctuate=true&utterances=true"

    def __init__(self, api_key: str, audio_source: asyncio.Queue[bytes]):
        super().__init__()
        self.api_key = api_key
        self.audio_source = audio_source
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._transcript_queue: asyncio.Queue[str] = asyncio.Queue()
        self._partials: list[str] = []

    async def call(self, input: dict) -> ToolResult:
        """Return last N completed sentences from buffer."""
        n = input.get("n", 5)
        recent: list[str] = []
        # Drain without blocking
        while not self._transcript_queue.empty() and len(recent) < n:
            recent.append(await self._transcript_queue.get())
        return ToolResult(output="\n".join(recent), metadata={"source": "snapshot"})

    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        """
        Yield batches of completed transcript sentences.
        batch_seconds controls flush interval — lower = faster response, higher cost.
        """
        batch_seconds: int = input.get("batch_seconds", 30)
        max_sentences: int = input.get("max_sentences", 10)

        await self._connect()

        # Spin up sender coroutine (audio → WebSocket)
        sender_task = asyncio.create_task(self._send_audio())

        batch: list[str] = []
        batch_start = time.monotonic()

        try:
            async for message in self._ws:
                data = json.loads(message)

                if data.get("type") == "Results":
                    transcript = data["channel"]["alternatives"][0]["transcript"]
                    is_final = data.get("is_final", False)

                    if transcript and is_final:
                        batch.append(transcript)

                    elapsed = time.monotonic() - batch_start
                    if batch and (elapsed >= batch_seconds or len(batch) >= max_sentences):
                        yield ToolResult(
                            output="\n".join(batch),
                            metadata={"is_final": True, "sentence_count": len(batch)},
                        )
                        batch.clear()
                        batch_start = time.monotonic()

        except websockets.ConnectionClosed:
            if batch:
                yield ToolResult(output="\n".join(batch), metadata={"is_final": True})
        finally:
            sender_task.cancel()

    async def _connect(self) -> None:
        headers = {"Authorization": f"Token {self.api_key}"}
        self._ws = await websockets.connect(self.DEEPGRAM_URL, extra_headers=headers)

    async def _send_audio(self) -> None:
        """Pump audio bytes from source queue into WebSocket."""
        while True:
            chunk = await self.audio_source.get()
            if self._ws and not self._ws.closed:
                await self._ws.send(chunk)

    async def close(self) -> None:
        self._closed = True
        if self._ws and not self._ws.closed:
            await self._ws.close()
```

---

### 2. Log Tail Tool (file / journald)

```python
import asyncio
import os


class LogTailTool(StreamingTool):
    """
    Tail a log file and yield new lines as they appear.
    Useful for: monitoring build output, watching service logs during task execution.
    """

    def __init__(self, path: str, encoding: str = "utf-8"):
        super().__init__()
        self.path = path
        self.encoding = encoding
        self._stop = asyncio.Event()

    async def call(self, input: dict) -> ToolResult:
        """Return last N lines of file (snapshot)."""
        n = input.get("n", 20)
        lines: list[str] = []
        try:
            with open(self.path, encoding=self.encoding) as f:
                lines = f.readlines()[-n:]
        except FileNotFoundError:
            return ToolResult(output="", error=f"File not found: {self.path}")
        return ToolResult(output="".join(lines))

    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        """
        Yield new log lines as they appear. Polls every poll_interval seconds.
        batch_lines: yield after accumulating this many lines (or timeout).
        """
        poll_interval: float = input.get("poll_interval", 0.5)
        batch_lines: int = input.get("batch_lines", 20)
        timeout_seconds: float = input.get("timeout_seconds", 10.0)

        try:
            with open(self.path, encoding=self.encoding) as f:
                f.seek(0, os.SEEK_END)  # start at end of file

                batch: list[str] = []
                batch_start = time.monotonic()

                while not self._stop.is_set():
                    line = f.readline()
                    if line:
                        batch.append(line.rstrip())
                    else:
                        await asyncio.sleep(poll_interval)

                    elapsed = time.monotonic() - batch_start
                    if batch and (len(batch) >= batch_lines or elapsed >= timeout_seconds):
                        yield ToolResult(
                            output="\n".join(batch),
                            metadata={"line_count": len(batch), "source": self.path},
                        )
                        batch.clear()
                        batch_start = time.monotonic()

        except FileNotFoundError:
            yield ToolResult(output="", error=f"File not found: {self.path}")

    async def close(self) -> None:
        self._closed = True
        self._stop.set()
```

---

### 3. Server-Sent Events (SSE) Tool

```python
import aiohttp


class SSETool(StreamingTool):
    """
    Consumes an SSE endpoint and yields event data chunks.
    Common for: CI/CD build logs, deployment progress, LLM streaming APIs.
    """

    def __init__(self, url: str, headers: Optional[dict] = None):
        super().__init__()
        self.url = url
        self.headers = headers or {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._stop = asyncio.Event()

    async def call(self, input: dict) -> ToolResult:
        """SSE has no snapshot concept — returns empty with warning."""
        return ToolResult(
            output="",
            metadata={"warning": "SSE has no snapshot mode; use stream() from session start"}
        )

    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        """Yield SSE events. Reconnects up to max_reconnects on connection drop."""
        batch_events: int = input.get("batch_events", 5)
        reconnect_delay: float = input.get("reconnect_delay", 2.0)

        while self._reconnect_attempts <= self._max_reconnects and not self._stop.is_set():
            try:
                async with aiohttp.ClientSession() as session:
                    self._session = session
                    async with session.get(self.url, headers=self.headers) as resp:
                        resp.raise_for_status()
                        self._reconnect_attempts = 0  # reset on successful connect
                        batch: list[str] = []

                        async for line in resp.content:
                            if self._stop.is_set():
                                break

                            decoded = line.decode("utf-8").strip()
                            if decoded.startswith("data: "):
                                batch.append(decoded[6:])  # strip "data: " prefix

                            if len(batch) >= batch_events:
                                yield ToolResult(
                                    output="\n".join(batch),
                                    metadata={"event_count": len(batch)},
                                )
                                batch.clear()

                        if batch:
                            yield ToolResult(output="\n".join(batch))

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self._reconnect_attempts += 1
                if self._reconnect_attempts <= self._max_reconnects:
                    yield ToolResult(
                        output="",
                        error=f"Connection lost: {e}. Reconnecting ({self._reconnect_attempts}/{self._max_reconnects})...",
                    )
                    await asyncio.sleep(reconnect_delay * self._reconnect_attempts)
                else:
                    yield ToolResult(output="", error=f"Max reconnects reached: {e}")
                    break

    async def close(self) -> None:
        self._closed = True
        self._stop.set()
        if self._session and not self._session.closed:
            await self._session.close()
```

---

## Full Streaming Agent Loop

```python
import asyncio
from typing import Callable, Optional

from anthropic import AsyncAnthropic


class StreamingContext:
    """
    Manages context for streaming Agent Loop.
    Append-only strategy: add new chunks, trim oldest when budget exceeded.
    Never resend full history — linear token growth destroys streaming economics.
    """

    def __init__(self, token_budget: int = 4000):
        self.token_budget = token_budget
        self._chunks: list[str] = []
        self._token_count = 0

    def append(self, text: str) -> None:
        tokens = len(text) // 4
        self._chunks.append(text)
        self._token_count += tokens

        # Trim oldest chunks when over budget (keep most recent)
        while self._token_count > self.token_budget and len(self._chunks) > 1:
            removed = self._chunks.pop(0)
            self._token_count -= len(removed) // 4

    def get(self) -> str:
        return "\n---\n".join(self._chunks)

    def clear(self) -> None:
        self._chunks.clear()
        self._token_count = 0


async def streaming_agent_loop(
    stream_tool: StreamingTool,
    system_prompt: str,
    on_response: Callable[[str], None],
    model: str = "claude-sonnet-4-6",  # verified: 2026-04-09
    token_budget: int = 4000,
    batch_seconds: int = 30,
) -> None:
    """
    Data stream-driven Agent Loop.

    Trigger model: new data batch arrives → append to context → call LLM → handle response.
    NOT request-response: user doesn't send messages; data stream drives cadence.

    Args:
        stream_tool:   Streaming data source (TranscriptionStreamTool, LogTailTool, etc.)
        system_prompt: Injected once per LLM call (task instructions)
        on_response:   Callback for each LLM response (push notification, update UI, etc.)
        token_budget:  Max tokens of streaming context to retain
        batch_seconds: How many seconds of data to batch before calling LLM
    """
    client = AsyncAnthropic()
    context = StreamingContext(token_budget=token_budget)

    # Fill initial context via snapshot before starting live stream
    snapshot = await stream_tool.call({"n": 10})
    if snapshot.output:
        context.append(f"[Session start — recent history]\n{snapshot.output}")

    try:
        async for chunk in stream_tool.stream({"batch_seconds": batch_seconds}):
            if chunk.error:
                # Log error but continue — streaming tools recover
                on_response(f"[Stream error: {chunk.error}]")
                continue

            if not chunk.output.strip():
                continue

            # Append new data — does NOT resend full history
            context.append(chunk.output)

            # Call LLM with current context window
            response = await client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": context.get()},
                ],
            )

            result_text = response.content[0].text
            on_response(result_text)

    finally:
        await stream_tool.close()
```

---

## Lifecycle & Error Recovery Patterns

### Pattern 1: Supervised Streaming (restart on crash)

```python
async def supervised_streaming(
    tool_factory: Callable[[], StreamingTool],
    **loop_kwargs,
) -> None:
    """Restart streaming agent loop if tool crashes. Stops on KeyboardInterrupt."""
    max_restarts = 5
    restart_delay = 5.0

    for attempt in range(max_restarts):
        tool = tool_factory()
        try:
            await streaming_agent_loop(tool, **loop_kwargs)
            break  # clean exit
        except Exception as e:
            await tool.close()
            if attempt < max_restarts - 1:
                await asyncio.sleep(restart_delay)
            else:
                raise RuntimeError(f"Streaming failed after {max_restarts} restarts") from e
```

### Pattern 2: Timeout Guard (prevent hung streams)

```python
async def streaming_with_timeout(
    stream_tool: StreamingTool,
    chunk_timeout: float = 60.0,  # error if no chunk for this long
    **loop_kwargs,
) -> None:
    """Inject a watchdog: if no chunk arrives within chunk_timeout seconds, raise."""

    async def guarded_stream():
        async for chunk in stream_tool.stream(loop_kwargs.get("batch_seconds", 30)):
            yield chunk

    async def run():
        async for chunk in guarded_stream():
            try:
                async with asyncio.timeout(chunk_timeout):
                    pass  # chunk already received
            except asyncio.TimeoutError:
                raise RuntimeError(f"No data received for {chunk_timeout}s — stream hung")

    await run()
```

### Pattern 3: Graceful Shutdown on Agent Stop

```python
import signal

_active_tools: list[StreamingTool] = []

def register_tool(tool: StreamingTool) -> StreamingTool:
    _active_tools.append(tool)
    return tool

async def shutdown_all() -> None:
    await asyncio.gather(*[t.close() for t in _active_tools], return_exceptions=True)
    _active_tools.clear()

# In main entry point:
# loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown_all()))
```

---

## Cost & Latency Trade-offs

| `batch_seconds` | LLM calls/hour | Latency | Cost (est.) | Use case |
|---|---|---|---|---|
| 10s | 360 | <15s | High | Critical real-time alerts |
| 30s | 120 | <45s | Medium | Meeting notes, live monitoring |
| 60s | 60 | <90s | Low | Background log analysis |
| 300s | 12 | <6min | Very low | Periodic batch summaries |

**Rule**: Start at 30s. Decrease only when user experience requires it. Each halving doubles cost.

**Token linear growth prevention**: Always use `StreamingContext.append()` with budget trimming. Never `messages.append({"role": "user", "content": full_history})`.

---

## Testing Streaming Tools

```python
import pytest
import asyncio


class MockStreamingTool(StreamingTool):
    """Inject canned chunks for unit testing streaming agent loops."""

    def __init__(self, chunks: list[str], delay: float = 0.01):
        super().__init__()
        self.chunks = chunks
        self.delay = delay

    async def call(self, input: dict) -> ToolResult:
        return ToolResult(output=self.chunks[0] if self.chunks else "")

    async def stream(self, input: dict) -> AsyncGenerator[ToolResult, None]:
        for chunk in self.chunks:
            await asyncio.sleep(self.delay)
            yield ToolResult(output=chunk)

    async def close(self) -> None:
        self._closed = True


@pytest.mark.asyncio
async def test_streaming_context_budget():
    ctx = StreamingContext(token_budget=100)
    ctx.append("a" * 400)  # ~100 tokens
    ctx.append("b" * 400)  # ~100 tokens — should evict first chunk
    assert "a" not in ctx.get()  # oldest trimmed
    assert "b" in ctx.get()


@pytest.mark.asyncio
async def test_mock_streaming_tool():
    tool = MockStreamingTool(chunks=["chunk1", "chunk2", "chunk3"])
    results = []
    async for chunk in tool.stream({}):
        results.append(chunk.output)
    assert results == ["chunk1", "chunk2", "chunk3"]
    await tool.close()
    assert tool._closed
```

---

## When NOT to Use Streaming Tools

| Situation | Better alternative |
|---|---|
| Data arrives in discrete batches (hourly exports) | Regular `call()` tool with polling |
| WebSocket but < 1 message/minute | Request-response tool with long timeout |
| Need random access into history | Snapshot tool + external storage |
| MCP server integration | Streamable HTTP transport (stateless, horizontally scalable) |

Streaming tools add lifecycle complexity. Only reach for them when latency < 60s is a real requirement.
