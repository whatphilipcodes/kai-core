import time
from pydantic import ValidationError

from src.kai_core.config import settings
from src.kai_core.io.sender import Sender
from src.kai_core.io.receiver import Receiver
from src.kai_core.utils.logger import get_logger, setup_logging
from src.kai_core.schemata.ipc import DataReceive
from src.kai_core.config import settings

setup_logging()
logger = get_logger(__name__)

sender_instance = None

def handle_pipeline_message(item: DataReceive) -> None:
    global sender_instance
    msg_text = item.message
    marker = f"|Origin:{settings.network.node_id}"
    
    if marker in msg_text:
        clean_msg = msg_text.split(marker)[0]
        print(f"\n[LOOP COMPLETE] Message returned home successfully: '{clean_msg.strip()}'\n> ", end="")
        return

    print("\n[TRANSIT] Routing pipeline data from upstream node. Forwarding downstream...\n> ", end="")
    if sender_instance:
        sender_instance.send(item)

def main() -> None:
    global sender_instance
    logger.info(f"Starting Pipeline Node [{settings.network.node_id}] log level: {settings.system.log_level}")

    receiver = Receiver()
    receiver.register_callback(handle_pipeline_message)
    receiver.start()

    sender_instance = Sender()
    sender_instance.start()

    time.sleep(0.2)

    print(f"\n--- Pipeline Node: {settings.network.node_id} Running ---")
    print("Type a message to transmit into the loop pipeline.\n")

    try:
        while True:
            user_input = input("> ")
            if not user_input.strip():
                continue

            tracked_text = f"{user_input} |Origin:{settings.network.node_id}"
            try:
                payload = DataReceive(message=tracked_text)
                if sender_instance:
                    sender_instance.send(payload)
                    logger.info("Message successfully injected into loop pipeline.")
            except ValidationError as e:
                logger.error(f"Schema tracking constraints violated: {e}")

    except KeyboardInterrupt:
        print("\nPipeline node execution interrupted manually.")
    finally:
        receiver.stop()
        if sender_instance:
            sender_instance.stop()
        logger.info("Node resources released safely.")

if __name__ == "__main__":
    main()