#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from pyramid.view import IRequest
from pyramid.view import view_config

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site.interfaces import ISiteMappingContainer

from nti.app.site.model import SiteMappingContainer
from nti.app.site.model import PersistentSiteMapping

from nti.dataserver import authorization as nauth

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
             permission=nauth.ACT_CONTENT_EDIT)
class CurrentSiteMappingsView(AbstractAuthenticatedView):
    """
    Return all mappings pointing to the current site.
    """

    def __call__(self):
        return self.context
#         result = LocatedExternalDict()
#         site_name = getSite().__name__
#         items = component.getAllUtilitiesRegisteredFor(ISiteMapping)
#         items = [x for x in items if x.target_site_name == site_name]
#         result[ITEMS] = items
#         result[ITEM_COUNT] = len(items)
#         return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ISiteMappingContainer,
             request_method='POST',
             permission=nauth.ACT_CONTENT_EDIT)
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
            externalValue['target_site_name'] = getSite().__name__
        return externalValue

    def _do_call(self):
        # Need to register utility
        from IPython.terminal.debugger import set_trace;set_trace()
        new_mapping = self.readCreateUpdateContentObject(self.remoteUser)
        logger.info('Creating site mapping (%s) (user=%s)',
                    new_mapping, self.remoteUser)
        return new_mapping
