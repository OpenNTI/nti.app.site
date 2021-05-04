#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os

from PIL import Image

from pyramid import httpexceptions as hexc

from pyramid.view import IRequest
from pyramid.view import view_config
from pyramid.view import view_defaults

from requests.structures import CaseInsensitiveDict

from six import StringIO

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

from nti.appserver.brand.interfaces import ISiteBrand
from nti.appserver.brand.interfaces import ISiteAssetsFileSystemLocation

from nti.appserver.brand.model import SiteBrand
from nti.appserver.brand.model import SiteBrandImage
from nti.appserver.brand.model import SiteBrandAssets

from nti.appserver.ugd_edit_views import UGDPutView

from nti.contentlibrary.zodb import PersistentHierarchyKey
from nti.contentlibrary.zodb import PersistentHierarchyBucket

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.property.dataurl import DataURL

from nti.site.interfaces import IHostPolicySiteManager

from nti.site.localutility import install_utility
from nti.site.localutility import queryNextUtility

from nti.site.utils import unregisterUtility

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
@component.adapter(IHostPolicySiteManager, IRequest)
def SiteBrandPathAdapter(unused_context, request):
    if request.method == 'GET':
        # For READ, get whatever is in use
        result = component.queryUtility(ISiteBrand)
    else:
        # Otherwise, for WRITE/DELETE/etc,
        # only get SiteBrand for our current site.
        sm = component.getSiteManager()
        result = sm.get('SiteBrand')
    if result is None:
        # In either case, spoof an empty one if none.
        result = SiteBrand()
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


class SiteBrandUpdateBase(UGDPutView):
    """
    This context should be auto-created for new sites; we only need
    to update it once created.
    """

    ASSET_MULTIPART_KEYS = ('logo',
                            'icon',
                            'full_logo',
                            'email',
                            'favicon',
                            'login_logo',
                            'login_background',
                            'login_featured_callout',
                            'certificate_sidebar_image',
                            'certificate_logo')

    VALID_IMAGE_EXTS = ('.png','.jpg','.jpeg','.gif', '.svg')

    # 50 MB
    MAX_FILE_SIZE = 52428800

    def readInput(self, value=None, filter_asset=True):
        if self.request.body:
            values = super(SiteBrandUpdateBase, self).readInput(value)
        else:
            values = self.request.params
        if filter_asset:
            values = {x:y for x, y in values.items() if x not in self.ASSET_MULTIPART_KEYS}
        result = CaseInsensitiveDict(values)
        return result

    def _check_image_constraint(self, attr_name, data, ext):
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
        if attr_name == 'favicon':
            if ext and ext.lower() not in ('.ico', '.gif', '.png'):
                raise_json_error(self.request,
                                 hexc.HTTPUnprocessableEntity,
                                 {
                                     'message': _(u"favicon must be a ico, gif, or png type."),
                                     'code': 'InvalidFaviconTypeError',
                                 },
                                 None)
            data = StringIO(data)
            image = Image.open(data)
            if image.size not in ((16,16), (32,32)):
                raise_json_error(self.request,
                                 hexc.HTTPUnprocessableEntity,
                                 {
                                     'message': _(u"favicon must be 16x16 or 32x32."),
                                     'code': 'InvalidFaviconSizeError',
                                 },
                                 None)
        elif ext and ext.lower() not in self.VALID_IMAGE_EXTS:
            raise_json_error(self.request,
                                 hexc.HTTPUnprocessableEntity,
                                 {
                                     'message': _(u"Image must be a png, jpg, jpeg, gif, or svg type."),
                                     'code': 'InvalidFaviconTypeError',
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
        A dictionary of multipart inputs: name -> file. If we have a source_site_brand,
        we'll use those paths as sources for a (new) SiteBrand object.
        """
        result = get_all_sources(self.request)
        source = self._source_site_brand
        source_assets = getattr(source, 'assets', None)
        if source_assets is not None:
            for asset_key in self.ASSET_MULTIPART_KEYS:
                # Look for keys not in form upload
                if asset_key not in result:
                    source_image = getattr(source_assets, asset_key, None)
                    # Only use source if we have a path and it exists
                    # (we could also copy urls here, or in asset_url_dict).
                    if      source_image is not None \
                        and source_image.source \
                        and os.path.exists(source_image.source):
                            result[asset_key] = source_image.source
        return result

    @Lazy
    def _source_site_brand(self):
        """
        If we are a dynamic object, attempt to use a parent ISiteBrand as a
        basis for persisting the new child ISiteBrand.
        """
        if getattr(self.context, '_p_mtime', None) is None:
            return queryNextUtility(self.context, ISiteBrand)

    def _copy_source_data(self, attr_name, source_file, target_path, ext):
        """
        Copy the source file data to our target path.
        """
        try:
            with open(source_file, 'r') as f:
                data = f.read()
        except TypeError:
            # StringIO
            source_file.seek(0)
            data = source_file.read()

        if data.startswith('data:'):
            data_url = DataURL(data)
            data = data_url.data
        self._check_image_constraint(attr_name, data, ext)
        with open(target_path, 'wb') as target:
            target.write(data)

    def _copy_source_brand_attrs(self, source):
        """
        Copy the simple attributes from our source site brand.
        """
        self.context.brand_name = source.brand_name
        self.context.brand_color = source.brand_color
        if source.theme is not None:
            self.context.theme = dict(source.theme)


@view_config(context=ISiteBrand)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               permission=nauth.ACT_CONTENT_EDIT,
               request_method='PUT')
class SiteBrandUpdateView(SiteBrandUpdateBase):
    """
    This context should be auto-created for new sites; we only need
    to update it once created.
    """

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

                try:
                    # Multipart upload
                    original_filename = asset_file.name
                except AttributeError:
                    # Source path
                    original_filename = os.path.split(asset_file)[-1]
                ext = os.path.splitext(original_filename)[1]
                filename = u'%s%s' % (attr_name, ext)
                key = PersistentHierarchyKey(name=filename,
                                             bucket=assets.root)
                path = os.path.join(location_dir, assets.root.name, filename)
                self._copy_source_data(attr_name, asset_file, path, ext)
                brand_image = SiteBrandImage(source=path,
                                             filename=original_filename,
                                             key=key)
                self._store_brand_image(assets, attr_name, brand_image)

    def __call__(self):
        # Copy source attrs, import to do this before update
        if self._source_site_brand is not None:
            self._copy_source_brand_attrs(self._source_site_brand)
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

