#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from persistent import Persistent

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.container.contained import Contained
from zope.interface.interfaces import ComponentLookupError

from zope.schema.fieldproperty import createFieldProperties

from nti.app.site.interfaces import ISite
from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import ISiteSeatLimitAlgorithm

from zope.mimetype.interfaces import IContentTypeAware

from nti.app.site import SITE_MIMETYPE

from nti.base.mixins import CreatedAndModifiedTimeMixin

from nti.dataserver.users.utils import intids_of_users_by_site

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


SITE_SEAT_LIMIT_TRAVERSAL_NAME = '++etc++nti.SiteSeatLimit'


@interface.implementer(ISiteSeatLimit)
class SiteSeatLimit(Persistent, Contained):

    __name__ = SITE_SEAT_LIMIT_TRAVERSAL_NAME
    # omit used seats so we don't try to access during startup
    createFieldProperties(ISiteSeatLimit, omit=('used_seats',))

    @property
    def used_seats(self):
        algorithm = component.queryMultiAdapter((getSite(), self), ISiteSeatLimitAlgorithm, name=self.seat_algorithm)
        if algorithm is None and self.seat_algorithm != '':
            # We were set to a custom algorithm that was unregistered
            # Fallback to default
            logger.debug(u'Unable to find multi adapter %s for site seat limit.'
                         u' Falling back to default' % self.seat_algorithm)
            self.seat_algorithm = ''
            algorithm = component.getMultiAdapter((getSite(), self), ISiteSeatLimitAlgorithm, name=self.seat_algorithm)
        elif algorithm is None:
            # Tried for default and didn't find
            raise ComponentLookupError
        return algorithm.used_seats()


class DefaultSiteSeatLimitAlgorithm(object):

    def __init__(self, site, seat_limit):
        self.current_site = site
        self.seat_limit = seat_limit

    def used_seats(self, *args, **kwargs):
        user_ids = intids_of_users_by_site(self.current_site)
        return len(user_ids)  # Includes site admins
