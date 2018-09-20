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

from zope.annotation.interfaces import IAnnotations

from zope.interface.interfaces import ComponentLookupError

from zope.site.interfaces import IFolder

from nti.app.site import SITE_PROVIDER

from nti.app.site.interfaces import NTI
from nti.app.site.interfaces import ISite

from nti.app.site.model import Site

from nti.appserver.policies.interfaces import ISitePolicyUserEventListener

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.interfaces import ICommunity

from nti.dataserver.users.communities import Community

from nti.site.hostpolicy import get_host_site

logger = __import__('logging').getLogger(__name__)


def site_manager(folder):
    try:
        result = folder.getSiteManager()
    except (AttributeError, ComponentLookupError):
        result = component.getSiteManager()
    return result


@component.adapter(IFolder)
@interface.implementer(ICommunity)
def _folder_to_community(folder):
    result = None
    registry = site_manager(folder)
    site_policy = registry.queryUtility(ISitePolicyUserEventListener)
    community_username = getattr(site_policy, 'COM_USERNAME', '')
    if community_username:
        result = Community.get_community(community_username)
    return result


def site_provider(folder):
    annots = IAnnotations(folder, None)
    provider = annots.get(SITE_PROVIDER) if annots else None
    if not provider:
        registry = site_manager(folder)
        site_policy = registry.queryUtility(ISitePolicyUserEventListener)
        provider = getattr(site_policy, SITE_PROVIDER, '')
    return provider


@component.adapter(IFolder)
@interface.implementer(ISite)
def _folder_to_site(folder):
    result = Site()
    result.Name = folder.__name__
    result.Provider = site_provider(folder) or NTI
    if ICreated.providedBy(folder):
        result.creator = folder.creator
    if ILastModified.providedBy(folder):
        result.createdTime = folder.createdTime
        result.lastModified = folder.lastModified
    return result


@component.adapter(ISite)
@interface.implementer(IFolder)
def _site_to_folder(site):
    return get_host_site(site.Name, True)
