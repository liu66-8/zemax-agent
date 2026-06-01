from __future__ import annotations

import json
import logging
import sys
import threading
import time
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IPCMessage(BaseModel):
    type: str
    id: Optional[str] = None
    command: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    data: Any = None
    error: Optional[str] = None
    progress: Optional[float] = None
    message: Optional[str] = None


class IPCRouter:
    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._event_listeners: dict[str, list[Callable]] = {}
        self._running = False
        self._heartbeat_interval = 5.0
        self._last_heartbeat: float = 0.0
        self._seq = 0

    def register_handler(self, command: str, handler: Callable) -> None:
        self._handlers[command] = handler

    def on_event(self, event_type: str, callback: Callable) -> None:
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(callback)

    def handle_message(self, raw: str) -> Optional[IPCMessage]:
        try:
            msg_data = json.loads(raw)
            msg = IPCMessage.model_validate(msg_data)
        except (json.JSONDecodeError, Exception) as e:
            logger.error("Invalid IPC message: %s", e)
            return None

        if msg.type == "request":
            return self._handle_request(msg)
        elif msg.type == "event":
            self._handle_event(msg)
        elif msg.type == "heartbeat":
            self._last_heartbeat = time.time() if hasattr(time, "time") else 0
        elif msg.type == "progress":
            self._emit("progress", msg.data)

        return None

    def _handle_request(self, msg: IPCMessage) -> IPCMessage:
        handler = self._handlers.get(msg.command or "")
        if handler is None:
            return IPCMessage(
                type="response", id=msg.id,
                error=f"Unknown command: {msg.command}",
            )
        try:
            result = handler(**msg.params)
            return IPCMessage(
                type="response", id=msg.id,
                data=result,
            )
        except Exception as e:
            return IPCMessage(
                type="response", id=msg.id,
                error=str(e),
            )

    def _handle_event(self, msg: IPCMessage) -> None:
        if msg.command:
            self._emit(msg.command, msg.data)

    def send_progress(self, progress: float, message: str = "") -> IPCMessage:
        return IPCMessage(
            type="progress",
            progress=progress,
            message=message,
        )

    def send_event(self, event_type: str, data: Any = None) -> IPCMessage:
        return IPCMessage(
            type="event",
            command=event_type,
            data=data,
        )

    def send_heartbeat(self) -> IPCMessage:
        self._seq += 1
        return IPCMessage(
            type="heartbeat",
            id=f"hb_{self._seq}",
        )

    def _emit(self, event_type: str, data: Any) -> None:
        listeners = self._event_listeners.get(event_type, [])
        for cb in listeners:
            try:
                cb(data)
            except Exception:
                pass

    def start_heartbeat(self) -> None:
        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def stop(self) -> None:
        self._running = False

    def _heartbeat_loop(self) -> None:
        while self._running:
            msg = self.send_heartbeat()
            sys.stdout.write(json.dumps(msg.model_dump()) + "\n")
            sys.stdout.flush()
            time.sleep(self._heartbeat_interval)

    def write_message(self, msg: IPCMessage) -> None:
        sys.stdout.write(json.dumps(msg.model_dump()) + "\n")
        sys.stdout.flush()
