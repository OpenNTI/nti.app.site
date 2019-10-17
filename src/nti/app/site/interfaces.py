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

from zope.schema import Bool

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.interfaces import ISiteCommunity

from nti.schema.field import Int
from nti.schema.field import Object
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


class ISiteBrandImage(ILastModified, ICreated):
    """
    Stores a source image, 2x, and 3x images.
    """

    source = TextLine(title=u"source image",
                      required=False)

    two_times = TextLine(title=u"two_times image",
                         required=False)

    three_times = TextLine(title=u"three_times image",
                           required=False)


class ISiteBrandAssets(ILastModified, ICreated):
    """
    Defines the site brand assets
    """

    mobile = Object(ISiteBrandImage,
                    title=u'The site brand mobile image',
                    required=False)

    background = Object(ISiteBrandImage,
                        title=u'The site brand background image',
                        required=False)

    web = Object(ISiteBrandImage,
                 title=u'The site brand web image',
                 required=False)

    web_library = Object(ISiteBrandImage,
                         title=u'The site brand web library image',
                         required=False)

    favicon = Object(ISiteBrandImage,
                     title=u'The site brand favicon image',
                     required=False)

    login = Object(ISiteBrandImage,
                   title=u'The site brand login image',
                   required=False)


class ISiteBrand(IContained, ILastModified, ICreated):
    """
    A persistent that utility that defines site branding.
    """

    brand_name = TextLine(title=u"Site brand name", required=False)

    assets = Object(ISiteBrandAssets,
                    title=u'The site brand assets',
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


class ISiteSeatLimit(interface.Interface):
    """
    A limit upon the number of allowed users in a site.
    """

    hard = Bool(title=u'Hard Seat Limit',
                required=True,
                default=False)

    max_seats = Int(title=u'Maximum Number of Seats',
                    required=False,
                    default=None)

    used_seats = Int(title=u'Used Seats',
                     description=u'The current number of seats taken in the site.',
                     required=True)
