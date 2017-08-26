#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.app.site.interfaces import ISite

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.externalization import to_external_object

from nti.externalization.oids import to_external_ntiid_oid

from nti.site.interfaces import IHostPolicyFolder

OID = StandardExternalFields.OID
NTIID = StandardExternalFields.NTIID


@component.adapter(IHostPolicyFolder)
@interface.implementer(IInternalObjectExternalizer)
class _SiteExternalizer(object):

    def __init__(self, obj):
        self.folder = obj

    def toExternalObject(self, *args, **kwargs):
        result = to_external_object(ISite(self.folder), *args, **kwargs)
        result[NTIID] = result[OID] = to_external_ntiid_oid(self.folder)
        return result
