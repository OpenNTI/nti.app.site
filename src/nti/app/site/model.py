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

from nti.app.site.interfaces import ISite
from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import ISiteMappingContainer
from nti.app.site.interfaces import ISiteAdminSeatUserProvider
from nti.app.site.interfaces import ISiteAdminSeatUserLimitUtility

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
from nti.app.site.interfaces import SiteAdminSeatLimitExceededError

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

    hard = alias('hard_limit')

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
        # This includes site admins
        user_ids = intids_of_users_by_site(self.current_site)
        return len(user_ids)

    def __repr__(self):
        return "<%s (max_seats=%s) (max_admin_seats=%s)>" % (self.__class__.__name__,
                                                             self.max_seats,
                                                             self.max_admin_seats)

    @property
    def admin_used_seats(self):
        return len(self.get_admin_seat_users())

    def get_admin_seat_users(self):
        """
        Returns an iterable of admin users.
        """
        result = set()
        providers = component.getAllUtilitiesRegisteredFor(ISiteAdminSeatUserProvider)
        for provider in providers:
            result.update(provider.iter_users())
        return result

    def get_admin_seat_usernames(self):
        """
        Returns an iterable of admin usernames.
        """
        admin_users = self.get_admin_seat_users()
        return [x.username for x in admin_users]

    def _get_admin_seat_limit(self):
        """
        Get the admin seat limit. That may come from us or from the
        :class:`ISiteAdminSeatUserLimitUtility`.
        """
        admin_seat_limit = self.max_admin_seats
        if admin_seat_limit is None:
            admin_limit_utility = component.queryUtility(ISiteAdminSeatUserLimitUtility)
            if admin_limit_utility:
                admin_seat_limit = admin_limit_utility.get_admin_seat_limit()
        return admin_seat_limit

    def can_add_admin(self):
        """
        Returns a bool indicating whether a new admin can be added.
        """
        if not self.hard_admin_limit:
            return True
        admin_seat_limit = self._get_admin_seat_limit()
        # If no limit specified, we default to anything goes.
        return admin_seat_limit is None \
            or admin_seat_limit > self.admin_used_seats

    def validate_admin_seats(self):
        """
        Validates that the site admin seats have not been exceeded, raising
        a :class:`SiteAdminSeatLimitExceeded`.
        """
        if not self.hard_admin_limit:
            return
        admin_seat_limit = self._get_admin_seat_limit()
        # If no limit specified, we default to anything goes.
        admin_used_seats = self.admin_used_seats
        if      admin_seat_limit is not None \
            and admin_seat_limit < admin_used_seats:
            msg = "Admin seats exceeded. {used} used out of {available} available".format(used=admin_used_seats,
                                                                                          available=admin_seat_limit)
            raise SiteAdminSeatLimitExceededError(msg)


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
    mimeType = mime_type = 'application/vnd.nextthought.persistentsitemapping'

    __external_class_name__ = "SiteMapping"

    createDirectFieldProperties(IPersistentSiteMapping)

    __parent__ = None
    __name__ = None

    creator = None
    NTIID = alias('ntiid')

    def __repr__(self):
        return "<%s (source=%s) (target=%s)>" % (self.__class__.__name__,
                                                 self.source_site_name,
                                                 self.target_site_name)


zope.deferredimport.deprecatedFrom(
    "Moved to nti.appserver.brand.model",
    "nti.appserver.brand.model",
    "SiteBrand",
    "SiteBrandImage",
    "SiteBrandAssets")
