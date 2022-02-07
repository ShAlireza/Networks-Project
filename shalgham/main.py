from api.server import ShalghamServer

if __name__ == '__main__':
    from api.handler import ShalghamHandler

    server = ShalghamServer(handler_class=ShalghamHandler)

    server.start()