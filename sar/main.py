from api.server import SarServer

if __name__ == '__main__':
    from api.panel import sar_panel

    server = SarServer(handler=sar_panel)

    server.start()
