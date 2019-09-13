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

from zope.traversing.interfaces import IPathAdapter

from pyramid import httpexceptions as hexc

from pyramid.view import IRequest

from nti.appserver.workspaces.interfaces import IUserService

from nti.app.site.authorization import ROLE_SITE_ADMIN

from nti.app.site.workspaces.workspaces import ISiteAdminWorkspace

from nti.dataserver.authorization import ROLE_ADMIN

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.dataserver.interfaces import IUser

from nti.site.hostpolicy import get_host_site

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
@component.adapter(IUser, IRequest)
def SiteAdminWorkspacePathAdapter(context, unused_request):
    service = IUserService(context)
    workspace = ISiteAdminWorkspace(service, None)
    return workspace


@interface.implementer(IPathAdapter, IContained)
class SitesPathAdapter(object):

    __parent__ = None
    __name__ = 'sites'

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context

    def __getitem__(self, name):
        if not name:
            raise hexc.HTTPNotFound()
        result = get_host_site(name, safe=True)
        if result is None:
            raise KeyError(name)
        return result

    @Lazy
    def __acl__(self):
        aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, type(self)),
                ace_allowing(ROLE_SITE_ADMIN, ALL_PERMISSIONS, type(self))]
        return acl_from_aces(aces)
