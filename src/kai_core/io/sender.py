import zmq
from pydantic import BaseModel

from src.kai_core.config import settings
from src.kai_core.utils.logger import get_logger

logger = get_logger(__name__)

class Sender:
    def __init__(self):
        self.addr_outgoing = f"{settings.network.protocol.value}{settings.network.host_out}:{settings.network.port_out}"
        self.context = zmq.Context.instance()
        
        self.socket = self.context.socket(zmq.PUSH)
        self._running = False

    def start(self) -> None:
        if self._running:
            logger.warning("Sender is already running.")
            return

        self.socket.connect(self.addr_outgoing)
        self._running = True
        logger.info(f"ZMQ Sender connected downstream to {self.addr_outgoing}")

    def stop(self) -> None:
        if not self._running:
            return
            
        self._running = False
        self.socket.close()
        logger.info("ZMQ Sender stopped.")

    def send(self, payload: BaseModel) -> None:
        if not self._running:
            logger.error("Cannot send message: Sender is not running.")
            return
            
        try:
            message_bytes = payload.model_dump_json().encode('utf-8')
            self.socket.send(message_bytes)
            logger.debug(f"Message sent successfully: {message_bytes}")
        except zmq.ZMQError as e:
            logger.error(f"ZMQ error during message transmission: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during message transmission: {e}")