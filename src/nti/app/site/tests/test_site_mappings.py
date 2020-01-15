#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_items
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

        # Must be NT admin
        data = {'source_site_name': 'source_site_42'}
        for env in (site_admin_env, regular_env):
            self.testapp.post_json(mappings_rel, data,
                                   extra_environ=env,
                                   status=403)

        # Insert
        res = self.testapp.post_json(mappings_rel, data)
        res = res.json_body
        assert_that(res, has_entries('Class', 'PersistentSiteMapping',
                                     'href', '/dataserver2/++etc++hostsites/test_brand_site/++etc++site/SiteMappings/source_site_42',
                                     'MimeType', 'application/vnd.nextthought.persistentsitemapping',
                                     'source_site_name', 'source_site_42',
                                     'target_site_name', 'test_brand_site',
                                     'Creator', 'sjohnson@nextthought.com',
                                     'NTIID', not_none()))
        first_ntiid = res['NTIID']
        mappings_res = self.testapp.get(mappings_rel)
        mappings_res = mappings_res.json_body
        assert_that(mappings_res, has_entries('Class', 'SiteMappingContainer',
                                              'CreatedTime', not_none(),
                                              'NTIID', not_none(),
                                              'Last Modified', not_none(),
                                              'Items', has_items('source_site_42'),
                                              'href', '/dataserver2/SiteMappings'))

        # Idempotent
        res = self.testapp.post_json(mappings_rel, data)
        res = res.json_body
        assert_that(res, has_entry('NTIID', first_ntiid))

