import socket
import select
import struct

MAX_MSG_SIZE = 4096

# In-memory key-value store
kv_store = {}

def handle_request(data):
    if len(data) < 4:
        return struct.pack('!II', 4, 1) + b'ERR'
    
    num_strs = struct.unpack('!I', data[:4])[0]
    data = data[4:]
    strings = []
    
    for _ in range(num_strs):
        if len(data) < 4:
            return struct.pack('!II', 4, 1) + b'ERR'
        str_len = struct.unpack('!I', data[:4])[0]
        data = data[4:]
        if len(data) < str_len:
            return struct.pack('!II', 4, 1) + b'ERR'
        strings.append(data[:str_len].decode())
        data = data[str_len:]
    
    if not strings:
        return struct.pack('!II', 4, 1) + b'ERR'
    
    print(f"Received command: {strings}")  # Log the received command
    
    cmd = strings[0].lower()
    if cmd == 'get':
        if len(strings) != 2:
            return struct.pack('!II', 4, 1) + b'ERR'
        key = strings[1]
        if key in kv_store:
            response = kv_store[key].encode()
            return struct.pack('!II', len(response) + 4, 0) + response
        else:
            return struct.pack('!II', 4, 2)
    elif cmd == 'set':
        if len(strings) != 3:
            return struct.pack('!II', 4, 1) + b'ERR'
        key, value = strings[1], strings[2]
        kv_store[key] = value
        return struct.pack('!II', 4, 0)
    elif cmd == 'del':
        if len(strings) != 2:
            return struct.pack('!II', 4, 1) + b'ERR'
        key = strings[1]
        if key in kv_store:
            del kv_store[key]
            return struct.pack('!II', 4, 0)
        else:
            return struct.pack('!II', 4, 2)
    else:
        response = b'Unknown cmd'
        return struct.pack('!II', len(response) + 4, 1) + response

class Connection:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.rbuf = bytearray()
        self.wbuf = bytearray()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 1234))
    server_socket.listen(5)
    server_socket.setblocking(False)
    print("Server started on port 1234")

    connections = {}

    while True:
        rlist = [server_socket] + [conn.conn for conn in connections.values()]
        wlist = [conn.conn for conn in connections.values() if conn.wbuf]
        
        readable, writable, _ = select.select(rlist, wlist, [], 1.0)

        for s in readable:
            if s is server_socket:
                client_socket, client_address = s.accept()
                print(f"New connection from {client_address}")
                client_socket.setblocking(False)
                connections[client_socket] = Connection(client_socket, client_address)
            else:
                conn = connections[s]
                data = s.recv(MAX_MSG_SIZE)
                if data:
                    conn.rbuf.extend(data)
                    while len(conn.rbuf) >= 4:
                        msg_len = struct.unpack('!I', conn.rbuf[:4])[0]
                        if len(conn.rbuf) >= msg_len + 4:
                            msg = conn.rbuf[4:msg_len+4]
                            conn.rbuf = conn.rbuf[msg_len+4:]
                            response = handle_request(msg)
                            conn.wbuf.extend(response)
                        else:
                            break
                else:
                    print(f"Connection closed by {s.getpeername()}")
                    s.close()
                    del connections[s]

        for s in writable:
            conn = connections[s]
            sent = s.send(conn.wbuf)
            conn.wbuf = conn.wbuf[sent:]

if __name__ == "__main__":
    main()