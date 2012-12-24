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
import mock

from swift.common.middleware import key_manager
from swift.common.key_manager.drivers.fake import FakeDriver


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
        """
        Set up for testing swift.common.middleware.key_manager.KeyManager.
        """
        self.conf = {}
        self.patcher = mock.patch('swift.common.middleware.key_manager.'
                                  'create_instance')
        self.mock_create_instance = self.patcher.start()
        self.mock_create_instance.return_value = FakeDriver(self.conf)

    def tearDown(self):
        """
        Tear down for testing swift.common.middleware.key_manager.KeyManager.
        """
        self.patcher.stop()

    def test_filter(self):
        """
        Testing filter_factory
        """
        factory = key_manager.filter_factory(self.conf)
        self.assertTrue(callable(factory))
        self.assertTrue(callable(factory(FakeApp())))

    def test_functions_with_fake_driver(self):
        """
        Testing key_manager's methods
        """
        app = key_manager.KeyManager(FakeApp, self.conf)
        account_path = '/Version/MyName/Container/Object'

        # Fake driver return "12345"
        self.assertEquals(app.get_key_id("anybody"), 12345)
        self.assertEquals(app.get_account(account_path), "MyName")
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
