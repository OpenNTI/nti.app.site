#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from pyramid import httpexceptions as hexc

from pyramid.view import IRequest
from pyramid.view import view_config

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site import MessageFactory as _

from nti.app.site.interfaces import ISiteMappingContainer

from nti.app.site.model import SiteMappingContainer

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization import is_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.site.interfaces import ISiteMapping
from nti.site.interfaces import IHostPolicySiteManager

from nti.site.localutility import install_utility

from nti.site.utils import registerUtility

ITEMS = StandardExternalFields.ITEMS
MIMETYPE = StandardExternalFields.MIMETYPE
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
@component.adapter(IHostPolicySiteManager, IRequest)
def SiteMappingContainerPathAdapter(unused_context, unused_request):
    result = component.queryUtility(ISiteMappingContainer)
    if result is None:
        # In either case, spoof an empty one if none.
        result = SiteMappingContainer()
        install_utility(result,
                        'SiteMappings',
                        ISiteMappingContainer,
                        component.getSiteManager())
    return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             request_method='GET',
             permission=nauth.ACT_NTI_ADMIN,
             name='AllSiteMappings')
class AllSiteMappingsView(AbstractAuthenticatedView):
    """
    An endpoint to return all site mappings.
    """

    def __call__(self):
        # XXX: Just persistent, or all types?
        result = LocatedExternalDict()
        items = component.queryUtility(ISiteMapping)
        result[ITEMS] = items
        result[ITEM_COUNT] = len(items)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ISiteMappingContainer,
             request_method='GET',
             permission=nauth.ACT_NTI_ADMIN)
class CurrentSiteMappingsView(AbstractAuthenticatedView):
    """
    Return all mappings pointing to the current site.
    """

    def __call__(self):
        return self.context


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ISiteMappingContainer,
             request_method='POST',
             permission=nauth.ACT_NTI_ADMIN)
class SiteMappingsInsertView(AbstractAuthenticatedView,
                             ModeledContentUploadRequestUtilsMixin):
    """
    Return all mappings pointing to the current site.
    """

    DEFAULT_FACTORY_MIMETYPE = 'application/vnd.nextthought.persistentsitemapping'

    def _transformInput(self, externalValue):
        if MIMETYPE not in externalValue:
            externalValue[MIMETYPE] = self.DEFAULT_FACTORY_MIMETYPE
        if 'target_site_name' not in externalValue:
            # XXX: Should we force this?
            externalValue['target_site_name'] = getSite().__name__
        elif externalValue['target_site_name'] != getSite().__name__:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Target site must be current site."),
                                 'code': 'InvalidTargetSiteError',
                             },
                             None)
        return externalValue

    def _do_call(self):
        if not is_admin(self.remoteUser):
            raise hexc.HTTPForbidden()
        new_mapping = self.readCreateUpdateContentObject(self.remoteUser)
        # We may get an already-created site mapping, makes this a no-op.
        result = self.context.add_site_mapping(new_mapping)
        if result is new_mapping:
            logger.info('Creating site mapping (%s) (user=%s)',
                    new_mapping, self.remoteUser)
            registerUtility(component.getSiteManager(), result, provided=ISiteMapping)
        return result
