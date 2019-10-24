#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: decorators.py 125436 2018-01-11 20:05:13Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRequest

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.app.site.workspaces.interfaces import ISiteAdminWorkspace

from nti.app.site import VIEW_SITE_BRAND
from nti.app.site import VIEW_SITE_ADMINS

from nti.app.site.interfaces import ISiteBrandAssets

from nti.appserver.workspaces.interfaces import IUserWorkspaceLinkProvider

from nti.dataserver.authorization import is_admin_or_site_admin

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import Singleton

from nti.links.links import Link

from nti.traversal.traversal import find_interface

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ISiteAdminWorkspace, IRequest)
@interface.implementer(IExternalObjectDecorator)
class SiteAdminWorkspaceDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, unused_context, unused_result):
        return is_admin_or_site_admin(self.remoteUser)

    def _do_decorate_external(self, context, result_map):  # pylint: disable=arguments-differ
        links = result_map.setdefault("Links", [])
        rels = [VIEW_SITE_ADMINS]
        ds2 = find_interface(context, IDataserverFolder)
        for rel in rels:
            link = Link(ds2,
                        rel=rel,
                        elements=("%s" % rel,))
            links.append(link)
        # Can edit site brand
        link = Link(ds2,
                    rel=VIEW_SITE_BRAND,
                    method="PUT",
                    elements=("%s" % VIEW_SITE_BRAND,))
        links.append(link)


@component.adapter(ISiteBrandAssets)
@interface.implementer(IExternalObjectDecorator)
class SiteBrandAssetsDecorator(Singleton):
    """
    The `logo` is the base image. Decorate this URL to all other
    image URLs that are None.
    """

    TARGET_ATTRS = ('icon', 'full_logo', 'email', 'favicon')

    def decorateExternalObject(self, unused_context, external):
        logo_ext = external.get('logo')
        if logo_ext:
            for attr in self.TARGET_ATTRS:
                attr_ext = external.get(attr)
                if not attr_ext or not attr_ext.get('source'):
                    external[attr] = logo_ext


@component.adapter(IUser)
@interface.implementer(IUserWorkspaceLinkProvider)
class _UserSiteBrandLinkProvider(object):

    def __init__(self, user):
        self.user = user

    def links(self, unused_workspace):
        ds2 = find_interface(self.user, IDataserverFolder)
        link = Link(ds2,
                    rel=VIEW_SITE_BRAND,
                    elements=("%s" % VIEW_SITE_BRAND,))
        return (link,)
