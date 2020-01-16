#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: internalization.py 122560 2017-09-30 23:21:05Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.site.interfaces import IPersistentSiteMapping

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


@component.adapter(IPersistentSiteMapping)
@interface.implementer(IInternalObjectUpdater)
class _PersistentSiteMappingUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IPersistentSiteMapping

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        for attr in ('source_site_name', 'target_site_name'):
            if attr in parsed:
                try:
                    parsed[attr] = parsed[attr].lower()
                except (AttributeError, TypeError):
                    pass
        return super(_PersistentSiteMappingUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)
