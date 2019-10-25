#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from pyramid import httpexceptions as hexc

from pyramid.view import IRequest
from pyramid.view import view_config
from pyramid.view import view_defaults

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import get_all_sources
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.site.interfaces import ISiteBrand

from nti.app.site.model import SiteBrand

from nti.appserver.ugd_edit_views import UGDPutView

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.site.interfaces import IHostPolicySiteManager

from nti.site.localutility import install_utility

from nti.site.utils import unregisterUtility

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
@component.adapter(IHostPolicySiteManager, IRequest)
def SiteBrandPathAdapter(unused_context, unused_request):
    # Only get SiteBrand for our current site
    sm = component.getSiteManager()
    result = sm.get('SiteBrand')
    if result is None:
        brand_name = getSite().__name__
        result = SiteBrand(brand_name=brand_name)
        install_utility(result,
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


class SiteBrandImageMixin(object):
    """
    A mixin to manage images uploaded to the :class:`ISiteBrand`.
    """

    ASSET_MULTIPART_KEYS = ('catalog-source',
                            'catalog-background',
                            'catalog-promo-large',
                            'catalog-entry-cover',
                            'catalog-entry-thumbnail')

    @Lazy
    def _source_dict(self):
        """
        A dictionary of multipart inputs: name -> file.
        """
        return get_all_sources(self.request)

    def _make_asset_tmpdir(self, source_dict):
        """
        Make a tmp directory holding the presentation asset files to be moved
        to the appropriate destination.
        """
        if not source_dict:
            return
        if set(self.ASSET_MULTIPART_KEYS) - set(source_dict):
            # Do not have all of our multipart keys
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Missing presentation asset files."),
                                 'code': 'InvalidPresenationAssetFiles',
                             },
                             None)
        catalog_source = source_dict.get('catalog-source')
        catalog_promo = source_dict.get('catalog-promo-large')
        catalog_cover = source_dict.get('catalog-entry-cover')
        catalog_background = source_dict.get('catalog-background')
        catalog_thumbnail = source_dict.get('catalog-entry-thumbnail')
        return make_presentation_asset_dir(catalog_source,
                                           catalog_background,
                                           catalog_promo,
                                           catalog_cover,
                                           catalog_thumbnail)

    def get_source(self, request=None):
        """
        Return the validated presentation asset source.
        """
        request = self.request if not request else request
        # pylint: disable=no-member
        source_files = self._source_dict.values()
        for source_file in source_files or ():
            source_file.seek(0)
        # Otherwise, we have asset files we need to process
        return self._make_asset_tmpdir(self._source_dict)


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


@view_config(context=ISiteBrand)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               permission=nauth.ACT_CONTENT_EDIT,
               request_method='DELETE')
class SeatBrandDeleteView(AbstractAuthenticatedView):
    """
    Delete the site brand object.
    """

    def __call__(self):
        site_manager = self.context.__parent__
        unregisterUtility(site_manager, self.context, provided=ISiteBrand)
        del site_manager[self.context.__name__]
        return hexc.HTTPNoContent()

