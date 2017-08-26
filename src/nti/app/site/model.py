#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.site.interfaces import ISite

from zope.mimetype.interfaces import IContentTypeAware

from nti.app.site import SITE_MIMETYPE

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties


@WithRepr
@EqHash('name',)
@interface.implementer(ISite, IContentTypeAware)
class Site(SchemaConfigured):
    createDirectFieldProperties(ISite)

    __parent__ = None
    __name__ = alias('name')

    Name = alias('name')
    Provider = alias('provider')
    
    parameters = {}  # IContentTypeAware

    mimeType = mime_type = SITE_MIMETYPE
