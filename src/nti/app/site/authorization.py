#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import contextlib

from zope import component
from zope import interface

from zope.security import checkPermission
from zope.security import management

from zope.security.interfaces import IParticipation

from zope.security.management import endInteraction
from zope.security.management import newInteraction
from zope.security.management import queryInteraction

from nti.dataserver.authorization import ACT_MANAGE_SITE
from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.interfaces import IPrincipal
from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IGroupMember

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IParticipation)
class _Participation(object):

    __slots__ = ('interaction', 'principal')

    def __init__(self, principal):
        self.interaction = None
        self.principal = principal


@contextlib.contextmanager
def _zope_interaction(username):
    interaction = queryInteraction()
    endInteraction()
    newInteraction(_Participation(IPrincipal(username)))
    try:
        yield
    finally:
        endInteraction()
        if interaction is not None:
            management.thread_local.interaction = interaction


@component.adapter(IUser)
@interface.implementer(IGroupMember)
class NextthoughtDotComSiteAdmin(object):

    def __init__(self, context):
        username = getattr(context, 'username', context)

        # When used during authentication, we won't have an interaction
        # and will need to create one
        with _zope_interaction(username):
            if checkPermission(ACT_MANAGE_SITE.id, context):
                self.groups = (ROLE_SITE_ADMIN,)
            else:
                self.groups = ()
