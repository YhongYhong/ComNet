import os, socket, time, random

clientSocket = None
data_port = random.randint(1024, 65535)

def open_func(args):
    global clientSocket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        if len(args) == 1:
            addr = input("To ").split()
            ip = addr[0]
            if len(addr) == 1:
                clientSocket.connect((ip, 21))
            else:
                clientSocket.connect((ip, int(addr[1])))
        elif len(args) == 2:
            ip = args[1]
            clientSocket.connect((ip, 21))
        elif len(args) == 3:
            ip = args[1]
            clientSocket.connect((ip, int(args[2])))
    except:
        clientSocket = None
        return print("> ftp: connect :Connection refused")
        
    print(f"Connected to {ip}.")
    responseWithEnd()
    
    clientSocket.sendall('OPTS UTF8 ON\r\n'.encode())
    responseWithEnd()
    
    username = input(f"User ({ip}:(none)): ")
    clientSocket.sendall(f"USER {username}\r\n".encode())
    responseWithEnd()
    
    password = input("Password: ")
    clientSocket.sendall(f"PASS {password}\r\n".encode())
    print("")
    message = responseWithEnd().split()
    if message[0] == '530':
        return print("Login failed.")

def disconnect():
    clientSocket.sendall('QUIT\r\n'.encode())
    responseWithEnd()
    clientSocket.close()

def ls():
    f, s = data_port//256, data_port%256
    port_message = "PORT " + ",".join((clientSocket.getpeername()[0]).split(".")) + f",{f},{s}\r\n"
    clientSocket.sendall(port_message.encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return
    
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind(((clientSocket.getpeername()[0]), data_port))
    data_socket.listen(8)
    
    remote_target = ""
    if (len(args) >= 2):
        remote_target = args[1] 

    clientSocket.sendall(f"NLST {remote_target}\r\n".encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return
    
    data_connection, _ = data_socket.accept()
    ls_result = b""
    start_time = time.time()
    while True:
        data = data_connection.recv(1024)
        if not data:
            break
        ls_result += data
    end_time = time.time()
    file_size = len(ls_result.decode()) + 3

    ls_result = ls_result.decode()
    elapsed_time =  end_time-start_time
    transfer_rate = (file_size / (elapsed_time if elapsed_time else 1)) * 1000

    if (len(args) == 3):
        with open(args[2], 'w') as file:
            file.write(ls_result)
    else :
        print(ls_result, end="")

    data_socket.close()        
    message =  responseWithEnd().split()
    if message[0] == "550":
        return
    if transfer_rate % 1000 != 0: transfer_rate = file_size
    if file_size > 3 : print(f"ftp: {file_size} bytes received in {elapsed_time:.2f}Seconds {transfer_rate:.2f}Kbytes/sec.")
    
def ascii():
    clientSocket.send("TYPE A\r\n".encode())
    responseWithEnd()

def binary():
    clientSocket.send("TYPE I\r\n".encode())
    responseWithEnd()

def pwd():
    clientSocket.send("XPWD\r\n".encode())
    responseWithEnd()

def cd(path):
    clientSocket.send(f"CWD {path}\r\n".encode())
    responseWithEnd()

def get():
    remote_target = ""
    local_target = ""

    if (len(args) == 1):
        remote_target = input("Remote file ")
        local_target = input("Local file ")
    elif (len(args) == 2):
        remote_target = args[1]
        local_target = args[1]
    elif (len(args) == 3):
        remote_target = args[1]
        local_target = args[2]
        
    f,s = data_port//256, data_port%256
    port_message = "PORT " + ",".join((clientSocket.getpeername()[0]).split(".")) + f",{f},{s}\r\n"
    clientSocket.sendall(port_message.encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind(((clientSocket.getpeername()[0]), data_port))
    data_socket.listen(8)

    clientSocket.sendall(f"RETR {remote_target}\r\n".encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return

    if (not (len(local_target) >= 2 and local_target[1] == ":")):
        local_target = os.getcwd()+"\\"+local_target

    file_size = None
    data_connection, _ = data_socket.accept()
    with open(local_target, 'wb') as local_fp:
        start_time = time.time()
        while True:
            file_data = data_connection.recv(1024)
            if not file_data:
                break
            local_fp.write(file_data)
            file_size = len(file_data)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if file_size: transfer_rate = (file_size / (elapsed_time if elapsed_time else 1)) * 1000

    data_socket.close()        
    message =  responseWithEnd().split()
    if message[0] == "550":
        return
    if file_size: print(f"ftp: {file_size} bytes received in {elapsed_time:.2f}Seconds {transfer_rate:.2f}Kbytes/sec.")

def delete():
    target_file = ""
    if (len(args) == 1): 
        target_file = input("Remote file ")
    if (len(args) == 2): 
        target_file = args[1]
    
    command_message = f"DELE {target_file}\r\n"
    clientSocket.sendall(command_message.encode())
    message = responseWithEnd().split()
    if message[0] == "550":
        return

def put():
    remote_target = ""
    local_target = ""

    if (len(args) == 1):
        local_target = input("Local file ")
        remote_target = input("Remote file ")
    elif (len(args) == 2):
        local_target = args[1]
        remote_target = args[1].split("\\")[-1]
    elif (len(args) == 3):
        local_target = args[1]
        remote_target = args[2]

    try:
        open(local_target, "rb")
    except:
        return print(f"{local_target}: File not found")
        
    f,s = data_port//256, data_port%256
    port_message = "PORT " + ",".join(clientSocket.getpeername()[0].split("."))+f",{f},{s}\r\n"
    clientSocket.sendall(port_message.encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind((clientSocket.getpeername()[0], data_port))
    data_socket.listen(8)
    
    command_message = f"STOR {remote_target}\r\n"
    clientSocket.sendall(command_message.encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return

    if (not (len(local_target) >= 2 and local_target[1] == ":")):
        local_target = os.getcwd()+"\\"+local_target

    data_conn, addr = data_socket.accept()
    file_size = None
    with open(local_target, "rb") as f:
        start_time = time.time()
        data = f.read(1024)
        file_size = len(data)
        while data:
            data_conn.send(data)
            data = f.read(1024)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if file_size: transfer_rate = (file_size / (elapsed_time if elapsed_time else 1)) * 1000

    data_conn.close()
    data_socket.close()
    message =  responseWithEnd().split()
    if message[0] == "550":
        return
    if file_size: print(f"ftp: {file_size} bytes received in {elapsed_time:.2f}Seconds {transfer_rate:.2f}Kbytes/sec.")

def rename():
    if (len(args) == 1):
        og_name = input("From name ").split()
        if len(og_name) > 1: new_name = og_name[1]
        else: new_name = input("To name ")
        og_name = og_name[0]
    elif (len(args) == 2):
        og_name = args[1]
        new_name = input("To name ")
    elif (len(args) == 3):
        og_name = args[1]
        new_name = args[2]
    elif len(args) >= 4: return print("550 Couldn't open the file or directory")
    
    clientSocket.sendall(f"RNFR {og_name}\r\n".encode())
    message =  responseWithEnd().split()
    if message[0] == "550":
        return
    if message[0] == "350":
        clientSocket.sendall(f"RNTO {new_name}\r\n".encode())
        message2 =  responseWithEnd().split()
        if message2[0] == "550":
            return

def user():
    username = ""
    password = ""
    
    if (len(args) == 1): 
        username = input("Username ")
        clientSocket.sendall(f"USER {username}\r\n".encode())
        message =  responseWithEnd().split()
        if message[0] == "530":
            return print("Login failed.")
        password = input("Password: ")
        
    elif (len(args) == 2):
        username = args[1]
        clientSocket.sendall(f"USER {username}\r\n".encode())
        message =  responseWithEnd().split()
        if message[0] == "530":
            return print("Login failed.")
        password = input("Password: ")
        
    elif (len(args) == 3):
        username = args[1]
        clientSocket.sendall(f"USER {username}\r\n".encode())
        message =  responseWithEnd().split()
        if message[0] == "530":
            return print("Login failed.")
        password = args[2]

    clientSocket.sendall(f"PASS {password}\r\n".encode())
    print('')
    message =  responseWithEnd().split()
    if message[0] == "530":
        return print("Login failed.")

def responseWithEnd():
    resp = clientSocket.recv(1024)
    text_resp = resp.decode()
    print(resp.decode(), end='')
    return text_resp

while True:
    line = ''
    while not line: line = input('ftp> ').strip()
    args = line.split()
    command = args[0]
    command_lst = ['ascii', 'binary', 'bye', 'cd', 'close', 
                    'delete', 'disconnect', 'get', 'ls', 'open', 
                    'put', 'pwd', 'quit', 'rename', 'user']
    
    if command in ['quit', 'bye']:
        if clientSocket:
            disconnect()
        print("")
        break
    
    elif command == 'open':
        if not clientSocket:
            open_func(args)
        else:
            print(f"Already connected to {clientSocket.getpeername()[0]}, use disconnect first.")
    
    elif clientSocket:
        if command in ['disconnect', 'close']:
            disconnect()
            clientSocket = None
        elif command == 'ls':
            ls()
        elif command == 'ascii':
            ascii()
        elif command == 'binary':
            binary()
        elif command == 'pwd':
            pwd()
        elif command == 'cd':
            if len(args) == 1 :
                path = input("Remote directory ").split(' ')
                cd(path[0])
            else: 
                cd(args[1])
        elif command == 'get':
            get()
        elif command == 'delete':
            delete()
        elif command == 'put':
            put()
        elif command == 'rename':
            rename()
        elif command == 'user':
            user()
        else:
            print("Invalid command.")
    elif not clientSocket and command in command_lst:
        print("Not connected.")
    else:
        print("Invalid command.")