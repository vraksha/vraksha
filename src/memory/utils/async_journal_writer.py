import os
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def atomic_append(path: Path, text: str) -> None:
    """Synchronous fallback for critical atomic appends."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


class AsyncJournalWriter:
    """Non-blocking journal writer to offload disk I/O from the agent's thought loop.
    
    Disk I/O is a synchronous, blocking operation that can stall the Python event 
    loop for several milliseconds — or even seconds if the host system is under 
    heavy I/O wait. In an agentic system, 'thought' latency is the most critical 
    metric. If the agent has to wait for a physical write to complete before 
    moving to its next cognitive step, the perceived responsiveness collapses.
    
    This class uses an internal :class:`asyncio.Queue` to decouple the *intent* 
    to log from the physical write. Callers use :meth:`append` to fire-and-forget 
    their logs. A background worker task consumes the queue and performs the 
    actual :func:`atomic_append` in a separate thread pool via :func:`asyncio.to_thread`.
    """
    def __init__(self):
        self._queue: asyncio.Queue[tuple[Path, str]] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    def start(self):
        """Lazy-initialization ensures we don't spin up a background worker 
        until it's actually needed, saving resources on startup.
        """
        if not self._worker_task:
            self._worker_task = asyncio.create_task(self._worker())

    async def _worker(self):
        """We use :func:`asyncio.to_thread` here because file writes are 
        blocking C-level calls that don't yield to the event loop. This 
        keeps the main loop free for agent logic.
        """
        while True:
            try:
                path, text = await self._queue.get()
                # Use to_thread to keep the event loop free during blocking I/O
                await asyncio.to_thread(atomic_append, path, text)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory journal write failure: {e}", exc_info=True)

    def append(self, path: Path, text: str):
        """High-performance entry point that avoids any await keywords, 
        allowing it to be called from synchronous contexts without friction.
        
        It handles the lazy-start of the worker thread and pushes the new 
        log entry into the background queue.
        """
        try:
            # Try to start if not already running
            if not self._worker_task:
                self.start()

        except RuntimeError:
            # If no loop is running yet, it's okay, we'll start on the next call 
            # or the loop will be available later.
            pass

        self._queue.put_nowait((path, text))

