#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.dataserver.interfaces import ISiteCommunity

from nti.dataserver.users.communities import Community

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ISiteCommunity)
class SiteCommunity(Community):
    __external_can_create__ = False
    __external_class_name__ = 'Community'
    mimeType = mime_type = 'application/vnd.nextthought.sitecommunity'
