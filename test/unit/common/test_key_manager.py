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

from migrate.exceptions import DatabaseNotControlledError
from sqlalchemy import create_engine, exc
from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import String, Integer

from swift.common.key_manager.drivers.sql import SQLDriver
from swift.common.key_manager.drivers.sql.driver import Key, Session,\
     generate_key, ping_connection


meta_test = MetaData()
table_template = Table("key_info", meta_test,
                       Column('account', String(42)),
                       Column('key_id', Integer, primary_key=True,
                              autoincrement=True),
                       Column('encryption_key', String(42)))


class TestSQLDriver(unittest.TestCase):
    def setUp(self):
        """
        Set up for testing
        swift.common.key_manager.drivers.sql.SQLDriver.
        """
        self.db_path = tempfile.mktemp()
        self.url = "sqlite:///%s" % (self.db_path,)
        self.conf = {'crypto_keystore_sql_url': self.url}
        self.key_driver = SQLDriver(self.conf)
        self.dbapi_connection = mock.Mock()

        cursor = mock.Mock()
        cursor.execute = mock.Mock()
        self.dbapi_connection.cursor.return_value = cursor
        self.dbapi_connection.OperationalError = exc.OperationalError
        engine = create_engine(self.url)
        meta_test.bind = engine
        Session.configure(bind=engine)
        table_template.create(engine, checkfirst=True)

    def tearDown(self):
        """
        Tear down for testing
        swift.common.key_manager.drivers.sql.SQLDriver.
        """
        os.remove(self.db_path)

    def test_get_key_id(self):
        """
        Check key_id value for different account values.
        """
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
        # create 2 account with key_id
        acc_info = ["acc1", "acc2"]
        session = Session()
        for acc in acc_info:
            session.add(Key(acc, generate_key()))
        session.commit()
        # check key for first account
        key1 = self.key_driver.get_key(1)
        key2 = self.key_driver.get_key(1)
        self.assertEqual(key1, key2)

        # check key for second account
        key3 = self.key_driver.get_key(2)
        self.assertNotEqual(key2, key3)
        # check raise, if incorrect id (no in table)
        self.assertRaises(StandardError, self.key_driver.get_key, 100)
        session.close()

    @mock.patch('migrate.versioning.api.upgrade')
    def test_sync_success(self, mock_upgrade):
        """
        Successful migration.
        """
        self.key_driver.sync()
        mock_upgrade.assert_called_once_with(self.url, mock.ANY)

    @mock.patch('migrate.versioning.api.version_control')
    @mock.patch('migrate.versioning.api.upgrade')
    def test_sync_failed(self, mock_upgrade, mock_version_control):
        """
        Version control table doesn't exist.
        """
        mock_upgrade.side_effect = [DatabaseNotControlledError, None]
        self.key_driver.sync()
        mock_upgrade.assert_has_calls(2 * [mock.call(self.url, mock.ANY)])
        mock_version_control.assert_called_once_with(self.url, mock.ANY)

    def test_invalid_key_id(self):
        self.assertRaises(ValueError,
                         self.key_driver.validate_key_id, "n0tnumb3r")
        self.assertRaises(ValueError,
                         self.key_driver.validate_key_id, "-13")

    def test_valid_key_id(self):
        self.assertEqual(None, self.key_driver.validate_key_id("42"))

    def test_succesful_ping(self):
        self.dbapi_connection.cursor().execute.return_value = None
        self.assertEqual(None,
                        ping_connection(self.dbapi_connection, None, None))

    def test_connection_problems(self):
        error = exc.OperationalError(None, None, None)
        #typical situations when connection should be removed from a pool
        for code in (2006, 2013, 2014, 2045, 2055):
            error.args = [code, 'connection need to be removed']
            self.dbapi_connection.cursor().execute.side_effect = error
            self.assertRaises(exc.DisconnectionError, ping_connection,
                            self.dbapi_connection, None, None)

    def test_unknown_problem(self):
        error = exc.OperationalError(None, None, None)
        #expected exception type with unexpected error code, raised further
        error.args = [2000, "CR_UNKNOWN_ERROR"]
        self.dbapi_connection.cursor().execute.side_effect = error
        self.assertRaises(exc.OperationalError, ping_connection,
                            self.dbapi_connection, None, None)
        error = StandardError()
        #unexpected error, shouldn't be catched
        error.args = [42, 'all is lost']
        self.dbapi_connection.cursor().execute.side_effect = error
        self.assertRaises(StandardError, ping_connection,
                            self.dbapi_connection, None, None)


if __name__ == '__main__':
    unittest.main()
