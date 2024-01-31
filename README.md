# encoding:utf-8
import socket
import concurrent.futures

class Header:
    """
    用于读取和解析头信息
    """
    def __init__(self, client):
        self.client = client
        self.data = b''
        self.method = ''
        self.host = ''
        self.port = 80
        self.ssl = False
        self.parse()

    def parse(self):
        data = self.client.recv(1024)
        self.data += data
        headers = data.decode().split('\r\n')
        first_line = headers[0].split(' ')
        if len(first_line) < 2:
            return
        self.method = first_line[0]
        url = first_line[1]
        if 'https://' in url:
            self.ssl = True
            self.host = url.split(':')[0][8:]
            self.port = 443
        else:
            self.host = url.split(':')[0]
            if len(url.split(':')) == 3:
                self.port = int(url.split(':')[2].split('/')[0])
        for h in headers[1:]:
            if 'Host' in h:
                self.host = h.split(' ')[1]
                if ':' in self.host:
                    self.host, self.port = self.host.split(':')
                    self.port = int(self.port)
                break

    def is_ssl(self):
        return self.ssl

    def get_method(self):
        return self.method

    def get_host_info(self):
        return self.host, self.port


def communicate(sock1, sock2):
    """
    socket之间的数据交换
    :param sock1:
    :param sock2:
    :return:
    """
    try:
        while 1:
            data = sock1.recv(1024)
            if not data:
                return
            sock2.sendall(data)
    except:
        pass

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
    print(*header.get_host_info(), header.get_method())
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.connect(header.get_host_info())
        server.settimeout(timeout)
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

def serve(ip, port):
    """
    代理服务
    :param ip:
    :param port:
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ip, port))
        s.listen(10)
        print('proxy start...')
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                conn, addr = s.accept()
                executor.submit(handle, conn)

if __name__ == '__main__':
    IP = "0.0.0.0"
    PORT = 25432
    serve(IP, PORT)
