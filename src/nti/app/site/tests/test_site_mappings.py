#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import contains_string

import os
import shutil

from quopri import decodestring

from zope import component

from zope.component.hooks import site
from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from zope.traversing.interfaces import IEtcNamespace

from nti.app.site import DELETED_MARKER
from nti.app.site import VIEW_SITE_BRAND
from nti.app.site import VIEW_SITE_MAPPINGS

from nti.appserver.brand.interfaces import ISiteBrand
from nti.appserver.brand.interfaces import ISiteAssetsFileSystemLocation

from nti.app.site.tests import SiteLayerTest

from nti.app.site.views.brand_views import SiteBrandUpdateView

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.app.testing.testing import ITestMailDelivery

from nti.app.testing.webtest import TestApp

from nti.dataserver.authorization import ROLE_SITE_ADMIN_NAME

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.communities import Community

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.externalization.representation import to_json_representation

from nti.site.hostpolicy import synchronize_host_policies

logger = __import__('logging').getLogger(__name__)

# From master_email.pt
DEFAULT_COLOR = u'#89be3c'

DEFAULT_LOGO_URL = u'https://d2ixlfeu83tci.cloudfront.net/images/email_logo.png'


class TestSiteMappings(SiteLayerTest):

    default_origin = 'https://test_brand_site'

    def _get_workspace(self, name, environ, exists=True):
        service_res = self.testapp.get('/dataserver2',
                                       extra_environ=environ)
        service_res = service_res.json_body
        workspaces = service_res['Items']
        result = None
        try:
            result = next(x for x in workspaces if x['Title'] == name)
        except StopIteration:
            pass
        to_check = not_none if exists else none
        assert_that(result, to_check())
        return result

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_site_mappings(self):
        """
        Validate site mappings.
        """
        with mock_dataserver.mock_db_trans():
            synchronize_host_policies()

        # Make a site admin user
        with mock_dataserver.mock_db_trans(self.ds, site_name='test_brand_site'):
            self._create_user(u'sitemapping_siteadmin', u'temp001',
                              external_value={'realname': u'Site Admin',
                                              'email': u'siteadmin@test.com'})
            self._create_user(u'sitemapping_regularuser', u'temp001',
                              external_value={'realname': u'Site Admin',
                                              'email': u'siteadmin@test.com'})
            new_site = getSite()
            prm = IPrincipalRoleManager(new_site)
            prm.assignRoleToPrincipal(ROLE_SITE_ADMIN_NAME, u'sitemapping_siteadmin')

        # Update rel
        site_admin_env = self._make_extra_environ('sitemapping_siteadmin')
        regular_env = self._make_extra_environ('sitemapping_regularuser')
        site_admin_ws = self._get_workspace('SiteAdmin', site_admin_env)
        mappings_rel = self.require_link_href_with_rel(site_admin_ws,
                                                       VIEW_SITE_MAPPINGS)

        mappings_res = self.testapp.get(mappings_rel,
                                        extra_environ=site_admin_env)
        mappings_res = mappings_res.json_body
        assert_that(mappings_res, has_entries('Class', 'SiteMappingContainer',
                                              'href', not_none(),
                                              'NTIID', not_none()))

        # Insert
        data = {'source_site_name': 'source_site_42'}
        self.testapp.post_json(mappings_rel, data,
                               extra_environ=regular_env,
                               status=403)

        res = self.testapp.post_json(mappings_rel, data,
                                     extra_environ=site_admin_env)
        res = res.json_body
        from IPython.terminal.debugger import set_trace;set_trace()

        # Update
        res = self.testapp.put_json(brand_rel,
                                    data,
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_entries(**theme)))

        # Upload assets (have to handle this correctly since multipart)
        data['full_logo'] = EXT_URL
        upload_files=[('logo', logo_filename, PNG_DATAURL)]
        form_data = {'__json__': to_json_representation(data)}
        res = self.testapp.put(brand_rel,
                               form_data,
                               upload_files=upload_files,
                               extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', not_none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_entries(**theme)))
        assets = brand_res.get('assets')
        assert_that(assets, has_entries('CreatedTime', not_none(),
                                        'Last Modified', not_none(),
                                        'full_logo', has_entries('filename', none()),
                                        'logo', has_entries('href', is_('/site_assets_location/test_brand_site/logo.png'),
                                                            'filename', logo_filename),
                                        'icon', none(),
                                        'favicon', none(),
                                        'email', none()))

        logo_url = assets.get('logo').get('href')
        full_logo_url = 'http://localhost%s' % logo_url
        self._test_create_user('test_site_brand_email', full_logo_url, color)

        # Theme updates
        data['theme'] = new_theme = {'d': 'd vals'}
        res = self.testapp.put_json(brand_rel, data,
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', not_none(),
                                           'brand_name', new_brand_name,
                                           'theme', has_entries(**new_theme)))

        data['theme'] = None
        res = self.testapp.put_json(brand_rel, data,
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', not_none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_length(0)))

        # Unauth get
        unauth_testapp = TestApp(self.app)
        res = unauth_testapp.get(brand_rel,
                                 extra_environ={'HTTP_ORIGIN': self.default_origin})
        brand_res = res.json_body
        self.forbid_link_with_rel(brand_res, 'delete')
        assert_that(brand_res, has_entries('assets', not_none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_length(0)))

        assets = brand_res.get('assets')
        assert_that(assets, has_entries('CreatedTime', not_none(),
                                        'Last Modified', not_none(),
                                        'full_logo', has_entries('filename', none()),
                                        'logo', has_entries('href', is_('/site_assets_location/test_brand_site/logo.png'),
                                                            'filename', logo_filename),
                                        'icon', none(),
                                        'favicon', none(),
                                        'email', none()))

        # Null out image
        res = self.testapp.put_json(brand_rel, {'full_logo': None},
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assets = brand_res.get('assets')
        assert_that(assets, has_entries('CreatedTime', not_none(),
                                        'Last Modified', not_none(),
                                        'full_logo', none(),
                                        'logo', has_entries('href', is_('/site_assets_location/test_brand_site/logo.png'),
                                                            'filename', logo_filename),
                                        'icon', none(),
                                        'favicon', none(),
                                        'email', none()))


        with mock_dataserver.mock_db_trans(self.ds, site_name='test_brand_site'):
            site_brand = component.getUtility(ISiteBrand)
            assert_that(site_brand, not_none())
            assets = site_brand.assets
            assert_that(assets, not_none())
            assert_that(assets.root.key, not_none())

        asset_path = '/tmp/test_site_assets_location/test_brand_site'
        assert_that(os.path.exists(asset_path),
                    is_(True))
        delete_marker_path = os.path.join(asset_path, DELETED_MARKER)
        assert_that(os.path.exists(delete_marker_path), is_(False))

        # Delete assets; validate deleted marker
        res = self.testapp.put_json(brand_rel,
                                    {'assets': None},
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_length(0)))

        assert_that(os.path.exists(asset_path), is_(True))
        delete_marker_path = os.path.join(asset_path, DELETED_MARKER)
        assert_that(os.path.exists(delete_marker_path), is_(True))


        # Validate restore
        res = self.testapp.put(brand_rel,
                               form_data,
                               upload_files=upload_files,
                               extra_environ=site_admin_env)
        brand_res = res.json_body
        assets = brand_res.get('assets')
        assert_that(assets, has_entries('CreatedTime', not_none(),
                                        'Last Modified', not_none(),
                                        'full_logo', has_entries('href', EXT_URL,
                                                                 'filename', none()),
                                        'logo', has_entries('href', is_('/site_assets_location/test_brand_site/logo.png'),
                                                            'filename', logo_filename),
                                        'icon', none(),
                                        'favicon', none(),
                                        'email', none()))

        # No longer a deleted marker
        assert_that(os.path.exists(asset_path), is_(True))
        delete_marker_path = os.path.join(asset_path, DELETED_MARKER)
        assert_that(os.path.exists(delete_marker_path), is_(False))

        # Valid favicon
        bad_upload_files=[('favicon', 'bad_favicon.jpeg', PNG_DATAURL)]
        res = self.testapp.put(brand_rel,
                               form_data,
                               upload_files=bad_upload_files,
                               extra_environ=site_admin_env,
                               status=422)
        res = res.json_body
        assert_that(res, has_entries('code', 'InvalidFaviconTypeError',
                                     'message', 'favicon must be a ico, gif, or png type.'))


        # Bad favicon size
        good_upload_files=[('favicon', 'good_favicon.png', PNG_DATAURL)]
        res = self.testapp.put(brand_rel,
                               form_data,
                               upload_files=good_upload_files,
                               extra_environ=site_admin_env,
                               status=422)
        res = res.json_body
        assert_that(res, has_entries('code', 'InvalidFaviconSizeError',
                                     'message', 'favicon must be 16x16 or 32x32.'))

        # Test file size constraint
        SiteBrandUpdateView.MAX_FILE_SIZE = 0
        res = self.testapp.put(brand_rel,
                               form_data,
                               upload_files=upload_files,
                               extra_environ=site_admin_env,
                               status=422)
        res = res.json_body
        assert_that(res, has_entries('code', 'ImageSizeExceededError',
                                     'message', 'logo image is too large.'))


        # Delete will reset everything
        self.testapp.delete(brand_href, extra_environ=site_admin_env)

        res = self.testapp.get(brand_rel, extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', is_('NextThought'),
                                           'brand_color', none(),
                                           'theme', has_length(0)))

        site_href = u'/dataserver2/++etc++hostsites/test_brand_site/++etc++site/SiteBrand'
        res = self.testapp.get(site_href, extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', 'NextThought',
                                           'brand_color', none(),
                                           'theme', has_length(0)))

        assert_that(os.path.exists(asset_path), is_(True))
        delete_marker_path = os.path.join(asset_path, DELETED_MARKER)
        assert_that(os.path.exists(delete_marker_path), is_(True))
