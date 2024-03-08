import grpc
import scraper_pb2
import scraper_pb2_grpc
import os
from dotenv import load_dotenv

load_dotenv()


def send_message(topic, content, sender, time, match):
    # Create gRPC channel by connecting to external server. Should be either URL or host:port. Use secure for secure connection. usually gRPC we just use insecure
    channel = grpc.insecure_channel(os.getenv("ROUTING_SERVER"))
    # Stub for client
    stub = scraper_pb2_grpc.MessageStub(channel)

    # Generate request
    request = scraper_pb2.Request(
        topic=topic, content=content, sender=sender, time=time, match=match
    )

    # Call method to send
    response = stub.Send(request)

    print("Message Sent", response.success)


# Example Send. Uncomment if you have configured ROUTING_SERVER as env variable connecting to Routing Server
# if __name__ == '__main__':
#     topic = "scraper_updates"
#     content = "We found Products on your Website"
#     sender = "Scraper"
#     time = "2024-03-01T12:00:00"
#     match = "www.glossier.com/p/2s8k2a"
#     send_message(topic, content, sender, time, match)
