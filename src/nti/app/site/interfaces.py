#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.configuration.fields import Path

from zope.interface import Attribute

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.location.interfaces import IContained

from zope.schema import Bool

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.contentlibrary.interfaces import IDelimitedHierarchyBucket
from nti.contentlibrary.interfaces import IWritableDelimitedHierarchyKey

from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.dataserver.interfaces import ISiteCommunity

from nti.schema.field import Int
from nti.schema.field import Dict
from nti.schema.field import Object
from nti.schema.field import ValidURI
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
    Stores a source image.
    """

    source = ValidURI(title=u"source image",
                      required=False)

    filename = TextLine(title=u"the uploaded filename",
                        required=False)

    key = Object(IWritableDelimitedHierarchyKey,
                 title=u"asset source location",
                 description=u"Key that identifies where the asset source location is",
                 required=False,
                 default=None)
    key.setTaggedValue('_ext_excluded_out', True)


class ISiteBrandAssets(ILastModified, ICreated):
    """
    Defines the site brand assets
    """

    logo = Object(ISiteBrandImage,
                  title=u'The root site brand image',
                  required=False)

    icon = Object(ISiteBrandImage,
                  title=u'The site brand icon image',
                  required=False)

    full_logo = Object(ISiteBrandImage,
                       title=u'The site brand full_logo image',
                       required=False)

    email = Object(ISiteBrandImage,
                   title=u'The site brand web library image',
                   required=False)

    favicon = Object(ISiteBrandImage,
                     title=u'The site brand favicon image',
                     required=False)

    # <>/site-assets/<site>
    root = Object(IDelimitedHierarchyBucket,
                  title=u"asset location",
                  description=u"Bucket that identifies where the root location where assets are stored",
                  required=False,
                  default=None)
    root.setTaggedValue('_ext_excluded_out', True)


class ISiteBrand(IContained, ILastModified, ICreated, IShouldHaveTraversablePath):
    """
    A persistent that utility that defines site branding.
    """

    brand_name = TextLine(title=u"Site brand name",
                          required=False)

    brand_color = TextLine(title=u"The site color",
                           required=False)

    assets = Object(ISiteBrandAssets,
                    title=u'The site brand assets',
                    required=False)

    theme = Dict(title=u"Arbitrary key/val dict of theme",
                 readonly=False,
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



class ISiteAssetsFileSystemLocation(interface.Interface):
    """
    Register a non-persistent site assets library location.
    """

    directory = Path(title=u"Path to a directory containing site assets by site.",
                     required=True)
