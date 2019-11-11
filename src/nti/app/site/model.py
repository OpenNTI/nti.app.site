#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from persistent import Persistent

from persistent.mapping import PersistentMapping

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy
from zope.cachedescriptors.property import CachedProperty

from zope.component.hooks import getSite

from zope.container.contained import Contained

from zope.mimetype.interfaces import IContentTypeAware

from zope.schema.fieldproperty import createFieldProperties

from zope.traversing.api import joinPath

from nti.app.site.interfaces import ISite
from nti.app.site.interfaces import ISiteBrand
from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import ISiteBrandImage
from nti.app.site.interfaces import ISiteBrandAssets
from nti.app.site.interfaces import ISiteAssetsFileSystemLocation

from nti.app.site import SITE_MIMETYPE

from nti.appserver.policies.interfaces import ISitePolicyUserEventListener

from nti.base.mixins import CreatedAndModifiedTimeMixin

from nti.coremetadata.interfaces import IDataserver

from nti.dataserver.users.utils import intids_of_users_by_site

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

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


class SiteBrandTheme(PersistentMapping,
                     PersistentCreatedAndModifiedTimeObject):

    __parent__ = None

    # Leave these at 0 until they get set externally
    _SET_CREATED_MODTIME_ON_INIT = False


@WithRepr
@interface.implementer(ISiteBrand)
class SiteBrand(PersistentCreatedAndModifiedTimeObject,
                SchemaConfigured):

    createDirectFieldProperties(ISiteBrand)

    __parent__ = None
    __name__ = alias('Name')

    _theme = None

    creator = None
    name = alias('Name')
    mimeType = mime_type = 'application/vnd.nextthought.sitebrand'

    @property
    def theme(self):
        return dict(self._theme) if self._theme else {}

    @theme.setter
    def theme(self, nv):
        pass

    @Lazy
    def brand_name(self):
        policy = component.queryUtility(ISitePolicyUserEventListener)
        return getattr(policy, 'BRAND', '')


@WithRepr
@interface.implementer(ISiteBrandAssets)
class SiteBrandAssets(PersistentCreatedAndModifiedTimeObject,
                      SchemaConfigured):

    createDirectFieldProperties(ISiteBrandAssets)

    __parent__ = None
    __name__ = 'SiteBrandAssets'

    creator = None
    mimeType = mime_type = 'application/vnd.nextthought.sitebrandassets'


@WithRepr
@interface.implementer(ISiteBrandImage)
class SiteBrandImage(PersistentCreatedAndModifiedTimeObject,
                     SchemaConfigured):

    createDirectFieldProperties(ISiteBrandAssets)

    __parent__ = None
    __name__ = alias('Name')

    creator = None
    name = alias('Name')
    mimeType = mime_type = 'application/vnd.nextthought.sitebrandimage'

    @property
    def href(self):
        result = self.source
        if self.key is not None:
            # If we have a key, we are a relative path to a disk location.
            # Otherwise, we are empty or have a full URL to an external image.
            location = component.queryUtility(ISiteAssetsFileSystemLocation)
            if location is not None and self.__parent__:
                asset_part = self.__parent__.root.name
                __traceback_info__ = location.prefix, asset_part, self.key.name
                prefix = location.prefix
                if prefix.startswith('/'):
                    prefix = prefix[1:]
                if prefix.endswith('/'):
                    prefix = prefix[:-1]
                result = joinPath('/', prefix, self.key.name)
        return result

    @href.setter
    def href(self, nv):
        pass

