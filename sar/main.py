from api.server import SarServer

if __name__ == '__main__':
    from api.panel import SarPanel

    server = SarServer(handler_class=SarPanel)

    server.start()
