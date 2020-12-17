from structure import update, color, machine_data, sock_state
sset = sock_state.set
sget = sock_state.get
import _thread as th
import socket
import uerrno
import ujson
import json
from machine import Pin
from time import sleep
import gc

h={
'POST': """POST /$req HTTP/1.1
Host: 127.0.0.1:9515
Content-Type: $type
Content-Length: """
}

def start():
    print(color.yellow()+'\n Starting asmon_system')
    #server_list = get_server_list()
    host, port = ['asmon.com.ar','8080'] #server_list[0].split(':')
    if host != 'null':
        print(color.green()+'\nStart server communication\n' +
              'IP:', host, '\nPORT:', port+'\n'+color.normal())
        try:
            address = socket.getaddrinfo(host, port)[0][-1]
            print(address)
            th.start_new_thread(start_com, (address,))
        except:
            print(color.red()+'Error getting addr info from', host, port)
    else:
        print(color.red()+'Error starting asmon_system')


def get_server_list():
    server_request = update.read_remote(
        'server_list', 'https://raw.githubusercontent.com/marsex/asmon_structure/master/')
    try:
        server_list = server_request.text.split(',')
        i = 0
        for server in server_list:
            print('Server #'+str(i)+':', server)
            i = i + 1
        return server_list
    except:
        return ['null:null']


def start_com(address):
    json_data = machine_data.create()
    while True:
        print(color.green()+'Check cam_socket')
        cam_state = sget('cam')
        while cam_state != 'socket_closed':
            cam_state = sget('cam')
            sleep(.05)
            pass
        print(color.green()+'cam_socket disconnected')
        try:
            sset('com','creating_socket')
            client_socket = socket.socket()
            print(color.normal()+'{')
            client_socket.setblocking(0)
            try:    
                print(color.green()+'{\n\tConnect to',"asmon.com.ar:" , 8080)
                sset('com','connecting')
                client_socket.connect(address)
                print('\t\t{\n\t\t\tSending data')
                POST(client_socket, 'esp_data/dev_cam01', 'json',machine_data.get())
                print('\t\t\tData Sent\n\t\t\t{')
                print('\t\t\t\tWait for response')  
                
                sleep(0.2)
                buffer_data = client_socket.recv(1024)
                while (len(buffer_data) > 0):
                    print(buffer_data)
                    print(color.blue()+'\t\t\t\tGot response')
                    break
                connection = True
            except Exception as error:
                client_socket.close()
                connection = False
                print(color.red()+'\t\t\t**** ERROR Connecting ****\n\t\t\t', error)
                
            client_socket.close()  # flash buffer and close socket
            del client_socket
            sset('com','socket_closed')
        except:
            print('failed to create socket')
        
        gc.collect()
        print(color.red()+'\t\t\t}')
        print(color.normal()+'\t\t}')
        print(color.normal()+'\t}\n')
        print('}')
        sleep(.5)


def POST(s, req, type, data):
    size = 0
    if type == 'json':
        type = 'application/json'
        data = json.dumps(data)
        size = len(data)
        data = data.encode()
        header = h['POST'].replace('$req',req).replace('$type',type)

    s.send(b'%s %d\r\n\r\n' % (header, size))
    s.send(data)
    s.send(b'\r\n')