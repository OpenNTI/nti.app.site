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

from zc.displayname.interfaces import IDisplayNameGenerator

from zope import component
from zope import interface

from zope.component.hooks import site
from zope.component.hooks import getSite

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from zope.site.interfaces import INewLocalSite

from nti.app.site import DELETED_MARKER

from nti.app.site.interfaces import ISiteBrand
from nti.app.site.interfaces import ISiteBrandAssets
from nti.app.site.interfaces import IPersistentSiteMapping
from nti.app.site.interfaces import DuplicateSiteMappingError

from nti.appserver.brand.interfaces import ISiteAssetsFileSystemLocation

from nti.appserver.brand.utils import get_site_brand_name

from nti.appserver.interfaces import IPreferredAppHostnameProvider
from nti.appserver.interfaces import IApplicationSettings

from nti.appserver.policies.interfaces import ICommunitySitePolicyUserEventListener

from nti.dataserver.users.auto_subscribe import SiteAutoSubscribeMembershipPredicate

from nti.dataserver.users.communities import Community

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.mailer.interfaces import IMailerTemplateArgsUtility

from nti.site.interfaces import ISiteMapping
from nti.site.interfaces import IHostPolicySiteManager
from nti.site.interfaces import IMainApplicationFolder

from nti.site.utils import registerUtility
from nti.site.utils import unregisterUtility

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)


def _get_community_alias(policy):
    """
    Prefer a community alias, non 'NextThought' site brand, or 'Community'.
    """
    result = getattr(policy, 'COM_ALIAS', '')
    if not result:
        result = get_site_brand_name()
    if not result or result.lower() == 'nextthought':
        result = u'Community'
    return result


def _create_default_community(policy, community_name):
    """
    Create a default, auto-joinable community for the given site policy.
    """
    try:
        new_community = Community.create_community(username=community_name)
    except KeyError:
        # This may be common; e.g. creating a new site underneath an existing
        # one.
        logger.info("Cannot create existing community (%s)",
                    community_name)
    else:
        new_community.public = False
        new_community.joinable = False

        com_named = IFriendlyNamed(new_community)
        com_named.alias = _get_community_alias(policy)
        if getattr(policy, 'COM_REALNAME', ''):
            com_named.realname = getattr(policy, 'COM_REALNAME', '')

        new_community.auto_subscribe = SiteAutoSubscribeMembershipPredicate()
        new_community.auto_subscribe.__parent__ = new_community
        return new_community


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
            _create_default_community(policy, community_name)


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


@component.adapter(IPersistentSiteMapping, IObjectAddedEvent)
def on_site_mapping_added(site_mapping, unused_event=None):
    """
    On site mapping, globally register the site mapping. Must
    be global to be accessed correctly in site tween.
    """
    source_site_name = site_mapping.source_site_name
    current_utility = component.queryUtility(ISiteMapping,
                                             name=source_site_name)
    if current_utility is not None:
        raise DuplicateSiteMappingError(source_site_name)
    # Need to register this in persistent registry
    app_folder = find_interface(getSite(), IMainApplicationFolder)
    registerUtility(app_folder.getSiteManager(),
                    site_mapping,
                    name=source_site_name,
                    provided=ISiteMapping)


@component.adapter(IPersistentSiteMapping, IObjectRemovedEvent)
def _on_site_mapping_deleted(site_mapping, unused_event=None):
    """
    On site mapping, unregister mapping utility from global
    site manager.
    """
    app_folder = find_interface(getSite(), IMainApplicationFolder)
    unregisterUtility(app_folder.getSiteManager(),
                      provided=ISiteMapping,
                      name=site_mapping.source_site_name)


@interface.implementer(IMailerTemplateArgsUtility)
class SiteBrandMailerTemplateArgsUtility(object):
    
    @property
    def web_root(self):
        settings = component.getUtility(IApplicationSettings)
        web_root = settings.get('web_app_root', '/NextThoughtWebApp/')
        # It MUST end with a trailing slash, but we don't want that
        return web_root[:-1]

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

    def _brand_name(self, request):
        result = component.queryMultiAdapter((getSite(), request),
                                             IDisplayNameGenerator)
        # May be None in tests
        if result is not None:
            result = result()
        return result or u'NextThought'
    
    def get_template_args(self, request=None):
        """
        Return additional template args.
        """
        result = {}
        if request is None: 
            request = get_current_request()
        site_brand = component.queryUtility(ISiteBrand)
        if site_brand is not None:
            email_image_url = self._get_email_image_url(site_brand, request)
            if email_image_url:
                result['nti_site_brand_email_image_url'] = email_image_url
        result['nti_site_app_url'] = urllib_parse.urljoin(request.application_url, self.web_root)
        result['nti_site_brand_color'] = getattr(site_brand, 'brand_color', None) or '#3FB34F'
        result['nti_site_brand_name'] = self._brand_name(request)
        return result


@interface.implementer(IPreferredAppHostnameProvider)
class MostRecentSiteMappingPreferredHostnameProvider(object):

    def get_preferred_hostname(self, source_site_name):
        """
        Return the preferred host name for a particular given site name input.
        This implementation gets the most recently registered site mapping
        that points to the source_site_name input.
        """
        if not source_site_name:
            return
        result = source_site_name
        found_mappings = []
        site_mappings = component.getAllUtilitiesRegisteredFor(ISiteMapping)
        # Gather all site mappings pointing towards our input
        for site_mapping in site_mappings or ():
            if site_mapping.target_site_name == source_site_name:
                found_mappings.append(site_mapping)
        if found_mappings:
            # Get our most recent site mapping
            found_mappings = sorted(found_mappings,
                                    key=lambda x: getattr(x, 'createdTime', 0))
            result = found_mappings[0].source_site_name
        return result
