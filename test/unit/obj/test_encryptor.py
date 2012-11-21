import unittest
import os

from swift.obj.encryptor import M2CryptoDriver, FakeDriver


class TestEncryptor(unittest.TestCase):

    def _driver_testing(self, crypto_driver):
        """
        Test any crypto driver that it can correctly
        decrypt crypted by him text

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
