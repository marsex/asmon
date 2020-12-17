import camera
from structure import cam
cam.start()
from structure import machine_data, color, cam, wifi
import network
import socket
import time
import json
import uasyncio as asyncio
from time import sleep
import uerrno
import gc

wifi.connect('1255','12551255')

data_host = "asmon.com.ar"
USER = "espcam"
data_address = ''
cam_address = ''
json_command={}

header = {
    # start page for streaming
    # URL: /apikey/webcam
    'inicio': """HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

$html_file

"""
}
h={
'POST': """POST /$req HTTP/1.1
Host: 127.0.0.1:9515
X-AIO-Key: xxxxxxxxxxxxxxxxxxx
Content-Type: $type
Content-Length: """
}

def start(to):
    try:
        main_loop = asyncio.get_event_loop()  
        main_loop.create_task(sv(to))
        main_loop.run_forever()
    except OSError as e:
        print("async failed"+str(e)) 
    print("async out")   
    gc.collect()
    gc.mem_free()
 
async def sv(to):
    global json_command
    print(color.green()+'STARTING LOCAL SERVER'+color.normal())
    await asyncio.sleep(1)
    port = 80
    ap_localhost = '0.0.0.0'  # get ip addr
    conn_try=0
    while True:
        # try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #s.setblocking(False)
        a = ('0.0.0.0', 80)
        s.bind(a)
        s.listen(2)  # queue at most 2 clients
        print('\nSocket now listening on', str(ap_localhost)+':'+str(port))
        while True:
            try:
                ok = True
                error = ''
                try:
                    print(' in sec NB! default browser timeout (5-15 min)')
                    socket.settimeout(0.05)
                    client, client_address = socket.accept()
                    client.settimeout(0.5)  # in sec
                except Exception as e:
                    error = str(e)

                if error != '':
                    pass
                    ok = False

                if ok:  # No soc.accept timeout
                    error = ''
                    try:
                        print(' client accepted')
                        client_data = client.recv(1024)
                        print('# REQ: b''  # may be due to very short timeout')
                    except Exception as e:
                        error = str(e)

                    if error != '':
                        print(error)
                        ok = False
                    else:
                        client_data = client_data.decode('utf-8')
                        if client_data.find('favicon.ico') < 0:
                            req = client_data.split(' ')
                            try:
                                print(req[0], req[1], client_address)
                            except:
                                ok = False
                        else:
                            print('# handle favicon request early')
                            client.send(b'%s' % hdr['favicon'])
                            clean_up(client)
                            ok = False

                if ok:  # No soc.recv timeout or favicon request
                    try:
                        print('try asyncio port1')
                        asyncio.run(port1(client, req[1]))
                    except Exception as e:
                        error = str(e)
                        if error != '':
                            print(error)
            except Exception as e:
                error = str(e)
                if error != '':
                    print(error)
        print('error????')
        await asyncio.sleep(.1)
        
async def port1(client, req):
    print('port1 req:', req)
    req = req.split('/')
    if req[1] == 'app':  # Must have /apikey/<REQ>
        index_page = create_html()
        html=hdr['html'].replace('$html',index_page)
        client.send(b'%s' % html)
        await asyncio.sleep(.1)
        clean_up(client)
    elif req[1] == 'logo.png':
        client.send(logo_img)
        await asyncio.sleep(.1)
        clean_up(client)
    elif req[1] == ('gpio'):
        pin, value = req[2], req[3]
        
        command_json = {'command': 'output_state', 'data': pin+'='+value}
        machine_data.parse_data(command_json)

        esp_data = machine_data.get()
        gpio_output = esp_data['gpio']['output_state']
        
        json_response = json.dumps({'command':'output_state','output_state': gpio_output})
        json_header = hdr['json'].replace('$len',str(len(json_response)))
        
        client.send(b'%s' % json_header)
        client.sendall(json_response.encode())
        clean_up(client)
    else:
        client.send(b'%s' % hdr['err'])
        clean_up(client)

def clean_up(client):
    client.close()  # flash buffer and close socket
    del client
    gc.collect()


def create_html():
    print('\n\nget_networks')
    scan_list = wifi.get_networks()

    tr_swap = ""
    tr_format = """
    <tr>
        <td onclick="set_ssid(this)">$ssid</td>
        <td class=$signal_state style="width:120px">$signal_state</td>
    </tr>
    """
    if len(scan_list) != 0:
        for wifi_net in scan_list:
            net_signal = int(str(wifi_net[3]).replace('-', ''))
            net_ssid = str(wifi_net[0]).replace("b'", '')
            net_ssid = net_ssid.replace("'", '')
            signal_state = ''
            if net_signal <= 66:
                signal_state = "Excelente"

            if net_signal >= 67:
                signal_state = "Buena"

            if net_signal >= 80:
                signal_state = "Mala"

            tr_done = tr_format.replace('$ssid', net_ssid).replace(
                '$signal_state', signal_state)
            tr_swap = tr_swap + tr_done

    credentials_state, cred_ssid, cred_psw = wifi.get_credentials()
    print(tr_swap)
    gc.collect()
    file = open('/structure/index.html', 'r')
    chtml = file.read()
    chtml = chtml.replace('$tr_swap', tr_swap).replace(
        '$cred_ssid', cred_ssid).replace('$cred_psw', cred_psw)
    file.close()
    return chtml
