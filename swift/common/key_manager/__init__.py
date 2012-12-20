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
Management of keys for objects encryption.
"""

from swift.common.utils import import_class


def get_driver(conf, driver):
    """
    Function to get and initialize driver to store keys.

    :param conf: application configuration dictionary
    :param driver: import path to KeyDriver subclass

    :returns: instance of subclass of
              swift.common.key_manager.base.KeyDriver
    """
    driver_class = import_class(driver)
    return driver_class(conf)
