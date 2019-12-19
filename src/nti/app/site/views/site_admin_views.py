#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from pyramid.view import view_config

from zope import component

from zope.component.hooks import getSite

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.site.interfaces import ISiteMapping

from nti.site.utils import registerUtility

ITEMS = StandardExternalFields.ITEMS
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


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
             context=ISiteMapping,
             request_method='GET',
             permission=nauth.ACT_CONTENT_EDIT,
             name='SiteMappings')
class CurrentSiteMappingsView(AbstractAuthenticatedView):
    """
    Return all mappings pointing to the current site.
    """

    def __call__(self):
        result = LocatedExternalDict()
        site_name = getSite().__name__
        items = component.getAllUtilitiesRegisteredFor(ISiteMapping)
        items = [x for x in items if x.target_site_name == site_name]
        result[ITEMS] = items
        result[ITEM_COUNT] = len(items)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             request_method='POST',
             permission=nauth.ACT_CONTENT_EDIT,
             name='SiteMappings')
class SiteMappingsInsertView(AbstractAuthenticatedView):
    """
    Return all mappings pointing to the current site.
    """

    def __call__(self):
        result = LocatedExternalDict()
        site_name = getSite().__name__
        items = component.getAllUtilitiesRegisteredFor(ISiteMapping)
        items = [x for x in items if x.target_site_name == site_name]
        result[ITEMS] = items
        result[ITEM_COUNT] = len(items)
        registerUtility(registry, obj, provided, name=name)
        return result
