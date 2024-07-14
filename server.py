import socket
import select
import struct
import sys

MAX_MSG_SIZE = 4096

STATE_REQ = 0
STATE_RES = 1
STATE_END = 2

class Connection:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.state = STATE_REQ
        self.rbuf = bytearray()
        self.wbuf = bytearray()

def main():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to all interfaces
        server_address = ('', 1234)
        print(f"Starting up on {server_address[0]}:{server_address[1]}")
        server_socket.bind(server_address)
        
        server_socket.listen(5)
        server_socket.setblocking(False)
        print("Server is listening for connections...")

        connections = {}

        while True:
            rlist = [server_socket] + [conn.conn for conn in connections.values() if conn.state == STATE_REQ]
            wlist = [conn.conn for conn in connections.values() if conn.state == STATE_RES]
            
            readable, writable, exceptional = select.select(rlist, wlist, rlist, 1.0)

            for s in exceptional:
                print(f"Handling exceptional condition for {s.getpeername()}")
                s.close()
                if s in connections:
                    del connections[s]

            for s in readable:
                if s is server_socket:
                    client_socket, client_address = s.accept()
                    print(f"New connection from {client_address}")
                    client_socket.setblocking(False)
                    connections[client_socket] = Connection(client_socket, client_address)
                else:
                    data = s.recv(1024)
                    if data:
                        print(f"Received {len(data)} bytes from {s.getpeername()}")
                        connections[s].rbuf.extend(data)
                        connections[s].state = STATE_RES
                    else:
                        print(f"Closing {s.getpeername()} after reading no data")
                        s.close()
                        del connections[s]

            for s in writable:
                try:
                    next_msg = connections[s].rbuf
                    sent = s.send(next_msg)
                    print(f"Sent {sent} bytes back to {s.getpeername()}")
                    connections[s].rbuf = connections[s].rbuf[sent:]
                    if len(connections[s].rbuf) == 0:
                        connections[s].state = STATE_REQ
                except Exception as e:
                    print(f"Error sending data to {s.getpeername()}: {e}")
                    s.close()
                    del connections[s]

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing server socket")
        server_socket.close()

if __name__ == "__main__":
    main()