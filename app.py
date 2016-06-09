#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import base64
import uuid
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
import tornado
import momoko
import psycopg2
import hashlib
from passlib.apps import custom_app_context as pwd_context
import urlparse
from tornado import gen
import datetime

rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

class BaseHandler(RequestHandler):
    @property
    def db(self):
        return self.application.db
    
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_logged_in(self):
        return self.get_secure_cookie("keeplogged")


class MainHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.current_user is None and not self.current_user:
            self.redirect("/login")
        else:
            email = self.current_user
            sqlstm = "select loggedin from loggedinuser where email='%s';"%(email)
            check = self.db.execute(str(sqlstm))
            yield check
            print ("Executed Query in MainHandler.get(): %s" % (sqlstm))
            sys.stdout.flush()
            ans = check.result()
            checkagainst = ans.fetchone()
            sys.stdout.flush()
            if checkagainst is not None and not checkagainst[0]:
                self.redirect('/login')
            else:
                try:
                    sqlstm = "update loggedinuser set lastloggedin=now(),loggedin=true where email='%s';"%(email)
                    yield self.db.execute(str(sqlstm))
                    print ("Executed Query in MainHandler.get(): %s" % (sqlstm))
                    sys.stdout.flush()
                    self.render('index.html')
                except:
                    print "Error in Block MainHandler"
                    sys.stdout.flush()


class LoginHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render('login.html',msg={ })
    
    @gen.coroutine
    def post(self):
        email = self.get_argument('email')
        password = self.get_argument('password')
        self.set_secure_cookie("keeplogged", self.get_argument('keeplogged'))
        print self.get_argument('keeplogged')
        if not password or not email:
            errormsg = "No Password or User Entered"
            msg = { }
            msg['errormsg'] = errormsg
            self.render('login.html', msg=msg)
        else:
            sqlstm="select email,salt,password from usercredentials where email='%s';"%(email)
            check = self.db.execute(str(sqlstm))
            yield check
            print ("Executed Query in LoginHandler.post(): %s" % (sqlstm))
            sys.stdout.flush()
            ans = check.result()
            checkagainst = ans.fetchone()
            if checkagainst is not None:
                flag = pwd_context.verify(checkagainst[1]+password, checkagainst[2])
                if flag is True:
                    self.set_secure_cookie("user",email)
                    print ("User %s logged in %s in LoginHandler.post()"%(email,datetime.datetime.now()))
                    sqlstm="update loggedinuser set lastloggedin=now(),loggedin=true where email='%s';"%(email)
                    yield self.db.execute(str(sqlstm))
                    print ("Executed Query in LoginHandler.post(): %s" % (sqlstm))
                    sys.stdout.flush()
                    self.redirect('/')
                else:
                    errormsg = "Invalid Email Or Password"
                    msg = {}
                    msg['errormsg']=errormsg
                    self.render('login.html',msg=msg)
            else:
                errormsg = "Invalid Email Or Password"
                msg = {}
                msg['errormsg']=errormsg
                self.render('login.html',msg=msg)


class RegisterHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        msg = {}
        self.render('register.html',msg=msg)

    @gen.coroutine
    def post(self):
        emailid=self.get_argument('email')
        firstname=self.get_argument('First_Name')
        lastname=self.get_argument('Last_Name')
        dob=self.get_argument('dob')
        password1=self.get_argument('password')
        password2=self.get_argument('renter_password')
        if (password1!=password2):
            errormsg="Passwords Dont Match"
            msg = { }
            msg['errormsg'] = errormsg
            self.render('register.html', msg=msg)
        elif not password1 or not emailid or dob == "Date Of Birth":
            errormsg="Fields Cannot Be Empty"
            msg = { }
            msg['errormsg'] = errormsg
            self.render('register.html', msg=msg)
        else:
            salt  = base64.urlsafe_b64encode(uuid.uuid4().bytes)
            hashed_password =  pwd_context.encrypt(salt+password1)
            sqlstm = "insert into usercredentials values (%s,%s,%s,%s,%s,%s);"
            check = "select email from usercredentials where email='%s';"%(emailid)
            logging.info(str(check))
            x = self.db.execute(check)
            y = yield x
            print ("Executed Query in RegisterHandler.post(): %s" % (check))
            sys.stdout.flush()
            x = y.fetchone()
            logging.info(x is not None)
            if (x is not None):
                errormsg="User Already Exists"
                msg = {}
                msg['errormsg'] = errormsg
                self.render('register.html', msg=msg)
            else:
                try:
                    yield self.db.execute(str(sqlstm),(firstname,lastname,emailid,hashed_password,salt,dob))
                    print ("Executed Query in RegisterHandler.post(): %s" % ("insert into usercredentials values (%s,%s,%s,%s,%s,%s);"%(firstname,lastname,emailid,hashed_password,salt,dob)))
                    sys.stdout.flush()
                    self.set_secure_cookie("user", emailid)
                    self.set_secure_cookie("keeplogged",str(0))
                    print "User %s registered %s in RegisterHandler.post()"%(emailid,datetime.datetime.now())
                    sys.stdout.flush()
                    self.redirect('/')
                except:
                    self.write(str(error))
                    errormsg="Database Error.Please Try Later"
                    msg = { }
                    msg['errormsg'] = errormsg
                    self.redirect('/register')
        

class EchoWebSocket(WebSocketHandler,BaseHandler):
    clients = []

    def open(self):
        EchoWebSocket.clients.append(self)

    def on_message(self, message):
        print ('Got message from %s: %s', self.__dict__, message)
        for client in EchoWebSocket.clients:
            if client is self:
                continue
            client.write_message(message)

    @gen.coroutine
    def on_close(self):
        email = self.current_user
        flag = self.get_secure_cookie("keeplogged")
        sqlstm="update loggedinuser set loggedin=false where email='%s';"%(str(email))
        if flag is not None and not bool(int(flag)) and email is not None:
            yield self.db.execute(str(sqlstm))
            print ("Executed Query in EchoWebSocket.on_close(): %s" % (sqlstm))
            print "User %s left %s in EchoWebSocket.on_close()"%(email,datetime.datetime.now())
            sys.stdout.flush()
        else:
            sqlstm="update loggedinuser set loggedin=true where email='%s';"%(str(email))
            yield self.db.execute(str(sqlstm))
            print ("Executed Query in EchoWebSocket.on_close(): %s" % (sqlstm))
            print "User %s left %s in EchoWebSocket.on_close()"%(email,datetime.datetime.now())
            sys.stdout.flush()
        EchoWebSocket.clients.remove(self)



def main():
    settings = dict(
        template_path=rel('templates'),
        static_path=rel('static'),
        cookie_secret=u'6s+CeN4uMGFyEsRL6SNloaC1vql99xKbIWJaQYSYjMNoZDbDirZxbCUq5qQZdP7S+GM=',
        login_url='/login',
        xsrf_cookies=True,
        debug=False,
    )
    
    application = Application([
        (r'/', MainHandler),
        (r'/ws', EchoWebSocket),
        (r'/login',LoginHandler),
        (r'/register',RegisterHandler),
    ], **settings)

    ioloop = IOLoop.instance()
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    dsn = "dbname='%s' user='%s' password='%s' host='%s' port='%s'"%( url.path[1:], url.username, url.password, url.hostname, url.port)
    application.db = momoko.Pool(
        dsn=dsn,
        size=1,
        ioloop=ioloop
        )
    future = application.db.connect()
    ioloop.add_future(future, lambda f: ioloop.stop())
    ioloop.start()
    future.result()
    port = int(os.environ.get("PORT", 5000))
    application.listen(port)
    ioloop.start()


if  __name__ == '__main__':
    main()
