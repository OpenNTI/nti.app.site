#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import Allow
from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.users import User

logger = __import__('logging').getLogger(__name__)


def get_site_admins(site=None):
    """
    Returns all site admins.
    """
    result = []
    site = getSite() if site is None else site
    try:
        srm = IPrincipalRoleManager(site, None)
    except TypeError:
        # SiteManagerContainer (tests)
        srm = None
    if srm is not None:
        for prin_id, access in srm.getPrincipalsForRole(ROLE_SITE_ADMIN.id):
            if access == Allow:
                user = User.get_user(prin_id)
                if user is not None:
                    result.append(user)
    return result
