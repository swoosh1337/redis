import socket
import struct
import sys

MAX_MSG_SIZE = 4096

def send_req(sock, cmd):
    data = struct.pack('!I', len(cmd))
    for s in cmd:
        data += struct.pack('!I', len(s)) + s.encode()
    
    length = len(data)
    if length > MAX_MSG_SIZE:
        print("Message too long")
        return -1
    
    message = struct.pack('!I', length) + data
    try:
        sock.sendall(message)
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
        
        rescode, msg = struct.unpack('!I', data[:4])[0], data[4:].decode() if len(data) > 4 else ""
        if rescode == 0:
            print(f"server says: [0]{' ' + msg if msg else ''}")
        elif rescode == 1:
            print(f"server says: [1] {msg}")
        elif rescode == 2:
            print("server says: [2]")
        else:
            print(f"server says: [{rescode}] {msg}")
        return 0
    except Exception as e:
        print(f"Error receiving data: {e}")
        return -1

def interactive_mode(sock):
    while True:
        try:
            cmd = input("Enter command (or 'quit' to exit): ").split()
            if not cmd:
                continue
            if cmd[0].lower() == 'quit':
                break
            err = send_req(sock, cmd)
            if err:
                break
            err = read_res(sock)
            if err:
                break
        except KeyboardInterrupt:
            break
    print("Exiting interactive mode")

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 1234)
        sock.connect(server_address)
        print(f"Connected to {server_address[0]}:{server_address[1]}")

        if len(sys.argv) > 1:
            if sys.argv[1] == '-i':
                interactive_mode(sock)
            else:
                cmd = sys.argv[1:]
                err = send_req(sock, cmd)
                if not err:
                    err = read_res(sock)
        else:
            print("Usage: python client.py [-i] <command> [args...]")
            print("  -i: Interactive mode")
            print("Examples:")
            print("  python client.py get k")
            print("  python client.py set k v")
            print("  python client.py del k")
            print("  python client.py -i")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing connection")
        sock.close()

if __name__ == "__main__":
    main()