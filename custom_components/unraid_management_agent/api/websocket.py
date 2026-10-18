"""WebSocket client for real-time event streaming from the Unraid Management Agent."""

from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Callable
from types import TracebackType
from typing import Any

import websockets


class UnraidWebSocketClient:
    """
    WebSocket client for receiving real-time events from the Unraid Management Agent.

    This client provides multiple ways to manage the connection lifecycle:

    1. **Blocking mode** - Use ``start()`` or ``connect()`` which block until stopped:

       >>> await ws_client.start()  # Blocks forever - use as background task

    2. **Background task mode** - Use ``start_background()`` for non-blocking:

       >>> task = await ws_client.start_background()  # Returns immediately
       >>> # ... do other work ...
       >>> await ws_client.stop()  # Stop when done

    3. **Context manager mode** - Automatic lifecycle management:

       >>> async with ws_client:
       ...     # Client runs in background
       ...     await asyncio.sleep(60)
       >>> # Client automatically stopped

    Args:
        host: The Unraid server hostname or IP address
        port: The API port (default: 8043)
        on_message: Callback function for received messages (raw dict)
        on_error: Callback function for errors
        on_close: Callback function for connection close
        on_connect: Callback function when connected/reconnected
        on_disconnect: Callback function when connection lost
        on_reconnect_failed: Callback function when max retries exhausted
        use_wss: Whether to use WSS (secure WebSocket) instead of WS (default: False)
        auto_reconnect: Whether to automatically reconnect on disconnect (default: True)
        reconnect_delays: Exponential backoff delays in seconds (default: [1,2,4,8,16,32,60])
        max_retries: Maximum reconnection attempts before giving up (default: 10)

    Example:
        >>> async def handle_event(data):
        ...     print(f"Received: {data}")
        >>>
        >>> async def handle_connect():
        ...     print("Connected!")
        >>>
        >>> ws_client = UnraidWebSocketClient(
        ...     "192.168.1.100",
        ...     on_message=handle_event,
        ...     on_connect=handle_connect,
        ...     auto_reconnect=True,
        ... )
        >>>
        >>> # Non-blocking usage (recommended):
        >>> task = await ws_client.start_background()
        >>> # ... do other work ...
        >>> await ws_client.stop()
        >>>
        >>> # Or with context manager:
        >>> async with ws_client:
        ...     await asyncio.sleep(60)  # Client runs in background

    """

    def __init__(
        self,
        host: str,
        port: int = 8043,
        on_message: Callable[[dict[str, Any]], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_close: Callable[[], None] | None = None,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[..., Any] | None = None,
        on_reconnect_failed: Callable[[], None] | None = None,
        use_wss: bool = False,
        auto_reconnect: bool = True,
        reconnect_delays: list[int] | None = None,
        max_retries: int = 10,
        *,
        api_token: str | None = None,
        topics: list[str] | None = None,
    ):
        self.host = host
        self._headers: dict[str, str] = (
            {"Authorization": f"Bearer {api_token.strip()}"}
            if api_token and api_token.strip()
            else {}
        )
        self.port = port
        protocol = "wss" if use_wss else "ws"
        self.ws_url = f"{protocol}://{host}:{port}/api/v1/ws"

        # Callbacks
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_reconnect_failed = on_reconnect_failed

        # Reconnection settings
        self.auto_reconnect = auto_reconnect
        self.reconnect_delays = reconnect_delays or [1, 2, 4, 8, 16, 32, 60]
        self.max_retries = max_retries

        # Internal state
        self._websocket: Any = None  # Type varies by websockets version
        self._running = False
        self._retry_count = 0
        self._background_task: asyncio.Task[None] | None = None
        # Topic filter sent after each connect; None receives every topic
        self._topics = list(topics) if topics is not None else None
        # Filter the agent received on the current connection; None = all
        self._sent_topics: list[str] | None = None
        self._send_lock = asyncio.Lock()

    async def _call_callback(
        self, callback: Callable[..., Any] | None, *args: Any
    ) -> None:
        """Call a callback, handling both sync and async callbacks."""
        if callback:
            call_args = args
            if args:
                try:
                    sig = inspect.signature(callback)
                    has_var_args = any(
                        p.kind
                        in (
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        )
                        for p in sig.parameters.values()
                    )
                    pos_params = [
                        p
                        for p in sig.parameters.values()
                        if p.kind
                        in (
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        )
                    ]
                    if not has_var_args and len(pos_params) == 0:
                        call_args = ()
                except ValueError:
                    pass
                except TypeError:
                    pass

            if inspect.iscoroutinefunction(callback):
                await callback(*call_args)
            else:
                callback(*call_args)

    @property
    def subscribed_topics(self) -> list[str] | None:
        """
        Return the topics the current connection is filtered to.

        This is the filter the agent received, not a pending one. None while
        disconnected or while the connection receives every topic.
        """
        if not self.is_connected:
            return None
        return self._sent_topics

    async def set_topics(self, topics: list[str] | None) -> None:
        """
        Set the topic filter and send it to the agent when connected.

        The filter is sent again after each reconnect, and on the next call
        if a send fails. None resets the connection to every topic.
        """
        self._topics = list(topics) if topics is not None else None
        if self._websocket is None:
            return
        try:
            await self._send_topics(self._websocket)
        except websockets.exceptions.ConnectionClosed:
            # Sent again once the connection is back
            pass

    async def _send_topics(self, websocket: Any) -> None:
        """
        Send the current topic filter unless the agent already has it.

        Sends are serialised, and each records the filter its own frame
        carried. Until a send completes the connection's filter is unknown,
        so it is reported as unfiltered (callers then fetch everything).
        """
        async with self._send_lock:
            topics = self._topics
            if topics == self._sent_topics:
                return
            self._sent_topics = None
            await websocket.send(json.dumps({"subscribe": topics}))
            self._sent_topics = topics

    async def _subscribe_on_connect(self, websocket: Any) -> None:
        """Send the topic filter, if any, to a new connection."""
        async with self._send_lock:
            self._sent_topics = None
        if self._topics is not None:
            await self._send_topics(websocket)

    def _get_reconnect_delay(self) -> int:
        """Get the delay for the current retry attempt."""
        if self._retry_count < len(self.reconnect_delays):
            return self.reconnect_delays[self._retry_count]
        return self.reconnect_delays[-1]

    def _reset_retry_count(self) -> None:
        """Reset the retry counter after successful connection."""
        self._retry_count = 0

    async def connect(self) -> None:
        """
        Connect to the WebSocket and start receiving events.

        This method will block and continuously receive events until disconnect() is called.

        Raises:
            ConnectionError: If unable to connect to the WebSocket

        """
        self._running = True
        try:
            async with websockets.connect(
                self.ws_url, additional_headers=self._headers
            ) as websocket:
                self._websocket = websocket
                self._reset_retry_count()
                await self._subscribe_on_connect(websocket)

                # Call on_connect callback
                await self._call_callback(self.on_connect)

                while self._running:
                    try:
                        message = await websocket.recv()
                        # Handle both str and bytes message types
                        if isinstance(message, bytes):
                            message = message.decode("utf-8")
                        data = json.loads(message)

                        await self._call_callback(self.on_message, data)

                    except json.JSONDecodeError:
                        error = ValueError(f"Failed to parse message: {message!r}")
                        await self._call_callback(self.on_error, error)
                    except websockets.exceptions.ConnectionClosed:
                        break
        except Exception as e:
            await self._call_callback(self.on_error, e)
            raise ConnectionError(f"Failed to connect to WebSocket: {e}") from e
        finally:
            self._websocket = None
            self._sent_topics = None
            await self._call_callback(self.on_close)

    async def start(self) -> None:
        """
        Start the WebSocket client with auto-reconnection support.

        **WARNING: This method blocks indefinitely** until ``stop()`` is called
        or max retries are exhausted. For non-blocking usage, use ``start_background()``
        or the async context manager pattern instead.

        This method handles the connection lifecycle including automatic
        reconnection with exponential backoff when enabled.

        Example:
            >>> # BLOCKING - runs forever, must be used as a background task:
            >>> import asyncio
            >>> ws_client = UnraidWebSocketClient("192.168.1.100")
            >>> task = asyncio.create_task(ws_client.start())
            >>> # ... do other work ...
            >>> await ws_client.stop()
            >>>
            >>> # PREFERRED - use start_background() instead:
            >>> task = await ws_client.start_background()

        """
        self._running = True
        self._retry_count = 0

        while self._running:
            connection_error: Exception | None = None
            received_message = False
            disconnect_code: int | None = None
            disconnect_reason: str | None = None

            try:
                # Disable client-initiated keepalive pings; the Unraid Management Agent
                # server actively sends keepalive pings every 30s. Client-initiated pings
                # can trigger spurious keepalive ping timeout (1011) closes (fixes #135).
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=None,
                    additional_headers=self._headers,
                ) as websocket:
                    self._websocket = websocket
                    await self._subscribe_on_connect(websocket)

                    # Call on_connect callback
                    await self._call_callback(self.on_connect)

                    while self._running:
                        try:
                            message = await websocket.recv()
                            # Successfully received a message - reset retry count
                            if not received_message:
                                received_message = True
                                self._reset_retry_count()

                            # Handle both str and bytes message types
                            if isinstance(message, bytes):
                                message = message.decode("utf-8")
                            data = json.loads(message)

                            await self._call_callback(self.on_message, data)

                        except json.JSONDecodeError:
                            error = ValueError(f"Failed to parse message: {message!r}")
                            await self._call_callback(self.on_error, error)
                        except websockets.exceptions.ConnectionClosed as err:
                            close_frame = getattr(err, "rcvd", None)
                            disconnect_code = getattr(close_frame, "code", None)
                            disconnect_reason = getattr(close_frame, "reason", None)
                            break

            except Exception as e:
                connection_error = e
                if disconnect_reason is None:
                    disconnect_reason = str(e)
                await self._call_callback(self.on_error, e)

            finally:
                self._websocket = None
                self._sent_topics = None

            # Handle disconnection
            if self._running:
                await self._call_callback(
                    self.on_disconnect, disconnect_code, disconnect_reason
                )

            # If auto_reconnect is disabled, stop here
            if not self.auto_reconnect:
                await self._call_callback(self.on_close)
                if connection_error:
                    raise ConnectionError(
                        f"Failed to connect to WebSocket: {connection_error}"
                    ) from connection_error
                break

            # If manually stopped, exit without reconnection
            if not getattr(self, "_running", False):
                await self._call_callback(self.on_close)
                break

            # Attempt reconnection
            self._retry_count += 1

            if self._retry_count > self.max_retries:
                await self._call_callback(self.on_reconnect_failed)
                await self._call_callback(self.on_close)
                self._running = False
                break

            delay = self._get_reconnect_delay()
            await asyncio.sleep(delay)

    async def stop(self) -> None:
        """
        Stop the WebSocket client and disconnect gracefully.

        This is an alias for disconnect() and is the recommended way to
        shut down the client when using start().
        """
        await self.disconnect()

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._running = False
        if self._websocket:
            await self._websocket.close()

    async def start_background(self) -> asyncio.Task[None]:
        """
        Start the WebSocket client as a background task.

        This is the recommended non-blocking way to start the client.
        The returned task can be used to monitor the connection or cancel it.

        Returns:
            asyncio.Task that runs the WebSocket connection. Can be cancelled
            to stop the client (but prefer using ``stop()`` for graceful shutdown).

        Example:
            >>> ws_client = UnraidWebSocketClient(
            ...     "192.168.1.100",
            ...     on_message=lambda data: print(data)
            ... )
            >>> task = await ws_client.start_background()
            >>> # ... do other work while client runs in background ...
            >>> await ws_client.stop()  # Graceful shutdown

        """
        self._background_task = asyncio.create_task(self.start())
        return self._background_task

    async def __aenter__(self) -> UnraidWebSocketClient:
        """
        Async context manager entry - starts the client in background.

        Example:
            >>> async with UnraidWebSocketClient("192.168.1.100") as ws_client:
            ...     # Client is running in background
            ...     await asyncio.sleep(60)
            >>> # Client automatically stopped on exit

        """
        await self.start_background()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit - stops the client gracefully."""
        await self.stop()

    @property
    def is_connected(self) -> bool:
        """Check if the WebSocket is currently connected."""
        if self._websocket is None:
            return False

        closed = getattr(self._websocket, "closed", None)
        if closed is None:
            return True

        return not closed
