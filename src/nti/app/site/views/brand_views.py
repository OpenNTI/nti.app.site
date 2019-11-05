#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os

from pyramid import httpexceptions as hexc

from pyramid.view import IRequest
from pyramid.view import view_config
from pyramid.view import view_defaults

from requests.structures import CaseInsensitiveDict

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from zope.event import notify

from zope.lifecycleevent import ObjectRemovedEvent

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import get_all_sources
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.site import MessageFactory as _

from nti.app.site import DELETED_MARKER

from nti.app.site.interfaces import ISiteBrand, ISiteAssetsFileSystemLocation

from nti.app.site.model import SiteBrand
from nti.app.site.model import SiteBrandImage
from nti.app.site.model import SiteBrandAssets

from nti.appserver.ugd_edit_views import UGDPutView

from nti.contentlibrary.zodb import PersistentHierarchyKey
from nti.contentlibrary.zodb import PersistentHierarchyBucket

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.property.dataurl import DataURL

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
class SiteBrandView(AbstractView):
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
class SiteBrandUpdateView(UGDPutView):
    """
    This context should be auto-created for new sites; we only need
    to update it once created.
    """

    ASSET_MULTIPART_KEYS = ('logo',
                            'icon',
                            'full_logo',
                            'email',
                            'favicon')

    # 50 MB
    MAX_FILE_SIZE = 52428800

    def readInput(self, value=None, filter_asset=True):
        if self.request.body:
            values = super(SiteBrandUpdateView, self).readInput(value)
        else:
            values = self.request.params
        if filter_asset:
            values = {x:y for x, y in values.items() if x not in self.ASSET_MULTIPART_KEYS}
        result = CaseInsensitiveDict(values)
        return result

    def _check_image_constraint(self, attr_name, data):
        """
        Validate the image file constraints
        """
        if len(data) > self.MAX_FILE_SIZE:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"${field} image is too large.",
                                              mapping={'field': attr_name}),
                                 'code': 'ImageSizeExceededError',
                             },
                             None)

    @Lazy
    def _asset_url_dict(self):
        """
        A dictionary of asset urls.
        """
        vals = self.readInput(filter_asset=False)
        return CaseInsensitiveDict({x:y for x, y in vals.items() if x in self.ASSET_MULTIPART_KEYS})

    @Lazy
    def _source_dict(self):
        """
        A dictionary of multipart inputs: name -> file.
        """
        return get_all_sources(self.request)

    def _get_location_directory(self):
        location = component.queryUtility(ISiteAssetsFileSystemLocation)
        if location is None:
            logger.error('No ISiteAssetsFileSystemLocation registered')
            raise hexc.HTTPUnprocessableEntity()
        return location.directory

    def _create_assets(self, location_dir):
        """
        Create and initialize :class:`ISiteBrandAssets`.
        """
        site_name = getSite().__name__
        bucket_path = os.path.join(location_dir, site_name)
        if not os.path.exists(bucket_path):
            os.makedirs(bucket_path)
        bucket = PersistentHierarchyBucket(name=site_name)
        result = SiteBrandAssets(root=bucket)
        result.__parent__ = self.context
        self.context.assets = result

        # Check if these assets were previously marked as deleted; if so, undo.
        delete_path = os.path.join(bucket_path, DELETED_MARKER)
        if os.path.exists(delete_path):
            os.remove(delete_path)
        return result

    def _store_brand_image(self, assets, attr_name, brand_image):
        """
        Store the image object on our assets object.
        """
        brand_image.__parent__ = assets
        setattr(assets, attr_name, brand_image)

    def update_assets(self):
        """
        Update and store our assets, if necessary.
        """
        if self._asset_url_dict or self._source_dict:
            # Ok, we have something
            location_dir = self._get_location_directory()
            assets = self.context.assets
            if assets is None:
                assets = self._create_assets(location_dir)
            # Store our assets as urls
            for attr_name, asset_url in self._asset_url_dict.items():
                if not asset_url:
                    # Nulling out
                    setattr(assets, attr_name, None)
                else:
                    brand_image = SiteBrandImage(source=str(asset_url))
                    self._store_brand_image(assets, attr_name, brand_image)
            # Save to disk and store given images
            for attr_name, asset_file in self._source_dict.items():
                if attr_name not in self.ASSET_MULTIPART_KEYS:
                    continue
                key = PersistentHierarchyKey(name=unicode(attr_name),
                                             bucket=assets.root)
                path = os.path.join(location_dir, assets.root.name, attr_name)
                asset_file.seek(0)
                data_url = DataURL(asset_file.read())
                self._check_image_constraint(attr_name, data_url.data)
                with open(path, 'wb') as target:
                    target.write(data_url.data)
                brand_image = SiteBrandImage(source=path,
                                             filename=asset_file.name,
                                             key=key)
                self._store_brand_image(assets, attr_name, brand_image)

    def __call__(self):
        old_assets = self.context.assets
        super(SiteBrandUpdateView, self).__call__()
        # Now update assets
        self.update_assets()
        # Broadcast if nulled out
        if old_assets is not None and self.context.assets is None:
            notify(ObjectRemovedEvent(old_assets))
        return self.context


@view_config(context=ISiteBrand)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               permission=nauth.ACT_CONTENT_EDIT,
               request_method='DELETE')
class SiteBrandDeleteView(AbstractAuthenticatedView):
    """
    Delete the site brand object.
    """

    def __call__(self):
        site_manager = self.context.__parent__
        unregisterUtility(site_manager, self.context, provided=ISiteBrand)
        del site_manager[self.context.__name__]
        return hexc.HTTPNoContent()

