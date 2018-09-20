#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.app.site.interfaces import ISite

from zope.mimetype.interfaces import IContentTypeAware

from nti.app.site import SITE_MIMETYPE

from nti.base.mixins import CreatedAndModifiedTimeMixin

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@WithRepr
@EqHash('name',)
@interface.implementer(ISite, IContentTypeAware)
class Site(CreatedAndModifiedTimeMixin, SchemaConfigured):
    createDirectFieldProperties(ISite)

    __parent__ = None
    __name__ = alias('Name')

    creator = None
    name = alias('Name')
    provider = alias('Provider')
    
    parameters = {}  # IContentTypeAware

    mimeType = mime_type = SITE_MIMETYPE
