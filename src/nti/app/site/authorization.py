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

from zope.security import checkPermission

from nti.dataserver.authorization import ACT_MANAGE_SITE
from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.authorization_utils import zope_interaction

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IGroupMember

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(IGroupMember)
class SiteAdminGroupsProvider(object):

    def __init__(self, context):
        username = getattr(context, 'username', context)

        # Ensure we have the proper user in the interaction, which
        # might be different than the authenticated user
        with zope_interaction(username):
            if checkPermission(ACT_MANAGE_SITE.id, context):
                self.groups = (ROLE_SITE_ADMIN,)
            else:
                self.groups = ()
