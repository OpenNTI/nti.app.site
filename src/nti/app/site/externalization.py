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

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.oids import to_external_ntiid_oid

from nti.site.interfaces import IHostPolicyFolder

OID = StandardExternalFields.OID
CLASS = StandardExternalFields.CLASS
NTIID = StandardExternalFields.NTIID
ITEMS = StandardExternalFields.ITEMS
MIMETYPE = StandardExternalFields.MIMETYPE


@component.adapter(IHostPolicyFolder)
@interface.implementer(IInternalObjectExternalizer)
class _SiteExternalizer(object):

    def __init__(self, obj):
        self.site = obj

    def toExternalObject(self, *args, **kwargs):
        result = LocatedExternalDict()
        result[CLASS] = 'Site'
        result['Name'] = self.site.__name__
        result[MIMETYPE] = 'application/vnd.nextthought.site'
        result[NTIID] = result[OID] = to_external_ntiid_oid(self.site)
        return result
