#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import greater_than
from hamcrest import has_property
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from zope.annotation.interfaces import IAnnotations

from nti.app.site.interfaces import ISite

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.dataserver.interfaces import ICommunity
from nti.dataserver.interfaces import ISiteCommunity

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.communities import Community

from nti.site.hostpolicy import get_host_site


class TestGeneralViews(ApplicationLayerTest):

    default_origin = 'http://janux.ou.edu'

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_all_sites(self):
        href = '/dataserver2/sites/@@all'
        res = self.testapp.get(href, status=200)
        assert_that(res.json_body,
                    has_entry('Items', has_length(greater_than(0))))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_create_site(self):
        href = '/dataserver2/sites/@@create'
        res = self.testapp.post_json(href,
                                     {'name': 'abydos.nextthought.com',
                                      'provider': 'seti'},
                                     status=200)
        assert_that(res.json_body,
                    has_entries('Name', is_('abydos.nextthought.com'),
                                'Class', is_('Site'),
                                'MimeType', is_('application/vnd.nextthought.site')))

        with mock_dataserver.mock_db_trans():
            result = Community.get_community('abydos.nextthought.com')
            assert_that(result, is_not(none()))
            assert_that(result, validly_provides(ISiteCommunity))
            assert_that(result, verifiably_provides(ISiteCommunity))

            site = get_host_site('abydos.nextthought.com')
            assert_that(ICreated.providedBy(site), is_(True))
            assert_that(ILastModified.providedBy(site), is_(True))
            assert_that(site,
                        has_property('creator', is_(self.default_username.lower())))

            annotations = IAnnotations(site)
            assert_that(annotations, has_entry('PROVIDER', 'SETI'))

            community = ICommunity(site, None)
            assert_that(community, none())

        href = '/dataserver2/sites/abydos.nextthought.com/@@create'
        res = self.testapp.post_json(href,
                                     {'name': 'seti.nextthought.com'},
                                     status=200)

        assert_that(res.json_body,
                    has_entries('Name', is_('seti.nextthought.com'),
                                'CreatedTime', is_not(none()),
                                'Last Modified', is_not(none())))

        href = '/dataserver2/sites/@@create'
        self.testapp.post_json(href,
                               {'name': 'seti.nextthought.com'},
                               status=422)
        
    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_adapters(self):
        with mock_dataserver.mock_db_trans():
            Community.create_community(username='ifsta.nextthought.com')

        href = '/dataserver2/sites/ifsta.nextthought.com/@@create'
        self.testapp.post_json(href,
                               {'name': 'myfirehouse.ifsta.com'},
                                status=200)

        with mock_dataserver.mock_db_trans():
            site = get_host_site('myfirehouse.ifsta.com')
            community = ICommunity(site, None)
            assert_that(community, is_not(none()))

            site = ISite(site, None)
            assert_that(site, is_not(none()))
            assert_that(site, has_property('Provider', 'IFSTA'))
