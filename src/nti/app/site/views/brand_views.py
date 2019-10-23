#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from pyramid.view import IRequest
from pyramid.view import view_config
from pyramid.view import view_defaults

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractView

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site import MessageFactory as _

from nti.app.site.interfaces import ISiteBrand

from nti.app.site.model import SiteBrand

from nti.appserver.ugd_edit_views import UGDPutView

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.site.interfaces import IHostPolicySiteManager

from nti.site.localutility import install_utility


logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
def SiteBrandPathAdapter(unused_context, unused_request):
    result = component.queryUtility(ISiteBrand)
    if result is None:
        brand_name = getSite().__name__
        site_brand = SiteBrand(brand_name=brand_name)
        install_utility(site_brand,
                        'SiteBrand',
                        ISiteBrand,
                        component.getSiteManager())
    return result


@view_config(context=ISiteBrand)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest')
class SeatBrandView(AbstractView):
    """
    An unauthenticated view to fetch the site brand info.
    """

    def __call__(self):
        return self.context


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

    def __call__(self):
        result = super(SeatBrandUpdateView, self).__call__()
        # TODO assets etc
        return result
