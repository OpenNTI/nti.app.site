#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from persistent.interfaces import IPersistent

from zope import interface

from zope.container.constraints import contains

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from zope.interface import Attribute

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.schema import Bool
from zope.schema import ValidationError

from nti.appserver.brand.interfaces import ISiteBrand
from nti.appserver.brand.interfaces import ISiteBrandImage
from nti.appserver.brand.interfaces import ISiteBrandAssets

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.dataserver.interfaces import ISiteCommunity

from nti.schema.field import Int
from nti.schema.field import DecodingValidTextLine as TextLine

from nti.site.interfaces import ISiteMapping

#: Default provider
NTI = u'NTI'

# BWC
ISiteBrand = ISiteBrand
ISiteBrandImage = ISiteBrandImage
ISiteBrandAssets = ISiteBrandAssets
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


class IPersistentSiteMapping(ISiteMapping,
                             IPersistent,
                             ILastModified,
                             ICreated,
                             IShouldHaveTraversablePath):
    """
    A persistent :class:`ISiteMapping`.
    """


class ISiteMappingContainer(IContainer):
    """
    A storage container for :class:`ISiteMappings` objects. All site mappings
    in this container should have a target_site_name of the site this container
    is stored in.
    """
    contains(ISiteMapping)

    def get_site_mapping(source_site_name):
        """
        Lookup the :class:`ISiteMapping` by source_site_name.
        """

    def add_site_mapping(site_mapping):
        """
        Insert the :class:`ISiteMapping` by source_site_name.
        """


class DuplicateSiteMappingError(ValidationError):
    """
    Indicates a :class:`ISiteMapping` for a particular source_site_name is
    already in-use. The source_site_name must be unique per environment.
    """
