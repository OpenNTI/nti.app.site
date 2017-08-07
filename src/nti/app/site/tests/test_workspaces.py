#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import contains_inanyorder

import json

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
        res_dict = self.testapp.get('/dataserver2/users/sjohnson%40nextthought.com/SiteAdmin',
                               extra_environ=self._make_extra_environ())

        assert_that(res_dict.json_body, has_entry(CLASS, "Workspace"))

        # For now we have no collections, so just be sure the items are there
        assert_that(res_dict.json_body, has_entry(ITEMS, not_none()))
        assert_that(res_dict.json_body, has_entry("Title", "SiteAdmin"))

        # pgreazy is not an admin, so it should be nothing
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(self.basic_user)

            res = self.testapp.get('/dataserver2/users/pgreazy/SiteAdmin',
                                   extra_environ=self._make_extra_environ(),
                                   status=404)
        
    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_admin_decoration(self):
        #Get Site Admin workspace
        res_dict = self.testapp.get('/dataserver2/users/sjohnson%40nextthought.com/SiteAdmin',
                               extra_environ=self._make_extra_environ())
        
        assert_that(res_dict.json_body, has_entry(LINKS, not_none()))
        
        links = res_dict.json_body[LINKS]
        assert_that(links, contains_inanyorder(has_entry("rel", "RemoveSyncLocks"),
                                               has_entry("rel", "SyncAllLibraries")))
