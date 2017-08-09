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

from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IGroupMember


@component.adapter(IUser)
@interface.implementer(IGroupMember)
class NextthoughtDotComSiteAdmin(object):

    def __init__(self, context):
        if context.username.endswith('@nextthought.com'):
            self.groups = (ROLE_SITE_ADMIN,)
        else:
            self.groups = ()


def is_site_admin(user):
    """
    Returns whether the user has the `ROLE_ADMIN` role.
    """
    for _, adapter in component.getAdapters((user,), IGroupMember):
        if adapter.groups and ROLE_SITE_ADMIN in adapter.groups:
            return True
    return False
