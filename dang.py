# encoding:utf-8
import gevent
from gevent import socket, monkey

monkey.patch_all()

class Header:
    # ... (与之前相同)

def communicate(sock1, sock2):
    try:
        while True:
            data = sock1.recv(1024)
            if not data:
                return
            sock2.sendall(data)
    except:
        pass

def handle(client):
    timeout = 60
    client.settimeout(timeout)
    header = Header(client)
    if not header.data:
        client.close()
        return
    print(header.get_host_info(), header.get_method())
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.connect(header.get_host_info())
        server.settimeout(timeout)
        if header.is_ssl():
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            client.sendall(data)
            gevent.joinall([
                gevent.spawn(communicate, client, server),
                gevent.spawn(communicate, server, client)
            ])
        else:
            server.sendall(header.data)
            gevent.joinall([
                gevent.spawn(communicate, server, client),
                gevent.spawn(communicate, client, server)
            ])
    except:
        server.close()
        client.close()

def serve(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen(10)
    print('proxy start...')
    while True:
        conn, addr = s.accept()
        gevent.spawn(handle, conn)

if __name__ == '__main__':
    IP = "0.0.0.0"
    PORT = 25432
    serve(IP, PORT)
