#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries

from zope import component

from zope.component.hooks import site
from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from zope.traversing.interfaces import IEtcNamespace

from nti.app.site import VIEW_SITE_BRAND

from nti.app.site.interfaces import ISiteBrand

from nti.app.site.tests import SiteLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.app.testing.webtest import TestApp

from nti.dataserver.authorization import ROLE_SITE_ADMIN_NAME

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.communities import Community

from nti.site.hostpolicy import synchronize_host_policies
from nti.externalization.representation import to_json_representation

logger = __import__('logging').getLogger(__name__)


class TestSiteBrand(SiteLayerTest):

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
    def test_site_brand(self):
        """
        Validate the site subscribers (create community and site brand).

        Validate updating the SiteBrand object and permissioning.
        """
        PNG_DATAURL = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACXBIWXMAAAsTAAALEwEAmpwYAAACbmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS4xLjIiPgogICA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogICAgICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgICAgICAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iPgogICAgICAgICA8eG1wOkNyZWF0b3JUb29sPkFjb3JuIHZlcnNpb24gMi42LjU8L3htcDpDcmVhdG9yVG9vbD4KICAgICAgPC9yZGY6RGVzY3JpcHRpb24+CiAgICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAgICAgIHhtbG5zOnRpZmY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIj4KICAgICAgICAgPHRpZmY6Q29tcHJlc3Npb24+NTwvdGlmZjpDb21wcmVzc2lvbj4KICAgICAgICAgPHRpZmY6WVJlc29sdXRpb24+NzI8L3RpZmY6WVJlc29sdXRpb24+CiAgICAgICAgIDx0aWZmOlhSZXNvbHV0aW9uPjcyPC90aWZmOlhSZXNvbHV0aW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KO/MupgAAAA1JREFUCB1j+P//PwMACPwC/uYM/6sAAAAASUVORK5CYII='
        EXT_URL = 'https://s3.amazonaws.com/content.nextthought.com/images/ifsta/reportassets/elibrary-image.jpg'

        with mock_dataserver.mock_db_trans():
            # Validate our brand exists due to subscriber
            synchronize_host_policies()
            sites = component.queryUtility(IEtcNamespace, name='hostsites')
            test_site = sites.get('test_brand_site')
            with site(test_site):
                # SiteBrand created
                site_brand = component.queryUtility(ISiteBrand)
                assert_that(site_brand, not_none())
                assert_that(site_brand.brand_name, is_('test_brand_site'))
                assert_that(site_brand.assets, none())

            # Validate subscriber community creation
            community = Community.get_community('test_brand_site')
            assert_that(community, not_none())

        # Make a site admin user
        with mock_dataserver.mock_db_trans(self.ds, site_name='test_brand_site'):
            self._create_user(u'sitebrand_siteadmin', u'temp001',
                              external_value={'realname': u'Site Admin',
                                              'email': u'siteadmin@test.com'})
            self._create_user(u'sitebrand_regularuser', u'temp001',
                              external_value={'realname': u'Site Admin',
                                              'email': u'siteadmin@test.com'})
            new_site = getSite()
            prm = IPrincipalRoleManager(new_site)
            prm.assignRoleToPrincipal(ROLE_SITE_ADMIN_NAME, u'sitebrand_siteadmin')

        # Update rel
        site_admin_env = self._make_extra_environ('sitebrand_siteadmin')
        regular_env = self._make_extra_environ('sitebrand_regularuser')
        site_admin_ws = self._get_workspace('SiteAdmin', site_admin_env)
        brand_rel = self.require_link_href_with_rel(site_admin_ws, VIEW_SITE_BRAND)

        brand_res = self.testapp.get(brand_rel, extra_environ=site_admin_env)
        brand_res = brand_res.json_body
        brand_href = brand_res.get('href')
        assert_that(brand_href, not_none())
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', 'test_brand_site'))
        self.require_link_href_with_rel(brand_res, 'edit')
        self.require_link_href_with_rel(brand_res, 'delete')

        # Get rels
        user_ws = self._get_workspace('sitebrand_siteadmin', site_admin_env)
        self.require_link_href_with_rel(user_ws, VIEW_SITE_BRAND)

        user_ws = self._get_workspace('sitebrand_regularuser', regular_env)
        get_brand_rel = self.require_link_href_with_rel(user_ws, VIEW_SITE_BRAND)
        brand_res = self.testapp.get(get_brand_rel, extra_environ=regular_env)
        brand_res = brand_res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', 'test_brand_site',
                                           'brand_color', none(),
                                           'theme', has_length(0)))
        self.forbid_link_with_rel(brand_res, 'edit')
        self.forbid_link_with_rel(brand_res, 'delete')

        # Update brand name and theme
        new_brand_name = 'new brand name'
        color = u'#404040'
        theme = {'a': 'aval',
                 'b': {'b1': 'b1val'},
                 'c': None}
        data = {'brand_name': new_brand_name,
                'theme': theme,
                'brand_color': color,
                'full_logo': EXT_URL}
        logo_filename = 'logo-filename.png'
        upload_files=[('logo', logo_filename, PNG_DATAURL)]
        self.testapp.put_json(brand_rel, data,
                              extra_environ=regular_env,
                              status=403)

        # Upload assets (have to handle this correctly since multipart)
        form_data = {'__json__': to_json_representation(data)}
        res = self.testapp.put(brand_rel,
                               form_data,
                               upload_files=upload_files,
                               extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_entries(**theme)))

        # Theme updates
        data['theme'] = new_theme = {'d': 'd vals'}
        res = self.testapp.put_json(brand_rel, data,
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', new_brand_name,
                                           'theme', has_entries(**new_theme)))

        data['theme'] = None
        res = self.testapp.put_json(brand_rel, data,
                                    extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_length(0)))

        # Unauth get
        unauth_testapp = TestApp(self.app)
        res = unauth_testapp.get(brand_rel,
                                 extra_environ={'HTTP_ORIGIN': self.default_origin})
        brand_res = res.json_body
        self.forbid_link_with_rel(brand_res, 'delete')
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', new_brand_name,
                                           'brand_color', color,
                                           'theme', has_length(0)))

        # Delete will reset everything
        self.testapp.delete(brand_href, extra_environ=site_admin_env)

        res = self.testapp.get(brand_rel, extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', 'test_brand_site',
                                           'brand_color', none(),
                                           'theme', has_length(0)))

        site_href = u'/dataserver2/++etc++hostsites/test_brand_site/++etc++site/SiteBrand'
        res = self.testapp.get(site_href, extra_environ=site_admin_env)
        brand_res = res.json_body
        assert_that(brand_res, has_entries('assets', none(),
                                           'brand_name', 'test_brand_site',
                                           'brand_color', none(),
                                           'theme', has_length(0)))
