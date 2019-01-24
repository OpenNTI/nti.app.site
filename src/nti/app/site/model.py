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

from zope.cachedescriptors.property import CachedProperty

from zope.component.hooks import getSite

from zope.intid import IIntIds

from zope.schema.fieldproperty import createFieldProperties

from nti.app.site.interfaces import ISite
from nti.app.site.interfaces import ISiteSeatLimit

from zope.mimetype.interfaces import IContentTypeAware

from nti.app.site import SITE_MIMETYPE

from nti.base.mixins import CreatedAndModifiedTimeMixin

from nti.coremetadata.interfaces import IDataserver

from nti.dataserver.authorization import is_admin_or_content_admin_or_site_admin

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


@interface.implementer(ISiteSeatLimit)
class SiteSeatLimit(Persistent):

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
        intids = component.getUtility(IIntIds)
        num_users = 0
        for user_id in user_ids:
            user = intids.queryObject(user_id)
            if user is not None and not is_admin_or_content_admin_or_site_admin(user.username):
                num_users += 1
        return num_users
