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

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.externalization import to_external_object

from nti.ntiids.oids import to_external_ntiid_oid

from nti.site.interfaces import ISiteMapping
from nti.site.interfaces import IHostPolicyFolder

OID = StandardExternalFields.OID
CLASS = StandardExternalFields.CLASS
NTIID = StandardExternalFields.NTIID
MIMETYPE = StandardExternalFields.MIMETYPE

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


@component.adapter(ISiteMapping)
@interface.implementer(IInternalObjectExternalizer)
class _SiteMappingExternalizer(object):

    def __init__(self, obj):
        self.site_mapping = obj

    def toExternalObject(self, *args, **kwargs):
        result = LocatedExternalDict()
        result[MIMETYPE] = self.site_mapping.mimeType
        result[CLASS] = self.site_mapping.__class__.__name__
        result['source'] = self.site_mapping.source_site_name
        result['target'] = self.site_mapping.target_site_name
        result[NTIID] = result[OID] = to_external_ntiid_oid(self.site_mapping)
        return result
