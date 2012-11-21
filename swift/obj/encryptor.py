from M2Crypto.EVP import Cipher

from swift.common.middleware.encryption.drivers.fake_driver \
        import FakeDriver as FakeKeystoreDriver
from swift.common.middleware.encryption.drivers.sql import SQLDriver
"""
Library which realise cryptography functional.
It takes key value and encrypt objects
"""


class CryptoDriver(object):
    """
    Crypt, decrypt and get key using key_id. Decision what crypto driver
    to use are taken here. Drivers for different realisation should implements
    this class and implements functions crypt and decrypt.
    """
    key_value = ""

    def __init__(self, conf):
        self.protocol = conf.get("crypto_protocol")
        self.keystore_driver = self._get_keystore_driver(conf)

    def _get_keystore_driver(self, conf):
        """
        Returns the correct implementation of the keystore driver
        based on the configuration file.

        :param conf: object-server configuration file
        :returns: implementation of the keystore driver
        """
        driver = conf.get('crypto_keystore_driver')
        if driver == "sql":
            url = conf.get("crypto_keystore_sql_url")
            return SQLDriver(url)
        if driver == "fake":
            return FakeKeystoreDriver()

    def crypted_len(self, original_len):
        """
        Count length of crypted string, base on length original
        string. Should be called only for classes, which implement
        this class and realise crypto algorithm.

        :param original_len: length of original string
        :returns: length of crypted string
        """
        res = "a" * original_len
        return len(str(self.crypt(res)))

    def crypt(self, chunk_string):
        """
        :param chunk_string: string for encryption
        :returns: encrypted string
        """
        raise NotImplementedError

    def decrypt(self, chunck_string):
        """
        :param chunk_string: string for decryption
        :returns: decrypted string
        """
        raise NotImplementedError

    def get_key_value(self, key_id):
        """
        Get key value from KeyController
        :param key_id: Id of key
        :returns key_value: directly key for this id.
        """
        self.key_value = self.keystore_driver.get_key(key_id)


class FakeDriver(CryptoDriver):
    """
    Fake implementation of CryptoDriver, which does nothing. While
    encryption/decryption it just return original string.
    """
    def __init__(self, conf):
        CryptoDriver.__init__(self, conf)

    def crypt(self, chunk_string):
        """
        Make fake encryption. Just return original string.

        :param chunk_string: original string for encryption
        :returns: original string
        """
        return chunk_string

    def decrypt(self, chunk_string):
        """
        Make fake decryption. Just return original string.

        :param chunk_string: original string for decryption
        :returns: original string
        """
        return chunk_string


class M2CryptoDriver(CryptoDriver):
    """
    Implementation of CryptoDriver based on m2crypto library.
    Initial vector, which used in some algorithm is hardcoded,
    because we use unified keys for all algorithm. So only key
    value is used for crypting. Also using hardcoded value provides
    better secure than not using it at all.
    """
    def __init__(self, conf):
        CryptoDriver.__init__(self, conf)
        self.iv = "3141527182810345"
        self.protocol = conf.get("crypto_protocol", "aes_128_cbc")
        if self.protocol != "aes_128_cbc":
            raise NotImplementedError("Incorrect protocol")

    def crypt(self, chunk):
        """
        Encrypt string whith protocol from crypto_protocol config field.
        Use hardcoded initial vector and key extracted from keystore.

        :param chunk: string for encryption
        :returns: encrypted string
        :raises ValueError: if crypto protocol is not supported
                            by M2Crypto library
        """
        try:
            cipher = Cipher(alg=self.protocol,
                    key=self.key_value, iv=self.iv, op=1)
            v = cipher.update(chunk)
            v = v + cipher.final()
            del cipher
            return v
        except ValueError, error:
            if error[0] == 'unknown cipher':
                raise ValueError('%r:%r please select avaliable protocol \
                        type' % (error[0], error[1]))

    def decrypt(self, chunk):
        """
        Decrypt string whith protocol from crypto_protocol config field.
        Use hardcoded initial vector and key extracted from keystore.

        :param chunk: string for decryption
        :returns: decrypted string
        :raises ValueError: if crypto protocol is not supported
                            by M2Crypto library
        """
        try:
            cipher = Cipher(alg=self.protocol,
                    key=self.key_value, iv=self.iv, op=0)
            v = cipher.update(chunk)
            v = v + cipher.final()
            del cipher
            return v
        except ValueError, error:
            if error[0] == 'unknown cipher':
                raise ValueError('%r:%r please select avaliable protocol \
                        type' % (error[0], error[1]))
