#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import greater_than
does_not = is_not

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS


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
        
        href = '/dataserver2/sites/abydos.nextthought.com/@@create'
        res = self.testapp.post_json(href, 
                                     {'name':'seti.nextthought.com'}, 
                                     status=200)
        assert_that(res.json_body, 
                    has_entry('Name', is_('seti.nextthought.com')))

        href = '/dataserver2/sites/@@create'
        self.testapp.post_json(href, 
                               {'name':'seti.nextthought.com'}, 
                               status=422)
