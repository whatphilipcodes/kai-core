import zmq
import threading
from typing import Callable, Optional
from pydantic import ValidationError

from src.kai_core.config import settings
from src.kai_core.utils.logger import get_logger
from src.kai_core.schemata.ipc import DataReceive

logger = get_logger(__name__)


class Receiver:
    def __init__(self):
        self.addr_incoming = f"{settings.network.protocol.value}{settings.network.host_in}:{settings.network.port_in}"
        self.context = zmq.Context.instance()

        self.socket = self.context.socket(zmq.PULL)
        self.socket.bind(self.addr_incoming)

        self._callback: Optional[Callable[[DataReceive], None]] = None
        self._running = False
        self._thread = None

    def register_callback(self, callback: Callable[[DataReceive], None]) -> None:
        self._callback = callback

    def start(self) -> None:
        if self._running:
            logger.warning("Receiver is already running.")
            return

        if self._callback is None:
            logger.warning(
                "Starting receiver without a registered callback. Messages will be dropped."
            )

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        logger.info(f"ZMQ Receiver started and bound to {self.addr_incoming}")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self.socket.close()
        logger.info("ZMQ Receiver stopped.")

    def _process_message(self, message_bytes: bytes) -> None:
        """Deserializes and validates bytes into a Pydantic model."""
        try:
            data = DataReceive.model_validate_json(message_bytes)
            if self._callback:
                self._callback(data)
        except ValidationError as e:
            logger.warning(f"Discarding malformed payload: validation failed.\n{e}")

    def _listen(self) -> None:
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while self._running:
            events = dict(poller.poll(timeout=100))
            if self.socket in events and events[self.socket] == zmq.POLLIN:
                try:
                    message_bytes = self.socket.recv()
                    self._process_message(message_bytes)
                except zmq.ZMQError as e:
                    logger.error(f"ZMQ error during message reception: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error in receiver loop: {e}")
