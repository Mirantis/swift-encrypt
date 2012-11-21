# Copyright (c) 2011 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from swift.common.middleware.encryption import key_manager
from swift.common.middleware.encryption.drivers import fake_driver


class FakeApp(object):
    """ Fake WSGI application """
    def __init__(self, body=['FAKE APP'], params="FAKE"):
        self.body = body
        self.params = params

    def __call__(self, env, start_response):
        return self.body


def start_response(*args):
    """ Fake function for WSGI application """
    pass


class TestKeyManager(unittest.TestCase):
    def setUp(self):
        fake = 'fake'
        self.conf = {
            'crypto_keystore_driver': fake,
            'crypto_keystore_sql_url': fake,
        }

    def test_filter(self):
        """
        Testing filter_factory
        """
        factory = key_manager.filter_factory(self.conf)
        self.assert_(callable(factory))
        self.assert_(callable(factory(FakeApp())))

    def test_functions_with_fake_driver(self):
        """
        Testing key_manager's methods
        """
        app = key_manager.KeyManager(FakeApp, self.conf)
        account_path = '/Version/MyName/Container/Object'

        # Object for Fake driver is correct
        self.assertEquals(type(app.key_driver), fake_driver.FakeDriver)
        # have raise for any unknown driver.
        self.assertRaises(NotImplementedError, app.get_interface,
                          'unknown_driver')
        # Fake driver return "12345"
        self.assertEquals(app.get_key_id("anybody"), 12345)
        # account is correct
        self.assertEquals(app.get_account(account_path), "MyName")
        # Raise, if path with account is not correct
        self.assertRaises(ValueError, app.get_account, account_path[1:])

        # check filter for different types of request
        for req_type in ['GET', 'HEAD', 'DELETE', 'COPY', 'OPTIONS', 'POST']:
            resp = app({'PATH_INFO': account_path, 'REQUEST_METHOD': req_type},
                       start_response)
            diction = resp.body
            # Requset not include "key_id"
            self.assertFalse('HTTP_X_OBJECT_META_KEY_ID' in diction)

        # Request include "key_id", if it is PUT
        resp = app({'PATH_INFO': account_path, 'REQUEST_METHOD': 'PUT'},
                   start_response)
        diction = resp.body
        self.assertTrue('HTTP_X_OBJECT_META_KEY_ID' in diction)
        self.assertEquals(diction['HTTP_X_OBJECT_META_KEY_ID'], '12345')


if __name__ == '__main__':
    unittest.main()
