#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import is_
from hamcrest import none

from zope import component
from zope import lifecycleevent

from zope.component.hooks import site

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from zope.traversing.interfaces import IEtcNamespace

from nti.app.site.interfaces import ISiteSeatLimit

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.authorization import ROLE_SITE_ADMIN_NAME

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users import User

from nti.dataserver.users.common import remove_user_creation_site
from nti.dataserver.users.common import set_user_creation_site
from nti.dataserver.users.common import user_creation_sitename

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class TestSeatLimit(ApplicationLayerTest):

    def _create_user_in_site(self, username, creation_site):
        user = User.create_user(username=username)
        remove_user_creation_site(user)
        set_user_creation_site(user, creation_site)
        assert_that(user_creation_sitename(user), is_(creation_site))
        lifecycleevent.modified(user)
        return user

    def _get_number_of_utilities_for_site(self, name):
        with mock_dataserver.mock_db_trans():
            sites = component.queryUtility(IEtcNamespace, name='hostsites')
            hpf = sites[name]
            sm = hpf.getSiteManager()
            return len(list(sm.registeredUtilities()))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_seat_limit(self):
        with mock_dataserver.mock_db_trans():
            self._create_user_in_site(username=u'foo@bar', creation_site='ifsta.nextthought.com')
            self._create_user_in_site(username=u'foo2@bar', creation_site='ifsta.nextthought.com')
            sites = component.queryUtility(IEtcNamespace, name='hostsites')
            ifsta = sites['ifsta.nextthought.com']
            with site(ifsta):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                used = seat_limit.used_seats
                assert_that(used, is_(2))

            # Check caching is wokring as expected
            self._create_user_in_site(username=u'foo3@bar', creation_site='ifsta.nextthought.com')
            with site(ifsta):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                used = seat_limit.used_seats
                assert_that(used, is_(3))

            # Check admins arent included (TODO we are lacking coverage on content and nti admins)
            site_admin = self._create_user_in_site(username=u'foo4@bar', creation_site='ifsta.nextthought.com')
            prm = IPrincipalRoleManager(ifsta)
            prm.assignRoleToPrincipal(ROLE_SITE_ADMIN_NAME, site_admin.username)
            with site(ifsta):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                used = seat_limit.used_seats
                assert_that(used, is_(3))

            # Check child sites
            ifsta_child = sites['ifsta_child_site']
            with site(ifsta_child):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                used = seat_limit.used_seats
                assert_that(used, is_(0))

            self._create_user_in_site(u'foo7@bar', creation_site='ifsta_child_site')
            with site(ifsta_child):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                used = seat_limit.used_seats
                assert_that(used, is_(1))

            with site(ifsta):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                used = seat_limit.used_seats
                assert_that(used, is_(3))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_seat_limit_views(self):

        # Test defaults
        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(none()),
                                      'used_seats', is_(0)))

        # Test adding a user
        with mock_dataserver.mock_db_trans():
            self._create_user_in_site('foo@bar', creation_site='ifsta.nextthought.com')

        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(none()),
                                      'used_seats', is_(1)))

        # Test child sites GET
        res = self.testapp.get('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(none()),
                                      'used_seats', is_(0)))

        # Test child site POST creates new utility and parent is unaffected
        child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        parent_utils = self._get_number_of_utilities_for_site('ifsta.nextthought.com')

        res = self.testapp.post_json('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                     {'max_seats': 5})
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(5),
                                      'used_seats', is_(0)))
        updated_child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        updated_parent_utils = self._get_number_of_utilities_for_site('ifsta.nextthought.com')
        assert_that(updated_child_utils, is_(child_utils + 1))
        assert_that(parent_utils, is_(updated_parent_utils))
        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(none()),
                                      'used_seats', is_(1)))

        # Check edit works and we don't register twice
        res = self.testapp.put_json('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                    {'max_seats': 3})
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(3),
                                      'used_seats', is_(0)))
        updated_child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        assert_that(updated_child_utils, is_(child_utils + 1))

        # Check child of child inherits from 1 level above
        res = self.testapp.get('https://nextthought-fire1-alpha.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', is_(False),
                                      'max_seats', is_(5),
                                      'used_seats', is_(0)))

