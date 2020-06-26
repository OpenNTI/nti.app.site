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
from nti.app.site import VIEW_SITE_MAPPINGS

from nti.app.site.interfaces import ISiteBrand
from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import ISiteMappingContainer
from nti.app.site.interfaces import IPersistentSiteMapping

from nti.appserver.brand.model import SiteBrand

from nti.appserver.brand.interfaces import ISiteAssetsFileSystemLocation

from nti.appserver.workspaces.interfaces import IUserWorkspaceLinkProvider

from nti.dataserver.authorization import is_admin
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
        rels = [VIEW_SITE_ADMINS, VIEW_SITE_MAPPINGS]
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

    def _predicate(self, unused_context, unused_result):
        # Ignore context because we may have a different edit context
        return  self._is_authenticated \
            and is_admin_or_site_admin(self.remoteUser)

    @staticmethod
    def _current_site_sitebrand():
        # For editing the site brand, we want to edit our current
        # site's SiteBrand, if it exists. Otherwise, fall back and
        # expose the edit href of this site brand.
        sm = component.getSiteManager()
        edit_context = sm.get('SiteBrand')
        if edit_context is None:
            # Ok, the current site does not have a SiteBrand, build one for
            # our links
            edit_context = SiteBrand()
            edit_context.__name__ = 'SiteBrand'
            edit_context.__parent__ = sm
        return edit_context

    @staticmethod
    def _can_edit_sitebrand():
        return component.queryUtility(ISiteAssetsFileSystemLocation)

    def _do_decorate_external(self, unused_context, result_map):
        edit_context = self._current_site_sitebrand()
        links = result_map.setdefault("Links", [])
        if is_admin(self.remoteUser):
            # Only NT admins get delete rel
            link = Link(edit_context,
                        rel='delete',
                        method='DELETE')
            links.append(link)
        # Can only edit with a fs location
        if self._can_edit_sitebrand() is not None:
            link = Link(edit_context,
                        rel='edit',
                        method='PUT')
            links.append(link)


@component.adapter(IPersistentSiteMapping, IRequest)
@interface.implementer(IExternalObjectDecorator)
class PersistentSiteMappingAdminDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, unused_context, unused_result):
        return is_admin(self.remoteUser)

    def _do_decorate_external(self, context, result_map):
        links = result_map.setdefault("Links", [])
        link = Link(context,
                    rel='delete',
                    method="DELETE")
        links.append(link)


@component.adapter(ISiteMappingContainer, IRequest)
@interface.implementer(IExternalObjectDecorator)
class SiteMappingContainerAdminDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, unused_context, unused_result):
        return is_admin(self.remoteUser)

    def _do_decorate_external(self, context, result_map):
        links = result_map.setdefault("Links", [])
        link = Link(context,
                    rel='insert',
                    method="POST")
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


@component.adapter(ISiteBrand)
@interface.implementer(IExternalObjectDecorator)
class SiteBrandHideNextThoughtBrandingDecorator(Singleton):
    """
    For sites that do not want their nextthought branding, we provide this
    decorator that will decorate an informational attr on the SiteBrand.
    """

    def decorateExternalObject(self, unused_context, external):
        # For speed, we decorate this for everyone
        external['HideNextThoughtBranding'] = True


@component.adapter(ISiteBrand)
@interface.implementer(IExternalObjectDecorator)
class SiteBrandHideCertificateStylingDecorator(Singleton):
    """
    For sites that override the default completion certificate template,
    we provide this decorator to hide the certificate customizations used
    in that template.
    """

    def decorateExternalObject(self, unused_context, external):
        # For speed, we decorate this for everyone
        external['HideCertificateStyling'] = True


@component.adapter(ISiteSeatLimit)
@interface.implementer(IExternalObjectDecorator)
class SiteSeatLimitDecorator(Singleton):

    def decorateExternalObject(self, context, external):
        external['hard'] = context.hard
