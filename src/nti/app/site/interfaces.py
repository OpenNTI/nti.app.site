#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.interface import Attribute

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.location.interfaces import IContained

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.interfaces import ISiteCommunity

from nti.schema.field import DecodingValidTextLine as TextLine

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
                        required=False)


class ISiteAdminAddedEvent(IObjectEvent):
    """
    Fired after a site admin has been added
    """
    request = Attribute(u"Request")


@interface.implementer(ISiteAdminAddedEvent)
class SiteAdminAddedEvent(ObjectEvent):

    def __init__(self, obj, request=None):
        super(SiteAdminAddedEvent, self).__init__(obj)
        self.request = request


class ISiteAdminRemovedEvent(IObjectEvent):
    """
    Fired after a site admin has been removed
    """
    request = Attribute(u"Request")


@interface.implementer(ISiteAdminRemovedEvent)
class SiteAdminRemovedEvent(ObjectEvent):

    def __init__(self, obj, request=None):
        super(SiteAdminRemovedEvent, self).__init__(obj)
        self.request = request
