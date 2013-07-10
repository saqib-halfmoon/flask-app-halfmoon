#--------------------------------
#!/usr/bin/env python
# Copyright 2013 Halfmoon Labs, Inc.
# All Rights Reserved
#--------------------------------

import os
import halfmoon
import unittest
import tempfile

class HalfmoonCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, halfmoon.app.config['DATABASE'] = tempfile.mkstemp()
        halfmoon.app.config['TESTING'] = True
        self.app = halfmoon.app.test_client()
        halfmoon.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(halfmoon.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)  

    #--------------------------
    # testing functions
    #--------------------------

    def test_empty_db(self):
        rv = self.app.get('/')
        assert b'No entries here so far' in rv.data    

    def test_login_logout(self):
        rv = self.login(halfmoon.app.config['USERNAME'], halfmoon.app.config['PASSWORD'])
        assert b'You were logged in' in rv.data 
        rv = self.logout()
        assert b'You were logged out' in rv.data
        rv = self.login('adminx', 'default')
        assert b'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert b'Invalid password' in rv.data
    
    def test_messages(self):
        self.login('admin', 'default')
        rv = self.app.post('/add', data=dict(
        title='<Hello>',
        text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data

if __name__ == '__main__':
    unittest.main()