import time
import sys
from pydantic import ValidationError

from src.kai_core.config import settings
from src.kai_core.io.sender import Sender
from src.kai_core.io.receiver import Receiver
from src.kai_core.utils.logger import get_logger
from src.kai_core.schemata.ipc import DataReceive

logger = get_logger(__name__)

def callback_test(item: DataReceive) -> None:
    print(f"\n[RECEIVER] Payload received: {item.model_dump()}\n> ", end="")

def main() -> None:
    logger.info(
        f"Initializing Kai Core System with log level: {settings.system.log_level}."
    )

    receiver = Receiver()
    receiver.register_callback(callback_test)
    receiver.start()

    sender = Sender()
    sender.start()

    time.sleep(0.1)

    print("\n--- ZMQ Interactive Test ---")
    print("Type a message to send.\n")

    try:
        while True:
            user_input = input("> ")
                
            if not user_input.strip():
                continue

            try:
                payload = DataReceive(message=user_input)
                sender.send(payload)
                
            except ValidationError as e:
                logger.error(f"Input does not match DataReceive schema: {e}")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    finally:
        sender.stop()
        receiver.stop()
        logger.info("System shutdown complete.")

if __name__ == "__main__":
    main()