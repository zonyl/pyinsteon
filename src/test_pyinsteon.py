'''
Created on Mar 26, 2011

@author: jason@sharpee.com
'''
import unittest
from pyinsteon import PyInsteon, TCP
#from mock import Mock


class TestPyInsteon(unittest.TestCase):


    def setUp(self):
#        mockTCP = Mock()
#        self.__insteon = PyInsteon(mockTCP)

        self.__insteon = PyInsteon(TCP('192.168.13.146', 9761))
        pass


    def tearDown(self):
        pass


    def testVersion(self):
        """test version number"""
        version = self.__insteon.getVersion()
        self.assertEqual(version,"92")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()