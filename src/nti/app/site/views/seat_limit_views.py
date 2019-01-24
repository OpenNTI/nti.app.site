#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from ZODB.interfaces import IConnection

from pyramid.view import view_config
from pyramid.view import view_defaults

from zope import component

from zope.component.hooks import getSite

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object

from nti.app.site.interfaces import ISiteSeatLimit

from nti.app.site.model import SiteSeatLimit

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization import update_from_external_object

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               context=IDataserverFolder,
               name='SeatLimit')
class SeatLimitView(AbstractAuthenticatedView):

    @view_config(request_method='GET')
    def get_seat_limit(self):
        seat_limit = component.queryUtility(ISiteSeatLimit)
        return seat_limit

    @view_config(request_method=('POST', 'PUT'),
                 permission=nauth.ACT_READ)
    def create_or_update_seat_limit(self):
        site = getSite()
        seat_limit = component.queryUtility(ISiteSeatLimit, context=site)
        if seat_limit is None or seat_limit.__parent__ != site:
            # If we don't have one, create one
            seat_limit = SiteSeatLimit()
            seat_limit.__parent__ = site
            conn = IConnection(site)
            conn.add(seat_limit)
            sm = site.getSiteManager()
            sm.registerUtility(seat_limit, ISiteSeatLimit)

        ext_values = read_body_as_external_object(self.request)
        update_from_external_object(seat_limit, ext_values)
        return seat_limit
