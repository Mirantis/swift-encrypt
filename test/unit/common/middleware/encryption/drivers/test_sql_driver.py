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
import tempfile
import os

import mock
from sqlalchemy import exc

from swift.common.middleware.encryption.drivers.sql import SQLDriver
from swift.common.middleware.encryption.drivers.sql import key_info_table


class TestSQLDriver(unittest.TestCase):
    def setUp(self):
        """
        Create new sqllite database
        """
        self.db_path = tempfile.mktemp()
        self.url = "sqlite:///%s" % (self.db_path,)
        self.key_driver = SQLDriver(self.url)

    def test_initialization(self):
        """
        Check initialization method for new class
        """
        # Correct initialization
        self.assertEquals(type(SQLDriver(self.url)), SQLDriver)

    @mock.patch('swift.common.middleware.encryption.drivers.sql.create_engine')
    def test_reconnect_to_db(self, mock_create_engine):
        """
        Check reconnect function
        """
        key_driver = SQLDriver(self.url)
        # check first connect by initialization
        self.assert_(key_driver.engine.connect.call_count == 1)
        # check that connect once, if connect is successful
        key_driver.reconnect_to_db()
        self.assert_(key_driver.engine.connect.call_count == 2)

        # ckeck behavior if DB isn't available
        key_driver.engine.connect.call_count = 0
        key_driver.engine.connect.side_effect = exc.SQLAlchemyError
        # check sqlalchemy raise
        self.assertRaises(exc.SQLAlchemyError, key_driver.reconnect_to_db)
        # check number of attemps
        attempts = key_driver.engine.connect.call_count
        self.assertEquals(key_driver.connection_attempts, attempts)

        # check behavior if two connect request fail
        key_driver.engine.connect.call_count = 0
        connect_results = [exc.SQLAlchemyError, exc.SQLAlchemyError, 1]
        key_driver.engine.connect.side_effect = connect_results

        key_driver.reconnect_to_db()
        self.assertEquals(key_driver.engine.connect.call_count, 3)

    def test_create_table(self):
        """
        Drop table and try to create again
        """
        table_name = key_info_table.name
        # check, that table was created in initialization method
        self.assert_(self.key_driver.engine.has_table(table_name))

        # delete table and check it
        self.key_driver.engine.execute("drop table " + table_name)
        self.assertFalse(self.key_driver.engine.has_table(table_name))

        # create table using pattern and check it
        self.key_driver.create_table()
        self.assert_(self.key_driver.engine.has_table(table_name))

    def test_find_value(self):
        """
        Find row in table according serching pattern
        """
        first_acc_info = ["test_account", "test_key_string"]
        second_acc_info = ["test_account2", "test_key_string2"]

        answer1 = [('test_account', 1L, 'test_key_string')]
        answer2 = [('test_account2', 2L, 'test_key_string2')]

        self.key_driver.create_table()
        for data_acc in [first_acc_info, second_acc_info]:
            key_info_table.insert().execute(account=data_acc[0],
                                        encryption_key=data_acc[1])

        # check, that result empty , if such information not exist in DataBase
        self.assertFalse(self.key_driver.find_value("account", "my_account"))

        # check, results for currect find requests
        # First answer
        res = self.key_driver.find_value("account", first_acc_info[0])
        self.assertEquals(res, answer1)
        res = self.key_driver.find_value("encryption_key", first_acc_info[1])
        self.assertEquals(res, answer1)
        res = self.key_driver.find_value("key_id", "1")
        self.assertEquals(res, answer1)

        # Second answer
        res = self.key_driver.find_value("account", second_acc_info[0])
        self.assertEquals(res, answer2)
        res = self.key_driver.find_value("encryption_key", second_acc_info[1])
        self.assertEquals(res, answer2)
        res = self.key_driver.find_value("key_id", "2")
        self.assertEquals(res, answer2)

    def test_get_key_id(self):
        """
        Check key_id value for different account values
        """
        acc_info = ["acc1", "acc2"]
        # check key_id for first account (account not existed)
        self.assert_(self.key_driver.get_key_id(acc_info[0]) == 1)
        # check key_id for first account (account existed)
        self.assert_(self.key_driver.get_key_id(acc_info[0]) == 1)
        # check that account not created again (account existed)
        self.assertFalse(self.key_driver.get_key_id(acc_info[0]) == 2)
        # check key_id for second account
        self.assert_(self.key_driver.get_key_id(acc_info[1]) == 2)

    def test_get_key(self):
        """
        Check key value for different account and key_id values
        """
        # create 2 account with key_id
        acc_info = ["acc1", "acc2"]
        for acc in acc_info:
            key_info_table.insert().execute(account=acc)
        # check key for first account
        key1 = self.key_driver.get_key(1)
        key2 = self.key_driver.get_key(1)
        self.assert_(key1 == key2)

        # check key for second account
        key3 = self.key_driver.get_key(2)
        self.assert_(key2 != key3)
        # check raise, if incorrect id (no in table)
        self.assertRaises(StandardError, self.key_driver.get_key, 100)
        # check raise, if incorrect id (string and have not only digits)
        self.assertRaises(ValueError, self.key_driver.get_key, "id100")
        # check raise, if incorrect id (not string or int)
        test = [[2], {"test": "test"}, (222, 2)]
        for val in test:
            self.assertRaises(TypeError, self.key_driver.get_key, val)

    def tearDown(self):
        """
        Remove DataBase
        """
        os.remove(self.db_path)

if __name__ == '__main__':
    unittest.main()
