from api.server import ProxyServer

if __name__ == '__main__':
    from api.handler import ProxyHandler

    server = ProxyServer(handler_class=ProxyHandler)

    server.start()
