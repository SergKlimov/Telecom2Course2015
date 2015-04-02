#import email
from email.parser import FeedParser
import errno
import re
import socket

try:
    import ssl
    HAVE_SSL = True
except ImportError:
    HAVE_SSL = False

POP3_PORT = 110
POP3_SSL_PORT = 995
CR = b'\r'
LF = b'\n'
CRLF = CR+LF

_MAXLINE = 2048



class POP3:

    encoding = 'UTF-8'

    def __init__(self, host, port=POP3_PORT,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.sock = self._create_socket(timeout)
        self.file = self.sock.makefile('rb')
        self.welcome = self._getresp()

    def _create_socket(self, timeout):
        return socket.create_connection((self.host, self.port), timeout)

    def _putline(self, line):
        self.sock.sendall(line + CRLF)

    def _putcmd(self, line):
        line = bytes(line, self.encoding)
        self._putline(line)

    def _getline(self):
        line = self.file.readline(_MAXLINE + 1)
        octets = len(line)
        return line[:-2], octets

    def _getresp(self):
        resp, o = self._getline()
        print('resp from server: ' + str(resp))
        return resp

    def _getlongresp(self):
        resp = self._getresp()
        list = []; octets = 0
        line, o = self._getline()
        while line != b'.':
            if line.startswith(b'..'):
                o = o-1
                line = line[1:]
            octets = octets + o
            list.append(line)
            line, o = self._getline()
        return resp, list, octets

    def _shortcmd(self, line):
        self._putcmd(line)
        return self._getresp()

    def _longcmd(self, line):
        self._putcmd(line)
        return self._getlongresp()

    def user(self, user):
        return self._shortcmd('USER %s' % user)


    def pass_(self, pswd):
        return self._shortcmd('PASS %s' % pswd)


    def stat(self):
        retval = self._shortcmd('STAT')
        rets = retval.split()
        numMessages = int(rets[1])
        sizeMessages = int(rets[2])
        return (numMessages, sizeMessages)


    def list(self, which=None):
        if which is not None:
            return str(self._shortcmd('LIST %s' % which))
        return self._longcmd('LIST')

    def retr(self, which):
        return self._longcmd('RETR %s' % which)

    def dele(self, which):
        return self._shortcmd('DELE %s' % which)

    def rset(self):
        return self._shortcmd('RSET')


    def quit(self):
        resp = self._shortcmd('QUIT')
        self.close()
        return resp

    def close(self):
        if self.file is not None:
            self.file.close()
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno != errno.ENOTCONN:
                    raise
            finally:
                self.sock.close()
        self.file = self.sock = None

    timestamp = re.compile(br'\+OK.*(<[^>]+>)')

    def top(self, which, howmuch):
        return self._longcmd('TOP %s %s' % (which, howmuch))

    def uidl(self, which=None):
        if which is not None:
            return self._shortcmd('UIDL %s' % which)
        return self._longcmd('UIDL')

    def print_message(self, num):
        tmp = Mailbox.retr(num)
        print('qq')
        for i in tmp:
            print(str(i))
        raw = str(tmp[1])
        mes = raw.split(',')
        l = len(mes)
        message = mes[l-7]
        print ('Message:' + str(message)[3:-1])

    def print_message1(self):
        num = input('enter num of msg: ')
        tmp = Mailbox.retr(num)
        for i in tmp:
            print(str(i))
        raw = str(tmp[1])
        mes = raw.split(',')
        l = len(mes)
        message = mes[l-7]
        if str(message)[3:-1] != 'Content-Transfer-Encoding: 7bit':
            print ('Message:' + str(message)[3:-1])
        else:
            message = mes[l-2]
            print ('Message:' + str(message)[3:-1])

    def print_stat(self):
        num,size=self.stat()
        print('num=%s, szie=%s' % (str(num), str(size)))
    def print_list(self):
        num = input('enter num of msg or press enter: ')
        if num == '':
            r,l,o=self.list()
            for i in l:
                print(str(i))
        else:
            r = self.list(int(num))
            print(r)

    def print_top(self):
        msg = input('number of msg:')
        num = input('number of rows:')
        r,l,o=self.top(int(msg),int(num))
        print('%s' % (str(l)))
    def print_uidl(self):
        num = input('enter num of msg or press enter: ')
        if num == '':
            r,l,o=self.uidl()
            for i in l:
                print('%s' % str(i))
        else:
            r=self.uidl(int(num))
            print(r)

    def send_user(self):
        userresp = ''
        while not userresp.startswith('b\'+OK'):
            user = input('Enter your login:')
            if user == '1':
                userresp = str(self.user('sergklimoff'))
            else:
                userresp = str(self.user(user))

    def send_pass(self):
        passresp = ''
        while not passresp.startswith('b\'+OK'):
            passwd = input('Enter your password:')
            if passwd == '1':
                passresp = str(self.pass_('KlimovSergey'))
            else:
                passresp = str(self.pass_(passwd))

    def uni_cmd(self):
        self.user('sergklimoff')
        self.pass_('KlimovSergey')

    def del_msg(self):
        num = input('Enter number of msg: ')
        self.dele(int(num))

if HAVE_SSL:

    class POP3_SSL(POP3):

        def __init__(self, host, port=POP3_SSL_PORT, keyfile=None, certfile=None,
                     timeout=socket._GLOBAL_DEFAULT_TIMEOUT, context=None):
            if context is not None and keyfile is not None:
                raise ValueError("context and keyfile arguments are mutually "
                                 "exclusive")
            if context is not None and certfile is not None:
                raise ValueError("context and certfile arguments are mutually "
                                 "exclusive")
            self.keyfile = keyfile
            self.certfile = certfile
            if context is None:
                context = ssl._create_stdlib_context(certfile=certfile,
                                                     keyfile=keyfile)
            self.context = context
            POP3.__init__(self, host, port, timeout)

        def _create_socket(self, timeout):
            sock = POP3._create_socket(self, timeout)
            sock = self.context.wrap_socket(sock,
                                            server_hostname=self.host)
            return sock

if __name__ == "__main__":

    serv = input('Enter pop server:')
    if serv == '1':
        serv = 'pop.yandex.ru'
    port = input('Enter pop port:')
    if port == '1':
        port = '995'
    #Mailbox = POP3_SSL('pop.yandex.ru', '995')
    #cmds = ['stat','list','retr','dele','top','uidl','rset','quit']
    Mailbox = POP3_SSL(serv, port)
    cds = {
        'uni' : Mailbox.uni_cmd,
        'user' : Mailbox.send_user,
        'pass' : Mailbox.send_pass,
        'stat' : Mailbox.stat,
        'retr' : Mailbox.print_message1,
        'list' : Mailbox.print_list,
        'top' : Mailbox.print_top,
        'uidl' : Mailbox.print_uidl,
        'quit' : Mailbox.quit,
        'dele' : Mailbox.del_msg,
        'rset' : Mailbox.rset,
        }
    cmd = ''

    while cmd != 'quit':
        cmd = input('Enter cmd:')
        if cmd in cds:
            cds[cmd]()
        else:
            print('Wrong cmd!')