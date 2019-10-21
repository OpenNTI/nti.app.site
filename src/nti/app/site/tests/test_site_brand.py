#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import assert_that

from zope import component

from zope.component.hooks import site

from zope.traversing.interfaces import IEtcNamespace

from nti.app.site.interfaces import ISiteBrand

from nti.app.site.tests import SiteLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.communities import Community

from nti.site.hostpolicy import synchronize_host_policies

logger = __import__('logging').getLogger(__name__)


class TestSiteBrand(SiteLayerTest):

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_site_brand(self):
        with mock_dataserver.mock_db_trans():
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
