import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
from PIL import Image
from io import BytesIO
import base64
from printer import PrintOrder
import printer


# Defines the webservice handler
class WSHandler(tornado.websocket.WebSocketHandler):

    def data_received(self, chunk):
        pass

    def check_origin(self, origin):
        return True

    def open(self):
        print('user is connected.\n')

    def on_message(self, message):
        image = Image.open(BytesIO(base64.b64decode(message)))
        print_order = PrintOrder(printer.print_image, image)
        printer.queue.put(print_order)

        self.write_message('Printing image...')
        print('printing image...\n')

    def on_close(self):
        print('connection closed\n')


# Starts webservice

def run_webservice():
    application = tornado.web.Application([(r'/ws', WSHandler), ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    