from ismcore.messaging.base_message_router import Router
from ismcore.messaging.nats_message_provider import NATSMessageProvider

from environment import ROUTING_FILE

# message_provider = PulsarMessagingProducerProvider()
message_provider = NATSMessageProvider()
message_router = Router(
    provider=message_provider,
    yaml_file=ROUTING_FILE
)


async def get_message_router():
    await message_router.connect()
    try:
        yield message_router
    finally:
        await message_router.close()