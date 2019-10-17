# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.site.interfaces import INewLocalSite

from nti.appserver.policies.interfaces import ICommunitySitePolicyUserEventListener

from nti.dataserver.users.auto_subscribe import SiteAutoSubscribeMembershipPredicate

from nti.dataserver.users.communities import Community

from nti.site.interfaces import IHostPolicySiteManager

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicySiteManager, INewLocalSite)
def _on_site_created(new_site_manager, unused_event=None):
    """
    On site creation, create a site community that auto-subscribes
    new users.

    XXX: Long term, we will set up subscribers based on SitePolicyEventListener
    objects created/modified.
    """
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
