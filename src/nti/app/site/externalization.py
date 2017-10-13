#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.site.interfaces import ISite

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.externalization import to_external_object

from nti.ntiids.oids import to_external_ntiid_oid

from nti.site.interfaces import IHostPolicyFolder

OID = StandardExternalFields.OID
NTIID = StandardExternalFields.NTIID

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicyFolder)
@interface.implementer(IInternalObjectExternalizer)
class _SiteExternalizer(object):

    def __init__(self, obj):
        self.folder = obj

    def toExternalObject(self, *args, **kwargs):
        result = to_external_object(ISite(self.folder), *args, **kwargs)
        result[NTIID] = result[OID] = to_external_ntiid_oid(self.folder)
        return result
