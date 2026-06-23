import time
import socket
from typing import Optional
from pydantic import ValidationError

from src.kai_core.config import settings
from src.kai_core.io.sender import Sender
from src.kai_core.io.receiver import Receiver
from src.kai_core.utils.logger import get_logger, setup_logging
from src.kai_core.schemata.ipc import DataReceive

setup_logging()
logger = get_logger(__name__)

NODE_NAME = socket.gethostname()

sender_instance: Optional[Sender] = None

def handle_pipeline_message(item: DataReceive) -> None:
    """Processes messages passing through the pipeline stage."""
    global sender_instance
    
    msg_text = item.message
    
    marker = f"|Origin:{NODE_NAME}"
    if marker in msg_text:
        clean_msg = msg_text.split(marker)[0]
        print(f"\n[LOOP COMPLETE] Message successfully routed back home: '{clean_msg}'\n> ", end="")
        return

    print("\n[TRANSIT] Processing message from upstream node. Forwarding downstream...\n> ", end="")
    if sender_instance:
        sender_instance.send(item)

def main() -> None:
    global sender_instance
    
    logger.info(f"Starting Node [{NODE_NAME}] log level: {settings.system.log_level}")

    receiver = Receiver()
    receiver.register_callback(handle_pipeline_message)
    receiver.start()

    sender_instance = Sender()
    sender_instance.start()

    time.sleep(0.5)

    print(f"\n--- Pipeline Node: {NODE_NAME} Running ---")
    print("Type a message to inject into the loop.\n")

    try:
        while True:
            user_input = input("> ")
            if not user_input.strip():
                continue
            tracked_text = f"{user_input} |Origin:{NODE_NAME}"
            
            try:
                payload = DataReceive(message=tracked_text)
                if sender_instance:
                    sender_instance.send(payload)
                    logger.info("Message injected into pipeline loop.")
            except ValidationError as e:
                logger.error(f"Payload validation constraint violation: {e}")

    except KeyboardInterrupt:
        print("\nNode execution interrupted manually.")
    finally:
        receiver.stop()
        if sender_instance:
            sender_instance.stop()
        logger.info("Node cleanup finalized.")

if __name__ == "__main__":
    main()