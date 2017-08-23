#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.site.interfaces import IFolder

from nti.appserver.policies.interfaces import ISitePolicyUserEventListener

from nti.dataserver.interfaces import ICommunity

from nti.dataserver.users.communities import Community


@component.adapter(IFolder)
@interface.implementer(ICommunity)
def _site_to_community(site):
    result = None
    site_policy = component.queryUtility(ISitePolicyUserEventListener)
    community_username = getattr(site_policy, 'COM_USERNAME', '')
    if community_username:
        result = Community.get_community(community_username)
    if result is None:
        result = Community.get_community(site.__name__)
    return result
