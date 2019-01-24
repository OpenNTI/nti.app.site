#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from zope import component

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object

from nti.app.site.interfaces import ISiteSeatLimit

from nti.app.site.model import SiteSeatLimit

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization import is_admin
from nti.dataserver.authorization import is_admin_or_site_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization import update_from_external_object

from nti.site import unregisterUtility

from nti.site.localutility import install_utility


__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               context=IDataserverFolder,
               name='SeatLimit')
class SeatLimitView(AbstractAuthenticatedView):

    @Lazy
    def site(self):
        return getSite()

    @Lazy
    def site_manager(self):
        return self.site.getSiteManager()

    def _get_site_seat_limit(self):
        seat_limit = component.queryUtility(ISiteSeatLimit, context=self.site)
        if seat_limit is None or seat_limit.__parent__ != self.site_manager:
            return None
        return seat_limit

    @view_config(request_method='GET')
    def get_seat_limit(self):
        # Only allow nti and site admins
        if not is_admin_or_site_admin(self.remoteUser):
            return hexc.HTTPUnauthorized()
        seat_limit = component.queryUtility(ISiteSeatLimit)
        return seat_limit

    @view_config(request_method=('POST', 'PUT'),
                 permission=nauth.ACT_READ)
    def create_or_update_seat_limit(self):
        if not is_admin(self.remoteUser):
            return hexc.HTTPUnauthorized()
        seat_limit = self._get_site_seat_limit()
        if seat_limit is None:
            # If we don't have one, create one
            seat_limit = SiteSeatLimit()
            # We use install_utility to ensure
            # the object lineage is properly set
            install_utility(seat_limit,
                            utility_name=seat_limit.__name__,
                            provided=ISiteSeatLimit,
                            local_site_manager=self.site_manager)

        ext_values = read_body_as_external_object(self.request)
        update_from_external_object(seat_limit, ext_values)
        return seat_limit

    @view_config(request_method='DELETE',
                 permission=nauth.ACT_READ)
    def delete_seat_limit(self):
        if not is_admin(self.remoteUser):
            return hexc.HTTPUnauthorized()
        seat_limit = self._get_site_seat_limit()
        if seat_limit is None:
            return hexc.HTTPExpectationFailed(u'There is no seat limit defined in this site')
        # There is not an uninstall_utility helper, see uninstall_utility_on_unregistration
        # for unregistering information
        unregisterUtility(self.site_manager, seat_limit, provided=ISiteSeatLimit)
        del self.site_manager[seat_limit.__name__]
        return hexc.HTTPNoContent()
