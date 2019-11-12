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

from nti.app.site.interfaces import ISiteBrand
from nti.appserver.brand.interfaces import ISiteAssetsFileSystemLocation

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.workspaces.interfaces import IUserWorkspaceLinkProvider

from nti.dataserver.authorization import ACT_CONTENT_EDIT

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


@component.adapter(ISiteBrand, IRequest)
@interface.implementer(IExternalObjectDecorator)
class SiteBrandAuthDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, unused_result):
        return  self._is_authenticated \
            and has_permission(ACT_CONTENT_EDIT, context, self.request)

    def _do_decorate_external(self, context, result_map):
        links = result_map.setdefault("Links", [])
        link = Link(context,
                    rel='delete',
                    method='DELETE')
        links.append(link)
        # Can only edit with a fs location
        if component.queryUtility(ISiteAssetsFileSystemLocation) is not None:
            link = Link(context,
                        rel='edit',
                        method='PUT')
            links.append(link)



@component.adapter(ISiteBrand)
@interface.implementer(IExternalObjectDecorator)
class SiteBrandEmailDisabledDecorator(Singleton):
    """
    For sites that do not want their custom email image overrideable via the
    UI, we provide this decorator that will decorate an informational attr on
    the SiteBrand.
    """

    def decorateExternalObject(self, unused_context, external):
        # For speed, we decorate this for everyone
        external['UneditableEmailImage'] = True
