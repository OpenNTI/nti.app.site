#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.site.interfaces import ISiteCommunity

from nti.dataserver.users.communities import Community


@interface.implementer(ISiteCommunity)
class SiteCommunity(Community):
    __external_can_create__ = False
    __external_class_name__ = 'Community'
    mimeType = mime_type = 'application/vnd.nextthought.sitecommunity'
