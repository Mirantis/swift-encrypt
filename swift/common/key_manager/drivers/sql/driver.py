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

import base64
import os

from sqlalchemy import create_engine, exc, orm
from sqlalchemy.schema import Column
from sqlalchemy.types import String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from migrate.versioning import api as versioning_api
from migrate import exceptions as versioning_exceptions

from swift.common.key_manager.drivers import base
from swift.common.key_manager.drivers.sql import migrate_repo


Base = declarative_base()
Session = sessionmaker(expire_on_commit=False)


class Key(Base):
    __tablename__ = "key_info"

    account = Column(String(42))
    key_id = Column(Integer, primary_key=True, autoincrement=True)
    encryption_key = Column(String(42))

    def __init__(self, account, encryption_key):
        self.account = account
        self.encryption_key = encryption_key

    def __eq__(self, other):
        return (self.account == other.account and
                self.key_id == other.key_id and
                self.encryption_key == other.encryption_key)

    def __ne__(self, other):
        return not self.__eq__(other)


class SQLDriver(base.KeyDriver):
    """
    Driver for cooperation proxy and object servers with keys storage.
    """
    default_connection_attempts = 5
    default_connection_url = 'sqlite:///keystore.sqlite'

    def __init__(self, conf):
        """
        Initialization function.

        :param conf: application configuration
        """
        super(SQLDriver, self).__init__(conf)
        self.connection_attempts = conf.get(
            'crypto_keystore_sql_connection_attempts',
            self.default_connection_attempts)
        self.connection_url = conf.get('crypto_keystore_sql_url',
                                       self.default_connection_url)
        self.engine = create_engine(self.connection_url)
        self.reconnect_to_db()

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
        """Give key_id is associated by account.

        If no key_id to be found, it's created.

        :param acc_name: string is name of account
        :returns: number of key in database
        """
        session = Session(bind=self.engine)
        try:
            key = session.query(Key).filter(Key.account == acc_name).first()
            if key is None:
                key = Key(acc_name, generate_key())
                session.add(key)
                session.commit()
        finally:
            session.close()
        return key.key_id

    def get_key(self, key_id):
        """
        Give encryption key presented as string

        :param key_id: number of key in database
        :return key: string is used for encryption process

        :raise StandardError: if DB don't have row with current key_id
        """
        self.reconnect_to_db()
        session = Session(bind=self.engine)
        re = session.query(Key).filter(Key.key_id == key_id).all()
        if not re:
            raise StandardError("In DataBase no row with current key_id")

        key = base64.b16decode(re[0].encryption_key)
        session.close()
        return key

    def sync(self):
        """
        Migrate database schemas.
        """
        repo_path = os.path.abspath(os.path.dirname(migrate_repo.__file__))
        try:
            versioning_api.upgrade(self.connection_url, repo_path)
        except versioning_exceptions.DatabaseNotControlledError:
            versioning_api.version_control(self.connection_url, repo_path)
            versioning_api.upgrade(self.connection_url, repo_path)


def generate_key():
    return base64.b16encode(os.urandom(16))
