#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope.interface.interfaces import IAdapterRegistration
from zope.interface.interfaces import IComponentRegistry
from zope.interface.interfaces import IHandlerRegistration
from zope.interface.interfaces import ISubscriptionAdapterRegistration
from zope.interface.interfaces import IUtilityRegistration

from nti.base._compat import text_

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.externalization import NonExternalizableObjectError
from nti.externalization.externalization import to_external_object

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class ComponentObjectIO(InterfaceObjectIO):

    _ext_iface_upper_bound = IComponentRegistry
    _excluded_out_ivars_ = ('adapters', 'utilities', 'subs')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        result = super(ComponentObjectIO, self).toExternalObject(**kwargs)
        ext_self = self._ext_replacement()
        for attr in ('registeredUtilities',
                     'registeredAdapters',
                     'registeredSubscriptionAdapters',
                     'registeredHandlers'):
            callable_generator = getattr(ext_self, attr)
            result[attr] = [to_external_object(reg) for reg in callable_generator()]
        return result


class UtilityRegistrationObjectIO(InterfaceObjectIO):
    
    _ext_iface_upper_bound = IUtilityRegistration

    _excluded_out_ivars_ = ('provided', 'component', 'factory', 'registry', 'info')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        result = super(UtilityRegistrationObjectIO, self).toExternalObject(mergeFrom, **kwargs)
        ext_self = self._ext_replacement()
        # Host Policy Folder name
        result['registry'] = ext_self.registry.__parent__.__name__
        result['provided'] = ext_self.provided.getName()
        result['info'] = text_(getattr(ext_self, 'info', None))
        # Try to externalize if we can
        try:
            result['factory'] = to_external_object(ext_self.factory)
        except NonExternalizableObjectError:
            result['factory'] = text_(ext_self.factory)
        try:
            result['component'] = to_external_object(ext_self.component)
        except NonExternalizableObjectError:
            result['component'] = text_(ext_self.component)
        return result


class AdapterRegistrationObjectIO(InterfaceObjectIO):

    _ext_iface_upper_bound = IAdapterRegistration

    _excluded_out_ivars_ = ('provided', 'name', 'factory', 'registry', 'info', 'required')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        result = super(AdapterRegistrationObjectIO, self).toExternalObject(mergeFrom, **kwargs)
        ext_self = self._ext_replacement()
        # Host Policy Folder name
        result['registry'] = ext_self.registry.__parent__.__name__
        result['provided'] = ext_self.provided.getName()
        result['info'] = text_(getattr(ext_self, 'info', None))
        result['required'] = text_(getattr(ext_self, 'required', None))

        # Try to externalize if we can
        try:
            result['factory'] = to_external_object(ext_self.factory)
        except NonExternalizableObjectError:
            result['factory'] = text_(ext_self.factory)
        return result


class SubscriptionAdapterRegistrationObjectIO(InterfaceObjectIO):

    _ext_iface_upper_bound = ISubscriptionAdapterRegistration

    _excluded_out_ivars_ = ('provided', 'name', 'factory', 'registry', 'info', 'required')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        result = super(SubscriptionAdapterRegistrationObjectIO, self).toExternalObject(mergeFrom, **kwargs)
        ext_self = self._ext_replacement()
        # Host Policy Folder name
        result['registry'] = ext_self.registry.__parent__.__name__
        result['provided'] = ext_self.provided.getName()
        result['info'] = text_(getattr(ext_self, 'info', None))
        result['required'] = text_(getattr(ext_self, 'required', None))

        # Try to externalize if we can
        try:
            result['factory'] = to_external_object(ext_self.factory)
        except NonExternalizableObjectError:
            result['factory'] = text_(ext_self.factory)
        return result


class HandlerRegistrationObjectIO(InterfaceObjectIO):

    _ext_iface_upper_bound = IHandlerRegistration

    _excluded_out_ivars_ = ('provided', 'name', 'factory', 'registry', 'info', 'required', 'handler')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        result = super(HandlerRegistrationObjectIO, self).toExternalObject(mergeFrom, **kwargs)
        ext_self = self._ext_replacement()
        # Host Policy Folder name
        result['registry'] = ext_self.registry.__parent__.__name__
        result['info'] = text_(getattr(ext_self, 'info', None))
        result['required'] = text_(getattr(ext_self, 'required', None))

        # Try to externalize if we can
        try:
            result['factory'] = to_external_object(ext_self.factory)
        except NonExternalizableObjectError:
            result['factory'] = text_(ext_self.factory)
        try:
            result['handler'] = to_external_object(ext_self.handler)
        except NonExternalizableObjectError:
            result['handler'] = text_(ext_self.handler)
        return result
