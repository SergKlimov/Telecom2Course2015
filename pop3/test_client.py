import unittest
from client import POP3_SSL

class testPOP3(unittest.TestCase):

    def setUp(self):
        self.login = 'sergklimoff'
        self.passwd = 'KlimovSergey'
        self.serv = 'pop.yandex.ru'
        self.port = '995'
        self.client = POP3_SSL(self.serv,self.port)
        self.client.user(self.login)
        self.client.pass_(self.passwd)

    def tearDown(self):
        self.client.quit()

    def test_no_retr(self):
        self.assertEqual(self.client.retr(2)[0].startswith(b'-ERR'), False)

    def get_mes(self, resp):
        tmp = resp
        raw = str(tmp[1])
        mes = raw.split(',')
        l = len(mes)
        message = mes[l-7]
        return message

    def test_retr(self):
        self.assertNotEqual(self.get_mes(self.client.retr(1))," b\'Smtng wrong'")

    def test_stat(self):
        self.assertGreaterEqual(self.client.stat(), (0,0))

    def test_dele(self):
        tmp1 = self.client.stat()[0]
        self.client.dele(1)
        self.client.quit()
        print('Before dele: %s' % str(tmp1))
        self.client = POP3_SSL(self.serv,self.port)
        self.client.user(self.login)
        self.client.pass_(self.passwd)
        tmp2 = self.client.stat()[0]
        print('After dele: %s' % str(tmp2))
        self.assertLess(tmp2, tmp1)

    def test_rset(self):
        tmp1 = self.client.stat()[0]
        self.client.dele(1)
        self.client.rset()
        self.client.quit()
        self.client = POP3_SSL(self.serv,self.port)
        self.client.user(self.login)
        self.client.pass_(self.passwd)
        tmp2 = self.client.stat()[0]
        self.assertEqual(tmp2, tmp1)

if __name__ == '__main__':
    unittest.main()