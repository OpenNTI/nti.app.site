#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import has_length

from zope import component

from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.app.site.tests import SiteLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.authorization import ROLE_SITE_ADMIN
from nti.dataserver.authorization import ROLE_SITE_ADMIN_NAME

from nti.dataserver.interfaces import IGroupMember

from nti.dataserver.tests import mock_dataserver


class TestSiteAdminGroupsProvider(SiteLayerTest):

    @WithSharedApplicationMockDS(users="site.admin")
    def test_site_admin(self):
        with mock_dataserver.mock_db_trans(self.ds, site_name='alpha.nextthought.com'):
            admin = self._get_user("site.admin")
            site = getSite()
            prm = IPrincipalRoleManager(site)
            prm.assignRoleToPrincipal(ROLE_SITE_ADMIN_NAME, 'site.admin')

            groups = component.getAdapter(admin, IGroupMember, name="SiteAdminGroupsProvider").groups
            assert_that(groups, has_length(1))
            assert_that(groups, contains(ROLE_SITE_ADMIN))

    @WithSharedApplicationMockDS(users="not.site.admin")
    def test_non_site_admin(self):
        with mock_dataserver.mock_db_trans(self.ds, site_name='alpha.nextthought.com'):
            admin = self._get_user("not.site.admin")

            groups = component.getAdapter(admin, IGroupMember, name="SiteAdminGroupsProvider").groups
            assert_that(groups, has_length(0))

