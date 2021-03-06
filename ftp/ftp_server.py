import os,socket,threading,time,sys, logging

allow_delete = False
local_ip = socket.gethostbyname(socket.gethostname())
#local_ip = '188.243.23.120'
local_port = 21
#currdir=os.path.abspath('.')
currdir='D:/common_linux/'

class FTPserverThread(threading.Thread):
    def __init__(self,conn,addr):
        self.conn=conn
        self.addr=addr
        self.basewd=currdir
        self.cwd=self.basewd
        self.rest=False
        threading.Thread.__init__(self)
        self.mode = ''
        self.users = {}
        self.user = ''
        logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(message)s', level = logging.DEBUG, filename = u'mylog.log')
        #print(os.path.abspath('.'))

    def run(self):
        self.load_usrs()
        self.conn.send(bytes('220 Welcome!\r\n', 'UTF-8'))
        while True:
            cmd=self.conn.recv(256)
            logging.info(cmd)
            if not cmd: break
            else:
                #print ('Recieved:',cmd)
                pr1 = cmd[:4].decode('UTF-8')
                pr2 = pr1.strip()
                pr = pr2.upper()
                #print('__%s__' % str(pr))
                func = getattr(self, pr)
                func(cmd)

    def load_usrs(self):
        f = open('users.cfg','r')
        for line in f:
            self.users[line.split(" ")[0]] = line.split(" ")[1]

    def check_user(self,usrnm):
        for i in self.users:
            if i == usrnm:
                self.user = usrnm
                return True
        return False

    def check_pass(self,paswd):
        if self.users[self.user] == paswd:
            return True
        else:
            return False

    def SYST(self,cmd):
        self.conn.send(bytes('215 UNIX Type: L8\r\n', 'UTF-8'))
    def USER(self,cmd):
        if cmd.decode('UTF-8').split(" ")[1].split("\r\n")[0] == 'anonymous':
            self.user = 'anonymous'
            self.conn.send(b'331 OK.\r\n')
        elif self.check_user(cmd.decode('UTF-8').split(" ")[1].split("\r\n")[0]):
            self.conn.send(b'331 OK.\r\n')
        else:
            self.conn.send(b'530 Login is incorrect\r\n')

    def FEAT(self,cmd):
        self.conn.send(bytes('211 OK.\r\n', 'UTF-8'))
    def PASS(self,cmd):
        if self.user == 'anonymous':
            self.conn.send(b'230 OK.\r\n')
        else:
            if self.check_pass(cmd.decode('UTF-8').split(" ")[1].split("\r\n")[0]+'\n'):
                self.conn.send(b'230 OK.\r\n')
            else:
                self.conn.send(b'530 Password is incorrect\r\n')

    def QUIT(self,cmd):
        self.conn.send(bytes('221 Goodbye.\r\n', 'UTF-8'))
    def TYPE(self,cmd):
        self.mode=cmd[5]
        self.conn.send(bytes('200 Binary mode.\r\n', 'UTF-8'))

    def CDUP(self,cmd):
        if not os.path.samefile(self.cwd,self.basewd):
            self.cwd=os.path.abspath(os.path.join(self.cwd,'..'))
        self.conn.send(bytes('200 OK.\r\n', 'UTF-8'))
    def PWD(self,cmd):
        cwd = 'D:/common_linux/'
        cwd = self.cwd
        self.conn.send(bytes('257 \"%s\"\r\n' % cwd, 'UTF-8'))
    def CWD(self,cmd):
        chwd=cmd[4:-2]
        print('__%s__' % chwd)
        nf = chwd.decode('UTF-8')
        print('new: %s' % nf)
        chwd = nf
        if chwd=='D:/':
            self.cwd=self.basewd
        elif chwd[0]=='/':
            self.cwd=os.path.join(self.basewd,chwd[1:])
        else:
            self.cwd=os.path.join(self.cwd,nf)
        self.conn.send(bytes('250 OK.\r\n', 'UTF-8'))

    def PASV(self,cmd):
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.servsock.bind((local_ip,0))
        self.servsock.listen(1)
        ip, port = self.servsock.getsockname()
        print ('open', ip, port)
        self.conn.send(bytes('227 Entering Passive Mode (%s,%u,%u).\r\n' %
                (','.join(ip.split('.')), port>>8&0xFF, port&0xFF),'UTF-8'))

    def start_datasock(self):
        self.datasock, addr = self.servsock.accept()
        print ('connect:', addr)

    def stop_datasock(self):
        self.datasock.close()
        self.servsock.close()

    def LIST(self,cmd):
        self.conn.send(bytes('150 Here comes the directory listing.\r\n','UTF-8'))
        print ('list:', self.cwd)
        self.start_datasock()
        for t in os.listdir(self.cwd):
            k=self.toListItem(os.path.join(self.cwd,t))
            self.datasock.send(bytes(k+'\r\n','UTF-8'))
        self.stop_datasock()
        self.conn.send(bytes('226 Directory send OK.\r\n','UTF-8'))

    def NLST(self,cmd):
        self.LIST(cmd)

    def toListItem(self,fn):
        st=os.stat(fn)
        fullmode='rwxrwxrwx'
        mode=''
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        d=(os.path.isdir(fn)) and 'd' or '-'
        ftime=time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime))
        return d+mode+' 1 user group '+str(st.st_size)+ftime+os.path.basename(fn)

    def MKD(self,cmd):
        dn=os.path.join(self.cwd,cmd[4:-2])
        os.mkdir(dn)
        self.conn.send('257 Directory created.\r\n')

    def RMD(self,cmd):
        dn=os.path.join(self.cwd,cmd[4:-2])
        if allow_delete:
            os.rmdir(dn)
            self.conn.send('250 Directory deleted.\r\n')
        else:
            self.conn.send('450 Not allowed.\r\n')

    def DELE(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        if allow_delete:
            os.remove(fn)
            self.conn.send('250 File deleted.\r\n')
        else:
            self.conn.send('450 Not allowed.\r\n')

    def RETR(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2].decode('UTF-8'))
        #fn=os.path.join(self.cwd,cmd[5:-2]).lstrip('/')
        print ('Downlowding:',fn)
        if self.mode=='I':
            #fi=open(fn,'rb')
            fi=open(fn,'rb',encoding="UTF-8")
        else:
            #fi=open(fn,'r')
            fi=open(fn,'rb')
        #print('en: %s' % fi.encoding)
        self.conn.send(bytes('150 Opening data connection.\r\n','UTF-8'))
        if self.rest:
            fi.seek(self.pos)
            self.rest=False
        try:
            data= fi.read(1024)
        except Exception as e:
            print('Error: ',e)
        self.start_datasock()
        while data:
            self.datasock.send(data)
            data=fi.read(1024)
        fi.close()
        self.stop_datasock()
        self.conn.send(bytes('226 Transfer complete.\r\n','UTF-8'))

    def STOR(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2].decode())
        print ('Uplaoding:',fn)
        if self.mode=='I':
            fo=open(fn,'wb')
        else:
            fo=open(fn,'wb')
        self.conn.send(bytes('150 Opening data connection.\r\n', 'UTF-8'))
        self.start_datasock()
        while True:
            data=self.datasock.recv(1024)
            if not data: break
            fo.write(data)
        fo.close()
        self.stop_datasock()
        self.conn.send(bytes('226 Transfer complete.\r\n','UTF-8'))

class FTPserver(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((local_ip,local_port))
        threading.Thread.__init__(self)

    def run(self):
        self.sock.listen(5)
        while True:
            fd, addr = self.sock.accept()
            #th=FTPserverThread(self.sock.accept())
            th=FTPserverThread(fd,addr)
            #th.daemon=True
            th.start()

    def stop(self):
        self.sock.close()

if __name__=='__main__':
    ftp=FTPserver()
    #ftp.daemon=True
    ftp.start()
    print ('On', local_ip, ':', local_port)
    #raw_input('Enter to end...\n')
    input('Enter to end...\n')
    ftp.stop()