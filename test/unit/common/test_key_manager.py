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

import os
import unittest
import tempfile
import mock

from sqlalchemy import exc
from migrate.exceptions import DatabaseNotControlledError

from swift.common.key_manager.drivers.sql import SQLDriver
from swift.common.key_manager.drivers.sql.driver import key_info_table


class TestSQLDriver(unittest.TestCase):
    def setUp(self):
        """
        Set up for testing
        swift.common.key_manager.drivers.sql.SQLDriver.
        """
        self.db_path = tempfile.mktemp()
        self.url = "sqlite:///%s" % (self.db_path,)
        self.conf = {'crypto_keystore_sql_url': self.url}
        self.key_driver = SQLDriver(self.conf, initialize_table=False)

    def tearDown(self):
        """
        Tear down for testing
        swift.common.key_manager.drivers.sql.SQLDriver.
        """
        os.remove(self.db_path)

    def test_create_table(self):
        """
        Drop table and try to create again.
        """
        self.key_driver.create_table()
        table_name = key_info_table.name
        self.assertTrue(self.key_driver.engine.has_table(table_name))

    def test_find_value(self):
        """
        Find row in table according serching pattern.
        """
        self.key_driver.create_table()

        first_acc_info = ["test_account", "test_key_string"]
        second_acc_info = ["test_account2", "test_key_string2"]

        answer1 = [('test_account', 1L, 'test_key_string')]
        answer2 = [('test_account2', 2L, 'test_key_string2')]

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
        Check key_id value for different account values.
        """
        self.key_driver.create_table()

        acc_info = ["acc1", "acc2"]
        # check key_id for first account (account not existed)
        self.assertEqual(self.key_driver.get_key_id(acc_info[0]), 1)
        # check key_id for first account (account existed)
        self.assertEqual(self.key_driver.get_key_id(acc_info[0]), 1)
        # check that account not created again (account existed)
        self.assertNotEqual(self.key_driver.get_key_id(acc_info[0]), 2)
        # check key_id for second account
        self.assertEqual(self.key_driver.get_key_id(acc_info[1]), 2)

    def test_get_key(self):
        """
        Check key value for different account and key_id values.
        """
        self.key_driver.create_table()

        # create 2 account with key_id
        acc_info = ["acc1", "acc2"]
        for acc in acc_info:
            key_info_table.insert().execute(account=acc)
        # check key for first account
        key1 = self.key_driver.get_key(1)
        key2 = self.key_driver.get_key(1)
        self.assertEqual(key1, key2)

        # check key for second account
        key3 = self.key_driver.get_key(2)
        self.assertNotEqual(key2, key3)
        # check raise, if incorrect id (no in table)
        self.assertRaises(StandardError, self.key_driver.get_key, 100)
        # check raise, if incorrect id (string and have not only digits)
        self.assertRaises(ValueError, self.key_driver.get_key, "id100")
        # check raise, if incorrect id (not string or int)
        test = [[2], {"test": "test"}, (222, 2)]
        for val in test:
            self.assertRaises(TypeError, self.key_driver.get_key, val)

    @mock.patch('migrate.versioning.api.upgrade')
    def test_sync_success(self, mock_upgrade):
        """
        Successful migration.
        """
        self.key_driver.create_table()

        self.key_driver.sync()
        mock_upgrade.assert_called_once_with(self.url, mock.ANY)

    @mock.patch('migrate.versioning.api.version_control')
    @mock.patch('migrate.versioning.api.upgrade')
    def test_sync_failed(self, mock_upgrade, mock_version_control):
        """
        Version control table doesn't exist.
        """
        self.key_driver.create_table()

        mock_upgrade.side_effect = [DatabaseNotControlledError, None]
        self.key_driver.sync()
        mock_upgrade.assert_has_calls(2 * [mock.call(self.url, mock.ANY)])
        mock_version_control.assert_called_once_with(self.url, mock.ANY)


class TestSQLDriverReconnection(unittest.TestCase):
    def setUp(self):
        """
        Set up for testing reconnection to database of
        swift.common.key_manager.driver.sql.SQLDriver class.
        """
        self.conf = {'crypto_keystore_sql_url': 'fake'}
        self.patcher = mock.patch(
            'swift.common.key_manager.drivers.sql.driver.create_engine')
        self.mock_create_engine = self.patcher.start()
        self.key_driver = SQLDriver(self.conf, initialize_table=True)
        self.mock_connect = self.mock_create_engine.return_value.connect

    def tearDown(self):
        """
        Tear down of testing reconnection to database of
        swift.common.key_manager.driver.sql.SQLDriver class.
        """
        self.patcher.stop()

    def test_on_init(self):
        """
        Check reconnection on driver initialization.
        """
        self.assertEqual(self.key_driver.engine.connect.call_count, 1)

    def test_success(self):
        """
        Check reconnect on happy path.
        """
        self.mock_connect.reset_mock()

        self.key_driver.reconnect_to_db()
        self.assertEqual(self.key_driver.engine.connect.call_count, 1)

    def test_db_failed(self):
        """
        Connection always fails try to fixed attempts count.
        """
        self.mock_connect.reset_mock()

        self.key_driver.engine.connect.side_effect = exc.SQLAlchemyError
        self.assertRaises(exc.SQLAlchemyError, self.key_driver.reconnect_to_db)
        attempts = self.key_driver.engine.connect.call_count
        self.assertEquals(self.key_driver.connection_attempts, attempts)

    def test_failed_success(self):
        """
        First two connections fails but third successful.
        """
        self.mock_connect.reset_mock()

        connect_results = [exc.SQLAlchemyError, exc.SQLAlchemyError, 1]
        self.key_driver.engine.connect.side_effect = connect_results

        self.key_driver.reconnect_to_db()

        self.assertEquals(self.key_driver.engine.connect.call_count, 3)


if __name__ == '__main__':
    unittest.main()
