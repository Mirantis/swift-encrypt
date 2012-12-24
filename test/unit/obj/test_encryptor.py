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

import unittest
import mock
import os

from swift.obj.encryptor import M2CryptoDriver, FakeDriver


class TestEncryptor(unittest.TestCase):
    def setUp(self):
        """
        Set up for testing swift.obj.encryptor.M2CryptoDriver and
        swift.obj.encryptor.FakeDriver encryption drivers.
        """
        self.patcher = mock.patch('swift.obj.encryptor.create_instance')
        self.mock_create_instance = self.patcher.start()

    def tearDown(self):
        """
        Tear down for testing swift.obj.encryptor.M2CryptoDriver and
        swift.obj.encryptor.FakeDriver encryption drivers.
        """
        self.patcher.stop()

    def _driver_testing(self, crypto_driver):
        """
        Test any crypto driver that it can correctly
        decrypt crypted by him text.

        :param crypto_driver: crypto driver for testing
        """
        text = os.urandom(20000)
        crypted_text = crypto_driver.crypt(text)
        self.assertEquals(text, crypto_driver.decrypt(crypted_text))

    def test_M2CryptoDriver_aes_128_cbc(self):
        """Test for M2Crypto driver whith aes_128_cbc algorithm"""
        conf = {"crypto_protocol": "aes_128_cbc"}
        crypto_driver = M2CryptoDriver(conf)
        self._driver_testing(crypto_driver)

    def test_FakeDriver(self):
        """Test for fake driver"""
        conf = {}
        crypto_driver = FakeDriver(conf)
        self._driver_testing(crypto_driver)
