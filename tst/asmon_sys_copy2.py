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
json_command = {}
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
    global json_command
    json_data = machine_data.create()
    while True:
        cam_state = sget('com')
        if cam_state == 'socket_closed':
            sset('com','busy')
            try:
                client_socket = socket.socket()
                client_socket.setblocking(False)
    
                try:    
                    client_socket.connect(address)
                except OSError as error:
                  if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                    print(color.red()+'**** Error connecting ****', error, color.normal())
                
                try:
                    POST(client_socket, 'esp_data/dev_cam01', 'json',machine_data.get())         
                    while True:
                        res = str(client_socket.recv(2000))
                        if res.find('200 OK') != -1:
                            command = str(res)[str(res).find('\\r\\n\\r\\n')+len('\\r\\n\\r\\n'):len(str(res))-1]
                            new_json_command = ujson.loads(command)
                            if json_command != new_json_command:
                                json_command = new_json_command
                                print(json_command)
                        break    
                except OSError as error:
                    if error.args[0] not in [uerrno.EINPROGRESS, uerrno.ETIMEDOUT]:
                        print(color.red()+'\t\t\t**** ERROR writing ****\n\t\t\t', error, color.normal())

                client_socket.close()  # flash buffer and close socket
                del client_socket
                gc.collect()
            except OSError as error:
                print(color.red()+'\t\t\t**** ERROR creating socket ****\n\t\t\t', error, color.normal())
        sset('com','socket_closed')
        sleep(.1)


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