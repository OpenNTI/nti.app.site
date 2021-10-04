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

from zope.cachedescriptors.property import Lazy

from zope.location.interfaces import IContained

from nti.appserver.workspaces.interfaces import IGlobalWorkspaceLinkProvider
from nti.appserver.workspaces.interfaces import IUserService

from nti.app.site import SITE_ADMIN
from nti.app.site import SITE_SEAT_LIMIT

from nti.app.site.workspaces.interfaces import ISiteAdminCollection
from nti.app.site.workspaces.interfaces import ISiteAdminWorkspace

from nti.coremetadata.interfaces import IUser

from nti.dataserver.authorization import is_admin_or_site_admin
from nti.dataserver.authorization import is_admin_or_content_admin_or_site_admin

from nti.property.property import alias

from nti.dataserver.interfaces import IDataserverFolder

from nti.links import Link

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ISiteAdminWorkspace, IContained)
class _SiteAdminWorkspace(object):

    __parent__ = None
    __name__ = SITE_ADMIN

    name = alias('__name__')

    def __init__(self, user_service):
        self.context = user_service
        self.user = user_service.user

    @Lazy
    def collections(self):
        """
        The returned collections are sorted by name.
        """
        result = []
        for collection in component.subscribers((self,), ISiteAdminCollection):
            result.append(collection)
        return sorted(result, key=lambda x: x.name)

    @property
    def links(self):
        return ()

    def __getitem__(self, key):
        """
        Make us traversable to collections.
        """
        # pylint: disable=not-an-iterable
        for i in self.collections:
            if i.__name__ == key:
                return i
        raise KeyError(key)  # pragma: no cover

    def __len__(self):
        pass

    def predicate(self):
        return is_admin_or_content_admin_or_site_admin(self.user)


@interface.implementer(ISiteAdminWorkspace)
@component.adapter(IUserService)
def SiteAdminWorkspace(user_service):
    workspace = _SiteAdminWorkspace(user_service)
    if workspace.predicate():
        workspace.__parent__ = workspace.user
        return workspace


@component.adapter(IUser)
@interface.implementer(IGlobalWorkspaceLinkProvider)
class _GlobalWorkspaceSiteSeatLimitLinkProvider(object):

    def __init__(self, user):
        self.user = user

    def links(self, unused_workspace):
        if is_admin_or_site_admin(self.user):
            ds2 = find_interface(self.user, IDataserverFolder)
            link = Link(ds2, rel=SITE_SEAT_LIMIT,
                        elements=(SITE_SEAT_LIMIT,))
            return [link]
        return ()
