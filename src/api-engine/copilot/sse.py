#
# SPDX-License-Identifier: Apache-2.0
#
"""Server-sent event plumbing for the copilot chat endpoint.

Two jobs. Formatting events as SSE frames is the easy one. The other is
keepalives: a turn that calls a slow tool can go quiet for a while, and an idle
connection is exactly what an intermediate proxy likes to drop. Emitting a
comment line on a timer means the request thread has to stay responsive while
the model is busy, so the loop runs on a worker thread and hands events back
through a queue.

The worker only makes HTTP calls (to the LLM and to Cello's REST API) and never
touches the ORM, so it needs no database connection of its own.
"""
import json
import logging
import queue
import threading

logger = logging.getLogger(__name__)

KEEPALIVE_SECONDS = 15.0

# How long to hold the response open before committing to a status code. Past
# this the stream starts and later failures arrive as an ``error`` frame, since
# the status line has already gone out.
FIRST_EVENT_TIMEOUT = 15.0

_QUEUE_DEPTH = 64


def frame(name, data):
    """One SSE frame. Compact separators keep tool payloads from bloating."""
    body = json.dumps(data, separators=(",", ":"), default=str)
    return "event: %s\ndata: %s\n\n" % (name, body)


def comment(text="ping"):
    """A comment line. Not an event, so a client parser skips it."""
    return ": %s\n\n" % text


class EventStream:
    """Drives an event generator on a worker thread.

    ``first`` waits for the opening event so the view can still answer with a
    real status code if the turn fails immediately. ``frames`` then yields SSE
    text, inserting a keepalive whenever the worker goes quiet.
    """

    def __init__(self, source, keepalive=KEEPALIVE_SECONDS):
        self._source = source
        self._keepalive = keepalive
        self._queue = queue.Queue(maxsize=_QUEUE_DEPTH)
        self._thread = threading.Thread(
            target=self._produce, name="copilot-stream", daemon=True
        )
        self._replay = []
        self._finished = False

    def _produce(self):
        try:
            for event in self._source:
                self._queue.put(("event", event))
        except Exception as exc:  # noqa: BLE001 - re-raised on the reader side
            self._queue.put(("error", exc))
        finally:
            self._queue.put(("end", None))

    def start(self):
        self._thread.start()

    def first(self, timeout=FIRST_EVENT_TIMEOUT):
        """The first item, or ``None`` if the worker is still thinking.

        Anything taken off the queue here is replayed by ``frames``, so calling
        this does not consume the event.
        """
        try:
            item = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        self._replay.append(item)
        return item

    def frames(self):
        """SSE text for the whole turn, keepalives included."""
        for item in self._replay:
            for text in self._render(item):
                yield text
        self._replay = []

        while not self._finished:
            try:
                item = self._queue.get(timeout=self._keepalive)
            except queue.Empty:
                yield comment()
                continue
            for text in self._render(item):
                yield text

    def _render(self, item):
        kind, payload = item
        if kind == "event":
            yield frame(payload.name, payload.data)
        elif kind == "error":
            self._finished = True
            logger.warning("Cello copilot stream failed: %s", payload)
            yield frame("error", error_payload(payload))
        else:
            self._finished = True


def error_payload(exc):
    """An ``error`` frame body. The code names the class of failure."""
    from copilot.llm import AgentConfigError, AgentUpstreamError

    if isinstance(exc, AgentConfigError):
        return {
            "code": "not_configured",
            "message": "The copilot is not configured: %s" % exc,
        }
    if isinstance(exc, AgentUpstreamError):
        return {
            "code": "upstream_error",
            "message": "The LLM provider could not be reached: %s" % exc,
        }
    return {
        "code": "internal_error",
        "message": "The copilot failed to answer.",
    }
