#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from hamcrest import is_
from hamcrest import none
from hamcrest import contains
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import contains_inanyorder

from zope import component
from zope import lifecycleevent

from zope.component.hooks import site
from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from zope.traversing.interfaces import IEtcNamespace

from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import SiteAdminSeatLimitExceededError

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.authorization import ROLE_SITE_ADMIN_NAME

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users import User

from nti.dataserver.users.common import set_user_creation_site
from nti.dataserver.users.common import user_creation_sitename
from nti.dataserver.users.common import remove_user_creation_site

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
            self._create_user_in_site(username=u'foo@bar',
                                      creation_site='ifsta.nextthought.com')
            self._create_user_in_site(username=u'foo2@bar',
                                      creation_site='ifsta.nextthought.com')

            self._create_user_in_site(username=u'ifsta_admin@bar',
                                      creation_site='ifsta.nextthought.com')
            sites = component.queryUtility(IEtcNamespace, name='hostsites')
            ifsta = sites['ifsta.nextthought.com']
            with site(ifsta):
                new_site = getSite()
                prm = IPrincipalRoleManager(new_site)
                prm.assignRoleToPrincipal(ROLE_SITE_ADMIN_NAME,
                                          u'ifsta_admin@bar')

                seat_limit = component.queryUtility(ISiteSeatLimit)
                assert_that(seat_limit.used_seats, is_(3))
                assert_that(seat_limit.admin_used_seats, is_(1))

            # Check caching is working as expected
            self._create_user_in_site(username=u'foo3@bar',
                                      creation_site='ifsta.nextthought.com')
            with site(ifsta):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                assert_that(seat_limit.used_seats, is_(4))
                assert_that(seat_limit.admin_used_seats, is_(1))

            # Check child sites
            ifsta_child = sites['ifsta_child_site']
            with site(ifsta_child):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                assert_that(seat_limit.used_seats, is_(0))
                assert_that(seat_limit.admin_used_seats, is_(1))

            self._create_user_in_site(u'foo7@bar', creation_site='ifsta_child_site')
            with site(ifsta_child):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                assert_that(seat_limit.used_seats, is_(1))

            # Admin usage
            with site(ifsta):
                seat_limit = component.queryUtility(ISiteSeatLimit)
                assert_that(seat_limit.used_seats, is_(4))
                assert_that(seat_limit.admin_used_seats, is_(1))
                assert_that(seat_limit.hard_admin_limit, is_(True))
                assert_that(seat_limit.max_admin_seats, none())
                assert_that(seat_limit.can_add_admin(), is_(True))
                assert_that(seat_limit.validate_admin_seats(), none())
                assert_that(seat_limit.get_admin_seat_usernames(), contains(u'ifsta_admin@bar'))
                user = User.get_user(u'ifsta_admin@bar')
                assert_that(seat_limit.get_admin_seat_users(), contains(user))

                # Now with limit
                seat_limit.max_admin_seats = 1
                assert_that(seat_limit.can_add_admin(), is_(False))
                assert_that(seat_limit.validate_admin_seats(), none())
                assert_that(seat_limit.get_admin_seat_usernames(), contains(u'ifsta_admin@bar'))
                assert_that(seat_limit.get_admin_seat_users(), contains(user))

                seat_limit.max_admin_seats = 0
                assert_that(seat_limit.can_add_admin(), is_(False))
                with self.assertRaises(SiteAdminSeatLimitExceededError):
                    seat_limit.validate_admin_seats()
                assert_that(seat_limit.get_admin_seat_usernames(), contains(u'ifsta_admin@bar'))
                assert_that(seat_limit.get_admin_seat_users(), contains(user))

                # Make soft; even over limit we can add admin
                seat_limit.hard_admin_limit = False
                assert_that(seat_limit.can_add_admin(), is_(True))
                assert_that(seat_limit.validate_admin_seats(), none())

                seat_limit.max_admin_seats = None
                seat_limit.hard_admin_limit = True

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_seat_limit_views(self):
        # Test defaults
        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        # Test adding a user
        with mock_dataserver.mock_db_trans():
            self._create_user_in_site('foo@bar', creation_site='ifsta.nextthought.com')

        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 1))

        # Test child sites GET
        res = self.testapp.get('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        # Test child site POST creates new utility and parent is unaffected
        child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        parent_utils = self._get_number_of_utilities_for_site('ifsta.nextthought.com')

        res = self.testapp.post_json('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                     {'max_seats': 5})
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', 5,
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        updated_child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        updated_parent_utils = self._get_number_of_utilities_for_site('ifsta.nextthought.com')
        assert_that(updated_child_utils, is_(child_utils + 1))
        assert_that(parent_utils, is_(updated_parent_utils))
        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 1))

        # Check edit works and we don't register twice
        res = self.testapp.put_json('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                    {'max_seats': 3})
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', 3,
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        updated_child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        assert_that(updated_child_utils, is_(child_utils + 1))

        # Check child of child inherits from 1 level above
        res = self.testapp.get('https://nextthought-fire1-alpha.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', 3,
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        # Check can set unlimited seats (null value)
        res = self.testapp.post_json('https://nextthought-fire1-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                     {'max_seats': None})
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        res = self.testapp.post_json('https://nextthought-fire1-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                     {'max_seats': 25,
                                      'hard_admin_limit': False,
                                      'max_admin_seats': 10})
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', False,
                                      'max_seats', 25,
                                      'max_admin_seats', 10,
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        # Test DELETE
        self.testapp.delete('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit',
                            status=204)
        updated_child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        updated_parent_utils = self._get_number_of_utilities_for_site('ifsta.nextthought.com')
        assert_that(updated_child_utils, is_(child_utils))
        assert_that(parent_utils, is_(updated_parent_utils))
        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 1))

        res = self.testapp.get('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        res = self.testapp.get('https://nextthought-fire1-alpha.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', False,
                                      'max_seats', 25,
                                      'max_admin_seats', 10,
                                      'admin_used_seats', 0,
                                      'used_seats', 0))


        # Check recreating works
        res = self.testapp.post_json('https://ifsta-alpha.nextthought.com/dataserver2/@@SeatLimit',
                                     {'max_seats': 3})
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', 3,
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 0))

        updated_child_utils = self._get_number_of_utilities_for_site('ifsta-alpha.nextthought.com')
        assert_that(updated_child_utils, is_(child_utils + 1))

        # Admin seats
        with mock_dataserver.mock_db_trans():
            self._create_user_in_site(username=u'seat_limitadmin1',
                                      creation_site='ifsta.nextthought.com')
            self._create_user_in_site(username=u'seat_limitadmin2',
                                      creation_site='ifsta.nextthought.com')
        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 0,
                                      'used_seats', 3))

        self.testapp.post('https://ifsta.nextthought.com/dataserver2/SiteAdmins/%s' % u'seat_limitadmin1')

        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        json = res.json
        assert_that(json, has_entries('hard', False,
                                      'hard_admin_limit', True,
                                      'max_seats', none(),
                                      'max_admin_seats', none(),
                                      'admin_used_seats', 1,
                                      'used_seats', 3))

        self.testapp.post_json('https://ifsta.nextthought.com/dataserver2/@@SeatLimit',
                               {'max_admin_seats': 1})
        res = self.testapp.post('https://ifsta.nextthought.com/dataserver2/SiteAdmins/%s' % u'seat_limitadmin2',
                                status=422)
        res = res.json_body
        assert_that(res, has_entries(u'code', u'MaxAdminSeatsExceeded',
                                      u'message', u'Admin seats exceeded. 2 used out of 1 available. Please contact sales@nextthought.com for additional seats.'))

        # Can force
        self.testapp.post('https://ifsta.nextthought.com/dataserver2/SiteAdmins/%s?force=true' % u'seat_limitadmin2')

        res = self.testapp.get('https://ifsta.nextthought.com/dataserver2/@@SeatLimit')
        res = res.json_body
        assert_that(res, has_entries('hard', False,
                                     'hard_admin_limit', True,
                                     'max_seats', none(),
                                     'max_admin_seats', 1,
                                     'MaxAdminSeats', 1,
                                     'admin_used_seats', 2,
                                     'AdminUsernames', contains_inanyorder('seat_limitadmin1', 'seat_limitadmin2'),
                                     'used_seats', 3))

        # Can null out
        res = self.testapp.post_json('https://ifsta.nextthought.com/dataserver2/@@SeatLimit',
                                     {'max_admin_seats': None})
        res = res.json_body
        assert_that(res, has_entries('hard', False,
                                     'hard_admin_limit', True,
                                     'max_seats', none(),
                                     'max_admin_seats', none(),
                                     'MaxAdminSeats', none(),
                                     'admin_used_seats', 2,
                                     'used_seats', 3))
