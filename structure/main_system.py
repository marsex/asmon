from structure import color
import _thread as th
from time import sleep

def start():
    print('main_system started')
    #th.start_new_thread(start_main_system,(host,port))

def start_main_system(arg1,arg2):
    while True:
        print(color.yellow()+'Start main_system'+color.normal())
        sleep(2)
