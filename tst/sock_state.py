sock_state = {'cam':'socket_closed','com':'socket_closed'}

def get(sock):
    return sock_state[sock]
    
def set(sock,status):
    global sock_state
    sock_state[sock] = status
