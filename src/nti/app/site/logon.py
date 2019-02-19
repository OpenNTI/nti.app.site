#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__docformat__ = "restructuredtext en"

from persistent import Persistent

from zope import component
from zope import interface

from zope.container.contained import Contained

from pyramid.interfaces import IRequest

from nti.appserver.logon import REL_LOGIN_GOOGLE
from nti.appserver.logon import GOOGLE_OAUTH_EXTERNAL_ID_TYPE

from nti.appserver.interfaces import ILogonLinkProvider
from nti.appserver.interfaces import IGoogleLogonSettings
from nti.appserver.interfaces import IGoogleLogonLookupUtility
from nti.appserver.interfaces import IUnauthenticatedUserLinkProvider

from nti.dataserver.interfaces import IMissingUser

from nti.dataserver.users import User

from nti.dataserver.users.interfaces import IUsernameGeneratorUtility

from nti.identifiers.utils import get_user_for_external_id

from nti.links.links import Link


@component.adapter(IRequest)
@interface.implementer(IUnauthenticatedUserLinkProvider)
class SimpleUnauthenticatedUserGoogleLinkProvider(object):

    rel = REL_LOGIN_GOOGLE

    def __init__(self, request):
        self.request = request

    def get_links(self):
        elements = (self.rel,)
        root = self.request.route_path('objects.generic.traversal',
                                       traverse=())
        root = root[:-1] if root.endswith('/') else root
        return [Link(root, elements=elements, rel=self.rel)]


@interface.implementer(ILogonLinkProvider)
@component.adapter(IMissingUser, IRequest)
class SimpleMissingUserGoogleLinkProvider(SimpleUnauthenticatedUserGoogleLinkProvider):

    def __init__(self, user, request):
        super(SimpleMissingUserGoogleLinkProvider, self).__init__(request)
        self.user = user

    def __call__(self):
        links = self.get_links()
        return links[0] if links else None


@interface.implementer(IGoogleLogonLookupUtility)
class GoogleLogonLookupUtility(Persistent, Contained):

    def __init__(self, use_gmail=True):
        self.use_gmail = use_gmail

    def lookup_user(self, identifier):
        if self.use_gmail:
            return User.get_user(identifier)
        # When a user login a child site, then login its parent or sibling site with the same GMail,
        # it would create duplicated users with the same GMail, which may cause a different user returned
        # when login the child site with that gmail.
        # fix get_user_for_external_id?
        user = get_user_for_external_id(GOOGLE_OAUTH_EXTERNAL_ID_TYPE, identifier)
        return user

    def generate_username(self, identifier):
        if self.use_gmail:
            return identifier
        username_util = component.getUtility(IUsernameGeneratorUtility)
        return username_util.generate_username()


@interface.implementer(IGoogleLogonSettings)
class GoogleLogonSettings(Persistent, Contained):

    def __init__(self, hd):
        self.hd = hd
