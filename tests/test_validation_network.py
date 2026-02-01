import socket
import json

def validate_network_send(port=5670):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_payload = json.dumps({"test": True}).encode("utf-8")
    s.sendto(test_payload, ("127.0.0.1", port))
    print(f"Payload sent to port {port},  SUCCESS")

if __name__ == "__main__":
    validate_network_send()