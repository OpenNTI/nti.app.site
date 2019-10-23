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

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.internalization import read_body_as_external_object

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site import MessageFactory as _

from nti.app.site.interfaces import ISiteBrand

from nti.app.site.model import SiteSeatLimit

from nti.appserver.ugd_edit_views import UGDPutView

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization import is_admin
from nti.dataserver.authorization import is_admin_or_site_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization import update_from_external_object

from nti.site import unregisterUtility

from nti.site.localutility import install_utility


logger = __import__('logging').getLogger(__name__)


@view_config(context=IDataserverFolder,
             name='SiteBrand')
@view_config(context=ISiteBrand)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest')
class SeatBrandView(AbstractView):
    """
    An unauthenticated view to fetch the site brand info.
    """

    def __call__(self):
        result = self.context
        if IDataserverFolder.providedBy(self.context):
            result = component.queryUtility(ISiteBrand)
        if result is None:
            raise hexc.HTTPNotFound()
        return result


@view_config(context=IDataserverFolder,
             name='SiteBrand')
@view_config(context=ISiteBrand)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               permission=nauth.ACT_CONTENT_EDIT,
               request_method='PUT')
class SeatBrandUpdateView(UGDPutView,
                          ModeledContentUploadRequestUtilsMixin):
    """
    These should be auto-created for new sites; we only need
    to update these once created.
    """

    def _get_object_to_update(self):
        result = self.context
        if IDataserverFolder.providedBy(self.context):
            result = component.queryUtility(ISiteBrand)
        if result is None:
            raise hexc.HTTPNotFound()
        return result

    def __call__(self):
        result = super(SeatBrandUpdateView, self).__call__()
        # TODO assets etc
        return result
