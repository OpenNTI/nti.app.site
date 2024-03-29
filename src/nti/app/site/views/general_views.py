#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import time
import string

from anytree.exporter import JsonExporter

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from requests.structures import CaseInsensitiveDict

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.annotation.interfaces import IAnnotations

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import site as curre_site

from zope.interface.interfaces import IComponents

from zope.traversing.interfaces import IEtcNamespace

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site import SITE_MIMETYPE
from nti.app.site import SITE_PROVIDER

from nti.app.site import MessageFactory as _

from nti.app.site.hostpolicy import is_valid_site_name
from nti.app.site.hostpolicy import create_site as create_site_folder

from nti.app.site.interfaces import NTI
from nti.app.site.interfaces import ISite

from nti.app.site.views import SitesPathAdapter

from nti.base._compat import text_

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.interfaces import ISiteHierarchy

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.ntiids.ntiids import escape_provider

from nti.site.hostpolicy import get_host_site
from nti.site.hostpolicy import get_all_host_sites

from nti.site.interfaces import IHostPolicyFolder

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
MIMETYPE = StandardExternalFields.MIMETYPE
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


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


@view_config(name='component_registry',
             route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=SitesPathAdapter,
             permission=ACT_READ)
class GetSiteRegistry(AbstractAuthenticatedView):

    @Lazy
    def params(self):
        return CaseInsensitiveDict(self.request.params)

    def __call__(self):
        # pylint: disable=no-member
        site_name = self.params.get('name') \
                 or self.params.get('site') \
                 or self.params.get('site_name')
        # pylint: disable=unsubscriptable-object
        site = self.context[site_name]
        ld = LocatedExternalDict({'PersistentManager': site.getSiteManager(),
                                  'RuntimeManager': component.getUtility(IComponents, name=site_name)})
        return ld


@view_config(name='site_hierarchy')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='GET',
               context=SitesPathAdapter,
               permission=ACT_READ)
class GetSiteHierarchyView(AbstractAuthenticatedView):

    def __call__(self):
        site_hierarchy = component.getUtility(ISiteHierarchy)
        # Make an externalizer for this tree?
        # Default is set so host policies can get dumped
        exporter = JsonExporter(indent=4, sort_keys=True, default=lambda x: x)
        return exporter.export(site_hierarchy.tree)


@view_config(name="view_hierarchy")
@view_defaults(route_name='objects.generic.traversal',
               renderer='../templates/site_hierarchy_view.pt',
               request_method='GET',
               context=SitesPathAdapter,
               permission=ACT_READ)
class SiteHierarchyView(AbstractAuthenticatedView):

    def __call__(self):
        return {}


@view_config(context=SitesPathAdapter)
@view_config(context=IHostPolicyFolder)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               name="create",
               permission=ACT_READ)
class CreateSiteView(AbstractAuthenticatedView,
                     ModeledContentUploadRequestUtilsMixin):

    content_predicate = ISite

    def readInput(self, value=None):
        values = super(CreateSiteView, self).readInput(value)
        if MIMETYPE not in values:
            values[MIMETYPE] = SITE_MIMETYPE
        for key, m in (('name', string.lower), ('provider', string.upper)):
            if values.get(key, None):
                value = values.pop(key, None)
                values[key.title()] = m(value)
        return values

    def __call__(self):
        site = self.readCreateUpdateContentObject(self.remoteUser)
        if not site.Name:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Must specified a site name."),
                             },
                             None)
        if site.Name.endswith('.'):
            site.Name = site.Name[:-1]
        if not is_valid_site_name(site.Name):
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Invalid site name."),
                                 'field': 'name'
                             },
                             None)
        folder = get_host_site(site.Name, safe=True)
        if folder is not None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Site already exists."),
                                 'code': 'SiteAlreadyExists',
                             },
                             None)
        provider = site.Provider
        if IHostPolicyFolder.providedBy(self.context):
            parent = get_host_site(self.context.__name__)
        else:
            provider = provider or NTI
            hostsites = component.getUtility(IEtcNamespace, name='hostsites')
            parent = hostsites.__parent__  # by definiton
        # set proper site
        with curre_site(parent):
            folder = create_site_folder(site.Name)
        if provider:
            annotations = IAnnotations(folder)
            annotations[SITE_PROVIDER] = escape_provider(text_(provider))
        # mark site
        interface.alsoProvides(folder, ICreated)
        interface.alsoProvides(folder, ILastModified)
        # pylint: disable=no-member
        folder.creator = self.remoteUser.username
        folder.lastModified = folder.createdTime = time.time()
        lifecycleevent.created(folder)
        return ISite(folder)
