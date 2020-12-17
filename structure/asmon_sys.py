from structure import update, color, machine_data, cam
from structure import urequests as requests
import _thread
import socket
import uerrno
import ujson
import json
import gc
from machine import Pin
from time import sleep
th = _thread.start_new_thread

json_command = {}
def start():
    print(color.yellow()+'\n Starting asmon_system')
    #server_list = get_server_list()
    #host, port = ['asmon.com.ar','8080'] #server_list[0].split(':')
    host = 's'
    h1 = "http://asmon.com.ar:8080/esp_data/dev_cam01"
    h2 = "http://asmon.com.ar:8081/snap/dev_cam01"
    
    if host != 'null':
        print(color.green()+'\nStart server communication\n'+color.normal())
        try:
            th(plus,(h1,h2,))
            #th.start_new_thread(start_com, (data_address,cam_address,))
        except:
            print(color.red()+'Error starting com thread'+color.normal())
    else:
        print(color.red()+'Error starting asmon_system'+color.normal())


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

def plus(h1,h2):
    global json_command
    print(color.yellow()+'\n Starting CAM+DATA_SYSTEM:')
    pic = cam.frame_gen()
    new_json_command = {}
    
    data_host=h1
    cam_host=h2
    print('data_host:',data_host)
    print('cam_host:',cam_host)
    while True:
        e=''
        url = data_host
        headers = {'X-AIO-Key': 'xxxxxxxxxxxxxxxxxxx',
                   'Content-Type': 'application/json'}
        data = json.dumps(machine_data.get())

        while True:
            try: 
                r = requests.post(url, data=data, headers=headers)
                new_json_command = r.json()
                if json_command != new_json_command:
                    json_command = new_json_command
                    print(json_command)
            except:
                e=''
            break
        
        url = cam_host
        headers = {'X-AIO-Key': 'xxxxxxxxxxxxxxxxxxx',
                    'Content-Type': 'image/jpeg'}
        while True:
            try:
                data = next(pic)
                r = requests.post(url, data=data, headers=headers)
                results = r.json()
            except:
                e=''
            break
    gc.collect()
    sleep(.1)