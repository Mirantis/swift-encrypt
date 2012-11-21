
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
KeyDriver class - pattern for drivers.

This class include methods for cooperation with DataBase:
    requestions - get_key and get_key_id.
"""


class KeyDriver(object):
    """Parent class for differetn key manager interfaces"""

    def get_key(self, key_id):
        """
        Empty method get_key

        :param key_id: number of key in database
        :raise NotImplementedError: If driver don't have this method
        """
        raise NotImplementedError("Not implemented get_key function. "
                                  "Maybe incorrect driver")

    def get_key_id(self, account):
        """
        Empty method get_key_id

        :param account: string is name of account
        :raise NotImplementedError: If driver don't have this method
        """
        raise NotImplementedError("Not implemented get_key_id function. "
                                  "Maybe incorrect driver")
