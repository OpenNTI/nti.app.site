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

from nti.dataserver.authorization import ROLE_PREFIX

from nti.dataserver.authorization import StringRole

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IGroupMember

#: Name of the super-user group that is expected to have full rights
#: on sites
ROLE_SITE_ADMIN_NAME = ROLE_PREFIX + 'nti.site.admin'
ROLE_SITE_ADMIN = StringRole(ROLE_SITE_ADMIN_NAME)


@component.adapter(IUser)
@interface.implementer(IGroupMember)
class NextthoughtDotComAdmin(object):

    def __init__(self, context):
        if context.username.endswith('@nextthought.com'):
            self.groups = (ROLE_SITE_ADMIN,)
        else:
            self.groups = ()
