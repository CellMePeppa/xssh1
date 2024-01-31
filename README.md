import socket
import ssl

def proxy_server():
    # 创建套接字并监听端口
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(1)
    print('Proxy server is listening on port 8000...')

    while True:
        # 接收客户端连接
        try:
            client_socket, client_addr = server_socket.accept()
        except Exception as e:
            print('Error accepting connection:', e)
            continue
        print('Accepted connection from', client_addr)

        # 接收客户端请求
        try:
            request_data = client_socket.recv(1024)
        except Exception as e:
            print('Error receiving data from client:', e)
            client_socket.close()
            continue
        print('Received request:\n', request_data)

        # 解析请求
        try:
            first_line = request_data.split(b'\r\n')[0]
            method, url, version = first_line.split()
        except Exception as e:
            print('Error parsing request:', e)
            response_data = b'HTTP/1.1 400 Bad Request\r\n\r\n'
            client_socket.sendall(response_data)
            client_socket.close()
            continue

        if method == b'CONNECT':
            # 处理HTTPS请求
            try:
                hostname, port = url.decode().split(':')
                target_addr = (hostname, int(port))
                target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_socket.settimeout(5.0)  # 设置连接超时为5秒
                target_socket.connect(target_addr)
            except Exception as e:
                print('Error connecting to target server:', e)
                response_data = b'HTTP/1.1 502 Bad Gateway\r\n\r\n'
                client_socket.sendall(response_data)
                client_socket.close()
                continue
            try:
                client_socket.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                context = ssl.create_default_context()
                ssl_client_socket = context.wrap_socket(client_socket, server_side=True)
                ssl_target_socket = context.wrap_socket(target_socket, server_hostname=hostname)
                # 在代理服务器和目标服务器之间进行转发
                try:
                    forward_traffic(ssl_client_socket, ssl_target_socket)
                except Exception as e:
                    print('Error forwarding data between client and server:', e)
                finally:
                    ssl_client_socket.close()
                    ssl_target_socket.close()
            except Exception as e:
                print('Error forwarding data between client and server:', e)
                ssl_client_socket.close()
                ssl_target_socket.close()
        else:
            # 处理HTTP请求
            _, _, hostname, path = url.decode().split('/', 3)
            target_addr = (hostname, 80)
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(5.0)  # 设置连接超时为5秒
            try:
                target_socket.connect(target_addr)
            except Exception as e:
                print('Error connecting to target server:', e)
                response_data = b'HTTP/1.1 502 Bad Gateway\r\n\r\n'
                client_socket.sendall(response_data)
                client_socket.close()
                continue
            try:
                target_socket.sendall(request_data)
                # 接收响应
                response_data = b''
                while True:
                    recv_data = target_socket.recv(1024)
                    if not recv_data:
                        break
                    response_data += recv_data
                    client_socket.sendall(recv_data)
                target_socket.close()
            except Exception as e:
                print('Error forwarding data between client and server:', e)
                target_socket.close()

        # 关闭客户端套接字
        client_socket.close()

def forward_traffic(source, destination):
    while True:
        try:
            data = source.recv(1024)
            if data:
                destination.sendall(data)
            else:
                break
        except Exception as e:
            print('Error forwarding data between client and server:', e)
            source.close()
            destination.close()
            break

if __name__ == '__main__':
    proxy_server()
