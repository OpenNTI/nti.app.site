#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_property

from nti.app.site import SITE_SEAT_LIMIT

from nti.appserver.workspaces.interfaces import IUserService

from nti.app.site.workspaces.workspaces import SiteAdminWorkspace

from nti.externalization.interfaces import StandardExternalFields

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver

CLASS = StandardExternalFields.CLASS
ITEMS = StandardExternalFields.ITEMS
LINKS = StandardExternalFields.LINKS


class TestSiteAdminWorkspace(ApplicationLayerTest):

    basic_user = "pgreazy"

    @WithSharedApplicationMockDS(users=True)
    def test_workspace(self):
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._get_user('sjohnson@nextthought.com')
            service = IUserService(user)

            workspace = SiteAdminWorkspace(service)

            assert_that(workspace, has_property('context'))
            assert_that(workspace, has_property('user'))

            assert_that(workspace.context, is_(service))
            assert_that(workspace.user, is_(user))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_path_adapter(self):
        # This is an admin, so they should have the workspace
        res = self.testapp.get('/dataserver2/users/sjohnson%40nextthought.com/SiteAdmin',
                               extra_environ=self._make_extra_environ())

        assert_that(res.json_body, has_entry(CLASS, "Workspace"))

        # For now we have no collections, so just be sure the items are there
        assert_that(res.json_body, has_entry(ITEMS, not_none()))
        assert_that(res.json_body, has_entry("Title", "SiteAdmin"))

        # pgreazy is not an admin, so it should be nothing
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(self.basic_user)
        self.testapp.get('/dataserver2/users/pgreazy/SiteAdmin',
                         extra_environ=self._make_extra_environ(),
                         status=404)

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_admin_decoration(self):
        # Get Site Admin workspace
        res = self.testapp.get('/dataserver2/users/sjohnson%40nextthought.com/SiteAdmin',
                               extra_environ=self._make_extra_environ())
        self.require_link_href_with_rel(res.json_body, 'RemoveSyncLock')
        self.require_link_href_with_rel(res.json_body, 'SyncAllLibraries')

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_site_seat_limit_link(self):
        # Get the global workspace
        res = self.testapp.get('/dataserver2')
        for workspace in res.json_body['Items']:
            if workspace.get('Title', None) == 'Global':
                global_workspace = workspace
                break
        assert_that(global_workspace, is_(not_none()))
        self.require_link_href_with_rel(global_workspace, SITE_SEAT_LIMIT)
