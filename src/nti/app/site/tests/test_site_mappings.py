#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_item
from hamcrest import has_entry
from hamcrest import has_items
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
does_not = is_not

from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.app.site import VIEW_SITE_MAPPINGS

from nti.app.site.tests import SiteLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.authorization import ROLE_SITE_ADMIN_NAME

from nti.dataserver.tests import mock_dataserver

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
        assert_that(res, has_entries('Class', 'SiteMapping',
                                     'href', '/dataserver2/++etc++hostsites/test_brand_site/++etc++site/SiteMappings/source_site_42',
                                     'MimeType', 'application/vnd.nextthought.persistentsitemapping',
                                     'source_site_name', 'source_site_42',
                                     'target_site_name', 'test_brand_site',
                                     'Creator', 'sjohnson@nextthought.com',
                                     'NTIID', not_none()))
        self.require_link_href_with_rel(res, 'delete')
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

        # Idempotent casing
        data2 = dict(data)
        data2['source_site_name'] = 'SOURCE_sitE_42'
        res = self.testapp.post_json(mappings_rel, data)
        res = res.json_body
        assert_that(res, has_entry('NTIID', first_ntiid))

        # Invalid target site
        data = {'source_site_name': 'source_site_42',
                'target_site_name': 'invalid_target_site'}
        self.testapp.post_json(mappings_rel, data, status=422)

        # A second site
        data = {'source_site_name': 'source_SITE_43',
                'target_site_name': 'test_brand_site'}
        self.testapp.post_json(mappings_rel, data)

        mappings_res = self.testapp.get(mappings_rel)
        mappings_res = mappings_res.json_body
        assert_that(mappings_res, has_entries('Class', 'SiteMappingContainer',
                                              'CreatedTime', not_none(),
                                              'NTIID', not_none(),
                                              'Last Modified', not_none(),
                                              'Items', has_items('source_site_42', 'source_site_43'),
                                              'href', '/dataserver2/SiteMappings'))
        self.require_link_href_with_rel(mappings_res, 'insert')

        # All mappings rel
        mappings_res = self.testapp.get('/dataserver2/AllSiteMappings')
        mappings_res = mappings_res.json_body
        items = mappings_res['Items']
        source_names = [x.get('source_site_name') for x in items]
        assert_that(source_names, has_items('source_site_42', 'source_site_43'))

        # Now can you use these sites as host origin
        for site_name in ('source_site_42', 'SOURCE_SITE_43'):
            env = self._make_extra_environ()
            env["HTTP_ORIGIN"] = 'https://%s' % site_name
            mappings_res = self.testapp.get(mappings_rel, extra_environ=env)
            mappings_res = mappings_res.json_body
            assert_that(mappings_res, has_entries('Class', 'SiteMappingContainer',
                                                  'Items', has_items('source_site_42', 'source_site_43'),
                                                  'href', '/dataserver2/SiteMappings'))

        # Delete
        self.testapp.delete('/dataserver2/++etc++hostsites/test_brand_site/++etc++site/SiteMappings/source_site_42')
        mappings_res = self.testapp.get(mappings_rel)
        mappings_res = mappings_res.json_body
        assert_that(mappings_res, has_entries('Class', 'SiteMappingContainer',
                                              'CreatedTime', not_none(),
                                              'NTIID', not_none(),
                                              'Last Modified', not_none(),
                                              'Items', has_items('source_site_43'),
                                              'href', '/dataserver2/SiteMappings'))

        # What should we do here with a no-longer-mapped site name, 404?
        # This ends up running in 'dataserver2'. In normal usage, this will
        # correspond with a DNS unregistration too.
        env = self._make_extra_environ()
        env["HTTP_ORIGIN"] = 'https://source_site_42'
        mappings_res = self.testapp.get(mappings_rel, extra_environ=env)
        mappings_res = mappings_res.json_body
        assert_that(mappings_res, has_entries('Class', 'SiteMappingContainer',
                                              'Items', has_length(0),
                                              'href', '/dataserver2/SiteMappings'))

        mappings_res = self.testapp.get('/dataserver2/AllSiteMappings')
        mappings_res = mappings_res.json_body
        items = mappings_res['Items']
        source_names = [x.get('source_site_name') for x in items]
        assert_that(source_names, has_item('source_site_43'))
        assert_that(source_names, does_not(has_item('source_site_42')))

