#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import greater_than
does_not = is_not

from nti.dataserver.users.communities import Community

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver


class TestGeneralViews(ApplicationLayerTest):

    default_origin = 'http://janux.ou.edu'

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_all_sites(self):
        href = '/dataserver2/sites/@@all'
        res = self.testapp.get(href, status=200)
        assert_that(res.json_body, 
                    has_entry('Items', has_length(greater_than(0))))
        
    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_create_stie(self):
        href = '/dataserver2/sites/@@create'
        res = self.testapp.post_json(href, 
                                     {'name':'abydos.nextthought.com'}, 
                                     status=200)
        assert_that(res.json_body, 
                    has_entry('Name', is_('abydos.nextthought.com')))
        
        with mock_dataserver.mock_db_trans():
            result = Community.get_community('abydos.nextthought.com')
            assert_that(result, is_not(none()))
            
        href = '/dataserver2/sites/abydos.nextthought.com/@@create'
        res = self.testapp.post_json(href, 
                                     {'name':'seti.nextthought.com'}, 
                                     status=200)

        assert_that(res.json_body, 
                    has_entries('Name', is_('seti.nextthought.com'),
                                'CreatedTime', is_not(none()),
                                'Last Modified', is_not(none())))

        href = '/dataserver2/sites/@@create'
        self.testapp.post_json(href, 
                               {'name':'seti.nextthought.com'}, 
                               status=422)
