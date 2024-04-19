import grpc
import scraper_pb2
import scraper_pb2_grpc
import os
from dotenv import load_dotenv
import sys


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
    stub.Send(request, timeout=2)  # Add timeout such that no response is required

    print("Message Sent")

if __name__ == '__main__':
    topic, content, sender, time, match = sys.argv[1:]
    send_message(topic, content, sender, time, match)
