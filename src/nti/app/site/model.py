#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import zope.deferredimport

from persistent import Persistent

from zope import component
from zope import interface

from zope.cachedescriptors.property import CachedProperty

from zope.component.hooks import getSite

from zope.container.contained import Contained

from zope.mimetype.interfaces import IContentTypeAware

from zope.schema.fieldproperty import createFieldProperties

from nti.app.site.interfaces import ISite, ISiteMappingContainer
from nti.app.site.interfaces import ISiteSeatLimit

from nti.app.site import SITE_MIMETYPE

from nti.base.mixins import CreatedAndModifiedTimeMixin

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IDataserver

from nti.dataserver.users.utils import intids_of_users_by_site

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.app.site.interfaces import IPersistentSiteMapping

from nti.site.site import SiteMapping

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

    # Because this will be updated on any user CUD in any site
    # it is likely a minimal gain
    @property
    def lastModified(self):
        ds = component.getUtility(IDataserver)
        users_folder = ds.users_folder
        return users_folder.lastModified

    @property
    def current_site(self):
        return getSite().__name__

    @CachedProperty('lastModified', 'current_site')
    def used_seats(self):
        user_ids = intids_of_users_by_site(self.current_site)
        return len(user_ids)  # Includes site admins


    def __repr__(self):
        return "<%s (source=%s) (target=%s)>" % (self.__class__.__name__,
                                                 self.source_site_name,
                                                 self.target_site_name)


@interface.implementer(ISiteMappingContainer)
class SiteMappingContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                           SchemaConfigured):
    createDirectFieldProperties(ISiteMappingContainer)

    __parent__ = None

    def get_site_mapping(self, source_site_name):
        return self.get(source_site_name)

    def add_site_mapping(self, site_mapping):
        result = self.get_site_mapping(site_mapping.source_site_name)
        if result is not None:
            return result
        self[site_mapping.source_site_name] = site_mapping
        return site_mapping


@WithRepr
@interface.implementer(IPersistentSiteMapping)
class PersistentSiteMapping(PersistentCreatedAndModifiedTimeObject,
                            SiteMapping,
                            Contained,
                            SchemaConfigured):
    """
    Maps one site to another persistently.
    """
    createDirectFieldProperties(IPersistentSiteMapping)

    __parent__ = None
    __name__ = None

    creator = None
    NTIID = alias('ntiid')


zope.deferredimport.deprecatedFrom(
    "Moved to nti.appserver.brand.model",
    "nti.appserver.brand.model",
    "SiteBrand",
    "SiteBrandImage",
    "SiteBrandAssets")
