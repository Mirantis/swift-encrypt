=======================================
On-disk Object Files Encryption Feature
=======================================

----------------------------
Configure On-disk Encryption
----------------------------

To enable on-disk encryption feature, you need to install Swift extended with
on-disk encryption support. Obtain the source code in the `Github repository
<https://github.com/Mirantis/swfit-encrypt>`_ and use installation procedures
described in your favourite installation guide.
Once you have the cluster deployed and Rings built, you need to change config
files for proxy-server and object-server.

Proxy-server configuration
--------------------------

You need to add the ``key-manager`` to the pipeline configuration directive in
the ``/etc/swift/proxy-server.conf`` file:

::

    pipeline = catch_errors healthcheck cache ratelimit tempauth key-manager proxy-logging proxy-server

You also need to configure the ``key-manager`` filter later in the same file,
for example:

::

    [filter:key-manager]
    use = egg:swift#key_manager
    crypto_keystore_driver 	= swift.common.key_manager.drivers.sql.SQLDriver
    crypto_keystore_sql_url	= mysql://root:12345@somehost/swift_encryption_store_key_account_db

Following configuration parameters are supported for the ``key-manager`` filter:

=========================== ===================================================
Configuration Parameter     Description
=========================== ===================================================
``crypto_keystore_driver``  This parameter defines which driver class will be
                            used for creating object which communicates to
                            key storage back-end.
``crypto_keystore_sql_url`` This parameter is only valid if ``SQLDriver`` used
                            for ``crypto_keystore_driver``. Otherwise, it is
                            ignored. Value of this parameter is used as SQL
                            connection string.
=========================== ===================================================

Following key store drivers are supported in current implementation:

.. automodule:: swift.common.key_manager.drivers
    :members:
    :undoc-members:
    :show-inheritance:

    ``swift.common.key_manager.drivers.dummy.DummyDriver``
        This is the dummy driver which does not store any keys and uses
        MD5 sum of account name to generate key string at the runtime
    ``swift.common.key_manager.drivers.dummy.FakeDriver``
        This is the fake key store driver which always returns the same
        key string
    ``swift.common.key_manager.drivers.sql.SQLDriver``
        This is the driver which generates keys and stores them to SQL
        database

Object-server configuration
---------------------------

You need to modify configuration file for all object-servers in your cluster.
Following encryption related directives are supported in ``[app:object-server]``
section:

=========================== ===================================================
Configuration Parameter     Description
=========================== ===================================================
``crypto_driver``           This parameter defines which driver class used for
                            encryption protocol implementation
``crypto_protocol``         This parameter defines which crypto protocol used
                            for encryption of object chunks
``crypto_keystore_driver``  This parameter defines which driver class used to
                            communicate to key store. Value of this parameter
                            must match the value of the same parameter in
                            proxy-server configuration
``crypto_keystore_sql_url`` This parameter is only valid if ``SQLDriver`` used
                            for ``crypto_keystore_driver``. Otherwise, it is
                            ignored. Value of this parameter is used as SQL
                            connection string. Value of this parameter must
                            match the value of the same parameter in
                            proxy-server configuration
=========================== ===================================================

Following crypto drivers are supported in current implementation:

.. automodule:: swift.obj.encryptor
    :members:
    :undoc-members:
    :show-inheritance:

Following algorithm is supported in current implementation:

    ``aes_128_cbc``
        This protocol is provided by M2Crypto library
