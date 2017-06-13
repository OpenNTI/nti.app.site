#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.traversing.interfaces import IPathAdapter

from pyramid import httpexceptions as hexc

from nti.app.site.interfaces import ACT_SITE_ADMIN

from nti.dataserver.authorization import ROLE_ADMIN

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.site.hostpolicy import get_host_site


@interface.implementer(IPathAdapter)
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
                ace_allowing(ACT_SITE_ADMIN, ALL_PERMISSIONS, type(self))]
        return acl_from_aces(aces)
