#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

from zope import component

from zope.component.hooks import getSite

from zope.interface.interfaces import IComponents

from nti.app.site.hostpolicy import create_site

from nti.appserver.policies.sites import BASEADULT

from nti.site.hostpolicy import get_host_site

from nti.site.site import get_component_hierarchy_names

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver


class TestHostPolicy(ApplicationLayerTest):

    default_origin = 'http://janux.ou.edu'

    @WithSharedApplicationMockDS(testapp=False, users=False)
    def test_create_site(self):
        # create root site
        with mock_dataserver.mock_db_trans():
            result = create_site('abydos.nextthought.com')
            assert_that(result, is_not(none()))
            assert_that(result,
                        has_property('__name__', is_('abydos.nextthought.com')))
            assert_that(result,
                        has_property('__parent__', is_not(none())))

            sm = result.getSiteManager()
            assert_that(sm, is_not(none()))
            assert_that(sm,
                        has_property('__parent__', is_(result)))

            bases = (component.getSiteManager(),)
            assert_that(sm,
                        has_property('__bases__', is_(bases)))

            comps = component.queryUtility(IComponents, 
                                           name='abydos.nextthought.com')
            assert_that(comps, is_not(none()))
            assert_that(comps,
                        has_property('__name__', is_('abydos.nextthought.com')))
            assert_that(comps,
                        has_property('__parent__', is_(BASEADULT)))

            bases = (BASEADULT,)
            assert_that(comps,
                        has_property('__bases__', is_(bases)))

        # check it exists
        with mock_dataserver.mock_db_trans():
            result = get_host_site('abydos.nextthought.com')
            assert_that(result, is_not(none()))

        # create subsite
        with mock_dataserver.mock_db_trans(site_name='abydos.nextthought.com'):
            current_site = getSite()
            assert_that(current_site, is_not(none()))
            assert_that(current_site,
                        has_property('__name__', is_('abydos.nextthought.com')))
            result = create_site('seti.nextthought.com')
            assert_that(result, is_not(none()))

            sm = result.getSiteManager()
            assert_that(sm, is_not(none()))
            assert_that(sm,
                        has_property('__parent__', is_(result)))

            bases = (component.getSiteManager(),)
            assert_that(sm,
                        has_property('__bases__', is_(bases)))

            parent = component.getUtility(IComponents, 
                                          name='abydos.nextthought.com')
            comps = component.queryUtility(IComponents, 
                                           name='seti.nextthought.com')
            assert_that(comps, is_not(none()))
            assert_that(comps,
                        has_property('__name__', is_('seti.nextthought.com')))
            assert_that(comps,
                        has_property('__parent__', is_(parent)))
            assert_that(comps,
                        has_property('__bases__', is_((parent,))))

        with mock_dataserver.mock_db_trans(site_name='seti.nextthought.com'):
            names = get_component_hierarchy_names()
            assert_that(names, has_length(2))
            assert_that(names, 
                        is_(['seti.nextthought.com', 'abydos.nextthought.com']))
