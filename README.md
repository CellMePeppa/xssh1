# encoding:utf-8
import socket
import select

class Header:
    def __init__(self, conn):
        self.conn = conn
        self.data = b''
        self.is_ssl_ = False
        while True:
            try:
                header = self.conn.recv(1)
                self.data += header
                if self.data[-4:] == b'\r\n\r\n':
                    break
            except:
                break

    def is_ssl(self):
        return self.is_ssl_

    def get_method(self):
        return self.data[:self.data.index(b' ')].decode()

    def get_host(self):
        index = self.data.find(b'Host: ')
        if index == -1:
            return None
        index += 6
        end = self.data.find(b'\r\n', index)
        host = self.data[index:end].decode()
        return host

    def get_port(self):
        if self.is_ssl():
            return 443
        else:
            host = self.get_host()
            if not host:
                return None
            port_index = host.find(':')
            if port_index == -1:
                return 80
            else:
                return int(host[port_index+1:])

    def get_host_info(self):
        host = self.get_host()
        if not host:
            return None
        port = self.get_port()
        if not port:
            return None
        ip = socket.gethostbyname(host)
        if not ip:
            return None
        if self.is_ssl():
            self.is_ssl_ = True
        return (ip, port)


def handle(client):
    """
    处理连接进来的客户端
    :param client:
    :return:
    """
    timeout = 60
    client.settimeout(timeout)
    header = Header(client)
    if not header.data:
        client.close()
        return
    print(header.get_host_info(), header.get_method())
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        r.connect(header.get_host_info())
        r.settimeout(timeout)
        if header.is_ssl():
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            client.sendall(data)
            communicate(client, server)
        else:
            server.sendall(header.data)
        communicate(server, client)
    except:
        server.close()
        client.close()

def communicate(src, dest):
    while True:
        readable, _, _ = select.select([src], [], [], 3)
        if not readable:
            break
        data = src.recv(8096)
        if not data:
            break
        dest.sendall(data)

def serve(ip, port):
    """
    代理服务
    :param ip:
    :param port:
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen(10)
    print('proxy start...')
    inputs = [s]
    try:
        while True:
            readable, _, _ = select.select(inputs, [], [])
            for conn in readable:
                if conn is s:
                    client, addr = s.accept()
                    inputs.append(client)
                else:
                    handle(conn)
    finally:
        s.close()

if __name__ == '__main__':
    IP = "0.0.0.0"
    PORT = 25432
    serve(IP, PORT)
