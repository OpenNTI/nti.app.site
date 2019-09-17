# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.appserver.policies.interfaces import ICommunitySitePolicyUserEventListener

from nti.dataserver.users.auto_subscribe import SiteAutoSubscribeMembershipPredicate

from nti.dataserver.users.communities import Community

from nti.site.interfaces import IHostPolicyFolder

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicyFolder, IObjectCreatedEvent)
def _on_site_created(unused_new_site, unused_event=None):
    """
    On site creation, create a site community that auto-subscribes
    new users.

    XXX: Long term, we will set up subscribers based on SitePolicyEventListener
    objects created/modified.
    """
    site = component.queryUtility(ICommunitySitePolicyUserEventListener)
    community_name = getattr(site, 'COM_USERNAME', None)
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
