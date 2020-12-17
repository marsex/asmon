def test():
    try:
        socket.connect()
    except:
        print('failed')
        return