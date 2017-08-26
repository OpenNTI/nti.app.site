#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.location.interfaces import IContained

from nti.dataserver.interfaces import ICommunity

from nti.schema.field import TextLine

#: Default provider
NTI = u'NTI'


class ISite(IContained):
    """
    Defines a site
    """
    name = TextLine(title=u"Site uri", required=False)

    provider = TextLine(title=u"Site provider",
                        required=False,
                        default=NTI)


class ISiteCommunity(ICommunity):
    """
    Defines a site community
    """
