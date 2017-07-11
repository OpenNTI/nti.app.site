#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from nti.app.site.authorization import is_site_admin

from nti.appserver.workspaces.interfaces import IUserService

from nti.app.site import SITE_ADMIN

from nti.app.site.interfaces import ISiteAdminWorkspace

from nti.dataserver.authorization import is_admin

from nti.property.property import alias


@interface.implementer(ISiteAdminWorkspace)
class _SiteAdminWorkspace(Contained):

    __name__ = SITE_ADMIN

    name = alias('__name__', __name__)

    def __init__(self, user_service):
        self.context = user_service
        self.user = user_service.user

    @Lazy
    def collections(self):
        return ()  # temp val, until we know what we need

    @property
    def links(self):
        return ()  # temp val

    def __getitem__(self, key):
        pass

    def __len__(self):
        pass

    def predicate(self):
        return is_admin(self.user) or is_site_admin(self.user)


@interface.implementer(ISiteAdminWorkspace)
@component.adapter(IUserService)
def SiteAdminWorkspace(user_service):
    workspace = _SiteAdminWorkspace(user_service)
    if workspace.predicate():
        workspace.__parent__ = workspace.user
        return workspace
