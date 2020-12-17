import network
import socket
import gc
from time import sleep
from structure import machine_data, wifi
import _thread
th_new = th.start_new_thread

red = ("\033[1;31;40m")
green = ("\033[1;32;40m")
yellow = ("\033[1;33;40m")
blue = ("\033[1;34;40m")
normal = ("\033[0;37;40m")

header = {
    # start page for streaming
    # URL: /apikey/webcam
    'inicio': """HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

$html_file

"""
}


def start():
    # th_new(ap_server,())
    th_new(st_server, ())
    return '\n\nOFFLINE System Running\n\n'


def st_server():
    print(blue+'\n\nStarting ST Server\n-----------------------')
    print('Check WiFi credentials\n')
    credentials_state, cred_ssid, cred_psw = wifi.get_credentials()

    while credentials_state == False:
        print('Getting credentials...')
        credentials_state, cred_ssid, cred_psw = wifi.get_credentials()
        sleep(1)
        pass

    print(green+'Got WiFi credentials\n')
    wifi_connected = wifi.connect(cred_ssid, cred_psw)

    while wifi_connected == False:
        print("WIFI not ready. Wait...")
        sleep(2)
        pass

    print(green+'Connection successful\n')

    while True:
        port = 80
        wlan_ip = network.WLAN(network.STA_IF).ifconfig()[0]

        st_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        st_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        st_socket.bind((wlan_ip, port))
        st_socket.listen(2)
        print('\nSocket now listening on', str(wlan_ip)+':'+str(port))
        while True:
            gc.collect()
            client, address = st_socket.accept()

            ip, port = str(address[0]), str(address[1])
            print('\n{')
            print(green+'Connection from ' + ip + ':' + port)
            try:
                th_new(handle_client, (client, ip, port))
            except:
                print('error creating handle_client thread')
        st_socket.close()
        print('st_socket closed')


def ap_server():
    print('\n\nStarting AP System\n\n')
    while True:
        port = 80
        ap_wlan = network.WLAN(network.AP_IF)
        ap_wlan.active(True)
        ap_wlan.config(essid='ASMON AP System')
        ap_wlan.config(authmode=3, password='12551255')
        ap_localhost = ap_wlan.ifconfig()[0]  # get ip addr

        ap_socket = socket.socket()  # create socket
        ap_socket.bind((ap_localhost, port))  # bind ip and port
        ap_socket.listen(2)  # listen message
        ap_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        print('\nSocket now listening on', str(ap_localhost)+':'+str(port))
        while True:
            gc.collect()
            client, address = ap_socket.accept()

            ip, port = str(address[0]), str(address[1])
            print('\n{')
            print(green+'  Connection from ' + ip + ':' + port)

            th_new(handle_client, (client, ip, port))
        ap_socket.close()


def handle_client(client, ip, port):
    MAX_BUFFER_SIZE = 69
    print('\n\nParsing data from ' + ip + ':' + port)
    input_from_client_bytes = client.readline()  # client.recv(MAX_BUFFER_SIZE)
    line = input_from_client_bytes
    print('data size:', len(input_from_client_bytes))
    while True:
        data = str(input_from_client_bytes)
        send_html = data.find('GET / HTTP/1.1')
        write_img = data.find('GET /logo.png')
        data_com = data.find('@data_com')
        get_credentials = data.find('@credentials:')
        output_state = data.find('@output_state:')
        end_data = data.find('@end')

        if send_html != -1:
            html_file = create_html()
            print('gotem')
            # client.sendall(response)
            client.send(b'%s' % header['inicio'].replace(
                '$html_file', html_file))
            print(data)
            break

        if write_img != -1:
            print('write logo')
            imOpen = open('/structure/logo.png')
            image = imOpen.read()
            imOpen.close()
            client.write(image)
            print(data)
            break

        if get_credentials != -1:
            print('Found credentials')
            c_data = data[get_credentials+len('@credentials:'): end_data]
            wifi.set_credentials(c_data)
            response = com_data.replace('$machine_data', '@credentials_saved')
            client.send(response)
            print(data)
            break

        if output_state != -1:
            print('Found output command')

            c_data = data[output_state+len('@output_state:'): end_data]
            command_json = {'command': 'output_state', 'update': c_data}
            machine_data.parse_data(command_json)

            esp_data = machine_data.get()
            gpio_output = esp_data['gpio']['output_state']
            json_response = {'output_state': gpio_output}
            response = com_data.replace('$machine_data', str(json_response))

            client.sendall(response)
            print(data)
            break
    clean_up(client)
    gc.collect()
    print(red + 'Connection ' + ip + ':' + port + ' ended\n'+normal+'}\n')


def clean_up(client):
    client.close()  # flash buffer and close socket
    del client


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


def send_json(client, data_json):
    import json
    data_json = json.dumps(data_json)
    response_headers = {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json','Content-Length': len(data_json),'Connection': 'close',}
    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
    response_proto = 'HTTP/1.1'
    response_status = '200'
    response_status_text = 'OK'
    r = '%s %s %s\r\n' % (response_proto, response_status,response_status_text)

    client.send(r.encode())
    client.send(response_headers_raw.encode())
    client.send('\r\n'.encode())  # to separate headers from body
    client.sendall(data_json.encode())


machine_data.create()
html = create_html()

com_data = """
<html>
    <input id="esp_data" style="padding: 8px 8px; display: block;width: 93.6%;" value="$machine_data" disabled>
    <script>
        machine_data = document.getElementById('esp_data').value;
        window.parent.document.getElementById('esp_data').value = machine_data; 
    </script>
</html>
"""
