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


class SiteAdminSeatLimitExceededError(ValidationError):
    """
    Raised when the site admins seats have been exceeded.
    """


class ISiteSeatLimit(interface.Interface):
    """
    A limit upon the number of allowed users in a site.
    """

    hard_limit = Bool(title=u'Hard Seat Limit',
                         required=True,
                         default=False)

    max_seats = Int(title=u'Maximum Number of Seats',
                    required=False,
                    default=None)

    used_seats = Int(title=u'Used Seats',
                     description=u'The current number of seats taken in the site.',
                     required=True)

    hard_admin_limit = Bool(title=u'Hard admin limit',
                               description=u"Whether admins can be added once we have reached a limit",
                               required=True,
                               default=True)

    max_admin_seats = Int(title=u'Maximum number of admins',
                          required=False,
                          default=None)

    admin_used_seats = Int(title=u'Number of admins in use',
                           description=u'The current number of admin seats taken in the site.',
                           required=True)

    def can_add_admin():
        """
        Returns a bool indicating whether a new admin can be added. If not
        site admin seat limit is found, we default to True.
        """

    def validate_admin_seats():
        """
        Validates that the site admin seats have not been exceeded, raising
        a :class:`SiteAdminSeatLimitExceededError`.
        """

    def get_admin_seat_users():
        """
        Returns an iterable of admin users.
        """

    def get_admin_seat_usernames():
        """
        Returns an iterable of admin usernames.
        """


class ISiteAdminSeatUserLimitUtility(interface.Interface):
    """
    A utility that will provide a site admin seat limit.
    """

    def get_admin_seat_limit():
        """
        Returns an int admin seat limit, or None if not available.
        """


class ISiteAdminSeatUserProvider(interface.Interface):
    """
    A utility that iterates over the list of admins that count towards the
    site's admin user limit
    """

    def iter_users():
        """
        A generator of admin user objects.
        """


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
