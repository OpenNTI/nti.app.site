#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from nti.site.interfaces import IHostPolicySiteManager
from zope.interface.interfaces import IUtilityRegistration

from nti.base._compat import text_
from nti.externalization.datastructures import InterfaceObjectIO
from nti.externalization.externalization import to_external_object, NonExternalizableObjectError

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class ComponentObjectIO(InterfaceObjectIO):

    _ext_iface_upper_bound = IHostPolicySiteManager
    _excluded_out_ivars_ = ('adapters', 'utilities', 'subs')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        from IPython.terminal.debugger import set_trace;set_trace()
        result =  super(ComponentObjectIO, self).toExternalObject(**kwargs)
        ext_self = self._ext_replacement()
        for attr in ('registeredUtilities',):
            callable_generator = getattr(ext_self, attr)
            result[attr] = [to_external_object(reg) for reg in callable_generator()]
        return result


class UtilityRegistrationObjectIO(InterfaceObjectIO):
    
    _ext_iface_upper_bound = IUtilityRegistration

    _excluded_out_ivars_ = ('provided', 'component', 'factory', 'registry')

    def toExternalObject(self, mergeFrom=None, **kwargs):
        from IPython.terminal.debugger import set_trace;set_trace()
        result = super(UtilityRegistrationObjectIO, self).toExternalObject(mergeFrom, **kwargs)
        ext_self = self._ext_replacement()
        # Host Policy Folder name
        result['registry'] = ext_self.registry.__parent__.__name__
        result['provided'] = ext_self.provided.getName()
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
