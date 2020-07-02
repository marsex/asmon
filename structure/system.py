from structure import update, color, machine_data, main_system, asmon_system
import uerrno

def start():
  try:
    print('Start asmon_system')
    asmon_system.start()
  except:
    print('ERROR starting asmon_system')
    
  try:
    print('Start main_system')
    main_system.start()
  except:
    print('ERROR starting main_system')