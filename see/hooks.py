# Copyright 2015-2016 F-Secure

# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License.  You may
# obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

import logging
import inspect

from collections import namedtuple

from see.interfaces import Hook


HookParameters = namedtuple('HookParameters', ('identifier',
                                               'configuration',
                                               'context'))


def hooks_factory(identifier, configuration, context):
    """
    Returns the initialized hooks.
    """
    manager = HookManager(identifier, configuration)
    manager.load_hooks(context)

    return manager


class HookManager(object):
    """
    The Hooks Manager takes care the Hooks allocation, configuration
    and deallocation.
    """
    def __init__(self, identifier, configuration):
        self.hooks = []
        self.identifier = identifier
        self.configuration = configuration
        self.logger = logging.getLogger(
            '%s.%s' % (self.__module__, self.__class__.__name__))

    def load_hooks(self, context):
        for hook in self.configuration.get('hooks', ()):
            config = hook.get('configuration', {})
            config.update(self.configuration.get('configuration', {}))

            self._load_hook(hook['name'], config, context)

    def _load_hook(self, name, configuration, context):
        self.logger.debug('Loading %s hook.', name)

        try:
            HookClass = lookup_hook_class(name)
            hook = HookClass(HookParameters(self.identifier,
                                            configuration,
                                            context))
            self.hooks.append(hook)
        except Exception as error:
            self.logger.exception('Hook %s initialization failure, error: %s.',
                                  name, error)

    def cleanup(self):
        for hook in self.hooks:
            try:
                hook.cleanup()
            except NotImplementedError:
                pass
            except Exception as error:
                self.logger.exception('Hook %s cleanup error: %s.',
                                      hook.__class__.__name__, error)

        self.hooks = []


def lookup_hook_class(name):
    HookClass = lookup_class(name)

    if not issubclass(HookClass, Hook):
        raise ValueError("%r is not subclass of of %r" % (HookClass, Hook))
    else:
        return HookClass


def lookup_class(fully_qualified_name):
    """
    Given its fully qualified name, finds the desired class and imports it.
    Returns the Class object if found.
    """
    module_name, class_name = str(fully_qualified_name).rsplit(".", 1)
    module = __import__(module_name, globals(), locals(), [class_name], 0)
    Class = getattr(module, class_name)

    if not inspect.isclass(Class):
        raise ValueError(
            "%s is not of type class: %s" % (class_name, type(Class)))

    return Class
