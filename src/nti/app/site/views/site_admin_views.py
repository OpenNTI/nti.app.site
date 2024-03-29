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
from nti.app.site.interfaces import IPersistentSiteMapping

from nti.app.site.utils import create_site_mapping_container

from nti.appserver.ugd_edit_views import UGDDeleteView

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization import is_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.site.interfaces import ISiteMapping
from nti.site.interfaces import IHostPolicySiteManager

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
        result = create_site_mapping_container()
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
        result = LocatedExternalDict()
        items = component.getAllUtilitiesRegisteredFor(ISiteMapping)
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
    View to insert a new site mapping, pointing to the current site.

    The newly created ISiteMapping must be registered globally to be
    accessible in `get_site_for_site_names`, which is used in the site
    tween.
    """

    DEFAULT_FACTORY_MIMETYPE = 'application/vnd.nextthought.persistentsitemapping'

    def _transformInput(self, externalValue):
        if MIMETYPE not in externalValue:
            externalValue[MIMETYPE] = self.DEFAULT_FACTORY_MIMETYPE
        if 'target_site_name' not in externalValue:
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
        return result


@view_config(route_name="objects.generic.traversal",
             context=IPersistentSiteMapping,
             renderer='rest',
             permission=nauth.ACT_NTI_ADMIN,
             request_method='DELETE')
class SiteMappingDeleteView(UGDDeleteView):

    def _do_delete_object(self, theObject):
        del theObject.__parent__[theObject.__name__]
        return theObject
