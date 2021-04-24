from os import stat_result
import socket
import os.path
import time
from datetime import datetime

def send_files(client_connection):
    filename = 'html/files.html'
    print(filename)
    f = open(filename, 'r', encoding = "utf-8")

    status = b'HTTP/1.1 200 OK\n'
    header = b'Content-Type: text/html\n'    
    
    html = ''
    for line in f.readlines(): #Doc tung dong trong files.html 
        html += line
        if '<tbody>' in line:   # Den <tbody> thi them download_file vao style="width:150px;height:150px;"
            for i in os.scandir("download"): # Vao duong dan
                html += '<tr><td style="text-align: center;"><a href="../download/{}" download>{}\
                        </a></td>\n<td style="text-align: center;">{}</td>\n<td style="text-align:\
                        center;">{}</td></tr>\n'.format(i.name, i.name, datetime.fromtimestamp\
                        (os.stat("download/"+i.name).st_mtime), size_formatted(os.stat("download/"+i.name)\
                        .st_size))
                #Tra len server
            line = f.read(1024*20)
    data = status + header + b'\r\n' + html.encode()
    client_connection.sendall(data)
    f.close()



def size_formatted(bytes, units=[' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']):
    return str(bytes) + units[0] if bytes < 1024 else size_formatted(bytes >> 10, units[1:])

class Server:
    def __init__(self, SERVER_HOST = '127.0.0.1', SERVER_PORT = 8888):
        self.SERVER_HOST = SERVER_HOST
        self.SERVER_PORT = SERVER_PORT
        self.login = False

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.bind((self.SERVER_HOST, self.SERVER_PORT))
        server.listen(5)

        print("Listening at (%s, %s)" % (self.SERVER_HOST, self.SERVER_PORT))

        while True:
            client_connection, client_addr = server.accept()
            print("Connected by", client_addr)

            request = client_connection.recv(1024).decode()
            if request == "":
                continue
                
            self.handle_request(request, client_connection)

            client_connection.close()

        server.close()
    
    def handle_request(self, request, client_connection):
        headers = request.split('\n')
        filename = headers[0].split()[1]
        print('Filename: ', filename)
        method = headers[0].split()[0]
        print('Method: ', method)
        print('\n')

        if method == 'POST':
            if headers[-1] == 'username=admin&password=admin':
                filename = '/info.html'
                self.login = True

            else:
                filename = '/404.html'
                self.login = True

        if self.login == False and filename != '/':
            
            filename = '/index.html'

        if filename == '/logout' or filename == '/back':
            self.login = False
            filename = '/index.html'
            
        if filename == '/':
                filename = '/home.html'

        # doc cac file tru files.html
        if filename[-4::] == 'html' and filename[1:-5]!='files':
            try:
                fin = open('html' + filename)

                content = fin.read()
                fin.close()

                content_type = 'text/html'
                header = 'Content-Type: ' + content_type + '\n'

                if filename[1:-5]=='info':
                    response = 'HTTP/1.1 301 Moved Permanently\n' + header + content
                elif filename[1:-5]=='404':
                    response = 'HTTP/1.1 404 NOT FOUND\n' + header + content
                else:
                    response = 'HTTP/1.1 200 OK\n' + header + content

            except FileNotFoundError:
                response = 'HTTP/1.1 404 NOT FOUND\n\nFile Not Found'
            client_connection.send(response.encode())

        elif filename[1:-5] == 'files':
            send_files(client_connection)

        else:
            # Xu li chunked
            fin = open(filename[1::], 'rb')
            data = fin.read(1024*20)
            response_body = b''
            header = 'Transfer-Encoding: chunked\r\n'
            response = 'HTTP/1.1 200 OK\r\n' + header 
            response_body += response.encode() + b'\r\n'
            
            while data:  # Doc lien tuc
                data_len = len(data)
                data_len_hex = hex(data_len)[2:data_len].encode()
                response_body += data_len_hex + b'\r\n' + data + b'\r\n'
                data = fin.read(1024*20)
            response_body += b'0\r\n\r\n'
            client_connection.sendall(response_body)
            

if __name__ == '__main__':
    server = Server()
    server.start()
