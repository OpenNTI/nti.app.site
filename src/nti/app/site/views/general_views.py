#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from requests.structures import CaseInsensitiveDict

from zope import component

from zope.component.hooks import site as curre_site

from zope.traversing.interfaces import IEtcNamespace

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site.hostpolicy import create_site

from nti.app.site import MessageFactory as _

from nti.app.site.views import SitesPathAdapter

from nti.dataserver.authorization import ACT_READ

from nti.externalization.externalization import StandardExternalFields

from nti.externalization.interfaces import LocatedExternalDict

from nti.site.hostpolicy import get_host_site
from nti.site.hostpolicy import get_all_host_sites

from nti.site.interfaces import IHostPolicyFolder

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


@view_config(name="all")
@view_config(name="sites")
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='GET',
               context=SitesPathAdapter,
               permission=ACT_READ)
class AllSitesView(AbstractAuthenticatedView):

    def __call__(self):
        result = LocatedExternalDict()
        result[ITEMS] = items = list(get_all_host_sites())
        result[TOTAL] = result[ITEM_COUNT] = len(items)
        return result


@view_config(context=SitesPathAdapter)
@view_config(context=IHostPolicyFolder)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               name="create",
               permission=ACT_READ)
class CreateSiteView(AbstractAuthenticatedView,
                     ModeledContentUploadRequestUtilsMixin):

    def readInput(self, value=None):
        values = super(CreateSiteView, self).readInput(value)
        return CaseInsensitiveDict(values)

    def __call__(self):
        data = self.readInput()
        name = data.get('name')
        if not name:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Invalid site name."),
                                 'code': 'InvalidSiteName',
                             },
                             None)
        site = get_host_site(name, safe=True)
        if site is not None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Site already exists."),
                                 'code': 'SiteAlreadyExists',
                             },
                             None)
        if IHostPolicyFolder.providedBy(self.context):
            parent = get_host_site(self.context.__name__)
        else:
            hostsites = component.getUtility(IEtcNamespace, name='hostsites')
            parent = hostsites.__parent__  # by definiton
        # set proper site
        with curre_site(parent):
            site = create_site(name)
        return site
