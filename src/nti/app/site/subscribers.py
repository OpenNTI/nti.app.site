# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from pyramid.threadlocal import get_current_request

from six.moves import urllib_parse

from zope import component
from zope import interface

from zope.component.hooks import site

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from zope.site.interfaces import INewLocalSite

from nti.app.site import DELETED_MARKER

from nti.app.site.interfaces import ISiteBrand
from nti.app.site.interfaces import ISiteBrandAssets
from nti.app.site.interfaces import ISiteAssetsFileSystemLocation

from nti.appserver.policies.interfaces import ICommunitySitePolicyUserEventListener

from nti.dataserver.users.auto_subscribe import SiteAutoSubscribeMembershipPredicate

from nti.dataserver.users.communities import Community

from nti.mailer.interfaces import IMailerTemplateArgsUtility

from nti.site.interfaces import IHostPolicySiteManager

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicySiteManager, INewLocalSite)
def _on_site_created(new_site_manager, unused_event=None):
    """
    On site creation, create a site community that auto-subscribes new users.

    XXX: Long term, we will set up subscribers based on SitePolicyEventListener
    objects created/modified.
    """
    with site(new_site_manager.__parent__):
        policy = new_site_manager.queryUtility(ICommunitySitePolicyUserEventListener)
        community_name = getattr(policy, 'COM_USERNAME', None)
        if community_name:
            try:
                new_community = Community.create_community(username=community_name)
            except KeyError:
                # This may be common; e.g. creating a new site underneath an existing
                # one.
                logger.info("Cannot create existing community (%s)",
                            community_name)
            else:
                new_community.auto_subscribe = SiteAutoSubscribeMembershipPredicate()
                new_community.auto_subscribe.__parent__ = new_community


@component.adapter(ISiteBrand, IObjectRemovedEvent)
def _on_site_brand_deleted(site_brand, unused_event=None):
    """
    On site brand removal, clean up on-disk assets by marking
    the location as deleted (for NFS).
    """
    if site_brand.assets is not None:
        _on_site_assets_deleted(site_brand.assets)


@component.adapter(ISiteBrandAssets, IObjectRemovedEvent)
def _on_site_assets_deleted(site_brand_assets, unused_event=None):
    """
    On site brand removal, clean up on-disk assets by marking
    the location as deleted (for NFS).
    """
    asset_name = site_brand_assets.root is not None and site_brand_assets.root.name
    if asset_name is not None:
        location = component.queryUtility(ISiteAssetsFileSystemLocation)
        if location is not None:
            bucket_path = os.path.join(location.directory, asset_name)
            if os.path.exists(bucket_path):
                # If no path, we can skip this part
                path = os.path.join(bucket_path, DELETED_MARKER)
                open(path, 'w').close()


@interface.implementer(IMailerTemplateArgsUtility)
class SiteBrandMailerTemplateArgsUtility(object):

    def _get_email_image_url(self, site_brand, request):
        result = None
        assets = site_brand.assets
        if assets is not None:
            if      assets.email \
                and assets.email.href:
                result = assets.email.href

            if      not result \
                and assets.logo \
                and assets.logo.href:
                # Fall back to logo if present
                result = assets.logo.href

            if result is not None:
                if request is None:
                    request = get_current_request()
                if request is not None:
                    result = urllib_parse.urljoin(request.application_url, result)
        return result

    def get_template_args(self, request=None):
        """
        Return additional template args.
        """
        result = {}
        site_brand = component.queryUtility(ISiteBrand)
        if site_brand is not None:
            if site_brand.brand_name:
                result['nti_site_brand_name'] = site_brand.brand_name
            email_image_url = self._get_email_image_url(site_brand, request)
            if email_image_url:
                result['nti_site_brand_email_image_url'] = email_image_url
        result['nti_site_brand_color'] = getattr(site_brand, 'brand_color', None) or '#89be3c'
        return result
