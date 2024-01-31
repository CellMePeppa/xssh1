import socket

def proxy_server():
    # 创建套接字并监听端口
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8000))
    server_socket.listen(1)
    print 'Proxy server is listening on port 8000...'

    while True:
        # 接收客户端连接
        client_socket, client_addr = server_socket.accept()
        print 'Accepted connection from', client_addr

        # 接收客户端请求
        request_data = client_socket.recv(1024)
        print 'Received request:\n', request_data

        # 解析请求
        method, url, version = request_data.split('\r\n')[0].split()

        # 构造目标服务器地址
        _, _, hostname, path = url.split('/', 3)
        target_addr = (hostname, 80)

        # 创建套接字并连接目标服务器
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect(target_addr)

        # 转发请求给目标服务器
        target_socket.send(request_data)

        # 接收目标服务器响应
        response_data = target_socket.recv(1024)
        print 'Received response:\n', response_data

        # 将响应返回给客户端
        client_socket.send(response_data)

        # 关闭套接字
        target_socket.close()
        client_socket.close()

if __name__ == '__main__':
    proxy_server()
