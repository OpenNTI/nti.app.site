#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.location.interfaces import IContained

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.interfaces import ISiteCommunity

from nti.schema.field import TextLine

#: Default provider
NTI = u'NTI'

# BWC
ISiteCommunity = ISiteCommunity

class ISite(IContained, ILastModified, ICreated):
    """
    Defines a site
    """
    Name = TextLine(title=u"Site uri", required=False)

    Provider = TextLine(title=u"Site provider",
                        required=False,
                        default=NTI)
