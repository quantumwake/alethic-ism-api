from core.base_message_router import Router
from core.pulsar_message_producer_provider import PulsarMessagingProducerProvider

from environment import ROUTING_FILE

message_provider = PulsarMessagingProducerProvider()
message_router = Router(
    provider=message_provider,
    yaml_file=ROUTING_FILE
)
