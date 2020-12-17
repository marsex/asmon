import nsv, comv3, machine
from structure import wifi, update
from time import sleep

def boot():
    print('\n\nStarting system\n-----------------------')
    wifi.ap_on()
    nsv.start()
    credentials_state, cred_ssid, cred_psw = wifi.get_credentials()

    while credentials_state == False:
        print('Getting credentials...')
        credentials_state, cred_ssid, cred_psw = wifi.get_credentials()
        sleep(1)
        pass

    sleep(1)

    wifi_connected = wifi.connect(cred_ssid, cred_psw)

    while wifi_connected == False:
        print("WIFI not ready. Wait...")
        sleep(1)
        pass

    print('Connection successful\n')
    print('Check for updates')
    if update.check('sys_info')[0] == True:
        print('\nSystem OUTDATED')
        update.system()
        print('\nSystem UPDATED')
        print('\nRestarting system\n-----------------------\n\n')
        machine.reset()
    else:
        print('\nSystem up to date\nStart system')
        comv3.start(10)
