# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from zope import component

from zope.component.hooks import site

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from zope.site.interfaces import INewLocalSite

from nti.app.site import DELETED_MARKER

from nti.app.site.interfaces import ISiteBrand

from nti.app.site.model import SiteBrand

from nti.appserver.policies.interfaces import ICommunitySitePolicyUserEventListener

from nti.dataserver.users.auto_subscribe import SiteAutoSubscribeMembershipPredicate

from nti.dataserver.users.communities import Community

from nti.site.interfaces import IHostPolicySiteManager

from nti.site.localutility import install_utility

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicySiteManager, INewLocalSite)
def _on_site_created(new_site_manager, unused_event=None):
    """
    On site creation, create a site community that auto-subscribes new users.
    Also configures a SiteBrand for the new site.

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

        brand_name = new_site_manager.__parent__.__name__
        site_brand = SiteBrand(brand_name=brand_name)
        install_utility(site_brand,
                        'SiteBrand',
                        ISiteBrand,
                        new_site_manager)


@component.adapter(ISiteBrand, IObjectRemovedEvent)
def _on_site_brand_deleted(site_brand, unused_event=None):
    """
    On site brand removal, clean up on-disk assets by marking
    the location as deleted (for NFS).
    """
    bucket = site_brand.assets and site_brand.assets.root
    if bucket is not None:
        path = os.path.join(bucket.key, DELETED_MARKER)
        open(path, 'w').close()
