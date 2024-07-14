import socket
import struct
import sys

MAX_MSG_SIZE = 4096

def send_req(sock, text):
    if len(text) > MAX_MSG_SIZE:
        return -1
    
    message = struct.pack('!I', len(text)) + text.encode()
    try:
        sock.sendall(message)
        print(f"Sent: {text}")
        return 0
    except Exception as e:
        print(f"Error sending data: {e}")
        return -1

def read_res(sock):
    try:
        header = sock.recv(4)
        if not header:
            print("EOF")
            return -1
        
        length = struct.unpack('!I', header)[0]
        if length > MAX_MSG_SIZE:
            print("Message too long")
            return -1
        
        data = sock.recv(length)
        if len(data) != length:
            print("read() error")
            return -1
        
        print(f"Server says: {data.decode()}")
        return 0
    except Exception as e:
        print(f"Error receiving data: {e}")
        return -1

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 1234)
        print(f"Connecting to {server_address[0]}:{server_address[1]}")
        sock.connect(server_address)

        query_list = ["hello1", "hello2", "hello3"]

        # Send all requests
        for query in query_list:
            err = send_req(sock, query)
            if err:
                print(f"Error sending: {query}")
                return

        # Read all responses
        for _ in query_list:
            err = read_res(sock)
            if err:
                print("Error reading response")
                return

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing socket")
        sock.close()

if __name__ == "__main__":
    main()