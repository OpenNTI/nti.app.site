#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.interface import Attribute

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.location.interfaces import IContained

from zope.schema import Bool
from zope.schema import Choice

from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import ISource

from zope.schema.vocabulary import SimpleVocabulary

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.interfaces import ISiteCommunity

from nti.schema.field import Int
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


class ISiteSeatLimitAlgorithm(interface.Interface):
    """
    An adapter to an algorithm for determining used seats in a site
    """

    def used_seats(*args, **kwargs):
        """
        Returns an Int of the number of used seats in a site
        """


@interface.implementer(ISource, IContextSourceBinder)
class SeatAlgorithmContextSourceBinder(object):

    def __call__(self, seat_limit_obj):
        site = getSite()
        adapters = component.getAdapters((site, seat_limit_obj), ISiteSeatLimitAlgorithm, context=site.getSiteManager())
        names = [adapter[0] for adapter in adapters]
        return SimpleVocabulary.fromValues(names)


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

    seat_algorithm = Choice(source=SeatAlgorithmContextSourceBinder(),
                            default=u'')
