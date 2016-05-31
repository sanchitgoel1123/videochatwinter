#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
import tornado.httpserver
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
import momoko
import psycopg2
import urlparse
import base64


rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
        self.render('index.html')


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    
    def post(self):
        self.set_secure_cookie("user",self.get_argument("name"))
        self.redirect("/")



class EchoWebSocket(WebSocketHandler):
    clients = []

    def open(self):
        logging.info('WebSocket opened from %s', self.request.remote_ip)
        EchoWebSocket.clients.append(self)

    def on_message(self, message):
        logging.info('got message from %s: %s', self.request.remote_ip, message)
        for client in EchoWebSocket.clients:
            if client is self:
                continue
            client.write_message(message)

    def on_close(self):
        logging.info('WebSocket closed')
        EchoWebSocket.clients.remove(self)


def main():


    #tornado.ioloop.IOLoop.instance().start()
    #options.parse_command_line()

    settings = dict(
        template_path=rel('templates'),
        static_path=rel('static'),
        cookie_secrets=base64.b64encode(os.urandom(50)).decode('ascii'),
        #xsrf_cookies=True,
        #debug=options.debug
    )
    
    application = Application([
        (r'/', MainHandler),
        (r'/ws', EchoWebSocket),
        (r'/login',LoginHandler),
    ], **settings)

    ioloop = IOLoop.instance()
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    application.db = momoko.Pool(
        dsn='dbname=url.path[1:] user=url.username password=url.password'
        'host=url.hostname port=url.port',
        size=1,
        ioloop=ioloop
        )
    future = application.db.connect()

    http_server = tornado.httpserver.HTTPServer(application)
    port = int(os.environ.get("PORT", 5000))
    #define('debug', metavar='True|False', default=False, type=bool, 
    #    help='enable Tornado debug mode: templates will not be cached '
    #    'and the app will watch for changes to its source files '
    #    'and reload itself when anything changes')
    http_server.listen(port)
    
    #application.listen(address=options.listen, port=options.port)
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
