# Copyright (c) 2010-2012 OpenStack, LLC.
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

"""
SQL driver for KeyDriver class.

This library include methods for managing encryption key, such as:
    creation key and key_id;
    store information about of key_id, key, account in sql DataBase.
"""

import random
from base64 import b64decode, b64encode
import os

from sqlalchemy import create_engine, MetaData, Table, Column, String, \
     Integer, exc

from .base import KeyDriver


meta = MetaData()
key_info_table = Table("key_info", meta,
        Column('account', String(30)),
        Column('key_id', Integer, primary_key=True, autoincrement=True),
        Column('encryption_key', String(30))
)


class SQLDriver(KeyDriver):
    """
    Driver for cooperation proxy and object servers with keys storage
    """
    connection_attempts = 5

    def __init__(self, url):
        """
        Initialization function.
        :param url: url address for connecting to sql DataBase

        """
        self.engine = meta.bind = create_engine(url)
        self.create_table()

    def create_table(self):
        """
        Try connect to DB and if it is successfully,
        create key_info_table
        """
        self.reconnect_to_db()
        key_info_table.create(self.engine, checkfirst=True)

    def reconnect_to_db(self):
        """
        Try connect to DB,
        if it is successfully -> break
        else raise Exception

        :raise exc.SQLAlchemyError: if cann't connect to db
        """
        for i in range(self.connection_attempts):
            try:
                self.engine.connect()
            except exc.SQLAlchemyError:
                if i == self.connection_attempts - 1:
                    raise
            else:
                break

    def get_key_id(self, acc_name):
        """
        Give key_id is associated by account

        :param acc_name: string is name of account
        :return key_id: number of key in database
        """
        re = self.find_value("account", acc_name)
        if not re:
            self.reconnect_to_db()
            key_info_table.insert().execute(account=acc_name)
            re = self.find_value("account", acc_name)
        key_id = re[0][1]
        return key_id

    def get_key(self, key_id):
        """
        Give encryption key presented as string

        :param key_id: number of key in database
        :return key: string is used for encryption process

        :raise TypeError: if key_id isn't string or int
        :raise ValueError: if string include not only digits chars
        :raise StandardError: if DB don't have row with current key_id
        """
        if type(key_id) is not long:
            try:
                key_id = long(key_id)
            except TypeError:
                raise TypeError("Incorrect type. Must be string or int.")
            except ValueError:
                raise ValueError("Incorrect value. String must include "
                                 "only digits chars.")

        re = self.find_value("key_id", str(key_id))
        if not re:
            raise StandardError("In DataBase no row with current key_id")

        if re[0][2] is None:
            # For openssl standart key consist of 16 hex chars
            key = os.urandom(16)
            # change format for store key in database
            enc_key = b64encode(key)
            # check connection to database
            self.reconnect_to_db()
            # select key_id column
            column = key_info_table.c.key_id
            # create update method for table with current key_id
            update_method = key_info_table.update(column == str(key_id))
            # update encryption_key column using update method
            update_method.execute(encryption_key=enc_key)
            return key

        key = b64decode(re[0][2])
        return key

    def find_value(self, col_name, val):
        """Find row where param col_name == val
        :param conn: connection object for executing SQL commands
        :param col_name: string - name of using collumn
        :param val: string - value to search

        :return res: tuple with values account, key_id, key
        """
        self.reconnect_to_db()
        # select column
        column = key_info_table.c[col_name]
        # use select method
        return key_info_table.select(column == val).execute().fetchall()
