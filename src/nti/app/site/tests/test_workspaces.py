#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import json

from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import has_entry
from hamcrest import not_none
from hamcrest import is_

from nti.appserver.workspaces.interfaces import IUserService

from nti.app.site.workspaces import SiteAdminWorkspace

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import StandardExternalFields

CLASS = StandardExternalFields.CLASS
ITEMS = StandardExternalFields.ITEMS


class TestSiteAdminWorkspace(ApplicationLayerTest):

    basic_user = "pgreazy"

    @WithSharedApplicationMockDS(users=True)
    def test_workspace(self):
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(self.basic_user)
            service = IUserService(user)

            workspace = SiteAdminWorkspace(service)

            assert_that(workspace, has_property('context'))
            assert_that(workspace, has_property('user'))

            assert_that(workspace.context, is_(service))
            assert_that(workspace.user, is_(user))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_path_adapter(self):
        res = self.testapp.get('/dataserver2/users/sjohnson%40nextthought.com/SiteAdmin',
                               extra_environ=self._make_extra_environ())

        res_dict = json.loads(res.body)

        assert_that(res_dict, has_entry(CLASS, "Workspace"))

        # For now we have no collections, so just be sure the items are there
        assert_that(res_dict, has_entry(ITEMS, not_none()))
        assert_that(res_dict, has_entry("Title", "SiteAdmin"))
