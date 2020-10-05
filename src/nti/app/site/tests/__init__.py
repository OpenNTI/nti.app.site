#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest

import zope.testing.cleanup

from nti.appserver.policies.site_policies import AdultCommunitySitePolicyEventListener

from nti.app.testing.application_webtest import ApplicationLayerTest
from nti.app.testing.application_webtest import ApplicationTestLayer

from nti.testing.base import AbstractTestBase

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

class TestSitePolicyEventListener(AdultCommunitySitePolicyEventListener):

    COM_ALIAS = u'TEST'
    COM_REALNAME = u"NextThought TEST"
    COM_USERNAME = u'ifsta.nextthought.com'
    DISPLAY_NAME = u'ifsta.nextthought.com'

    BRAND = u'TEST'

    PACKAGE = 'nti.app.site.tests'

    PROVIDER = u'TEST'

    def user_created(self, user, event):
        super(IFSTASitePolicyEventListener, self).user_created(user, event)
        if IImmutableFriendlyNamed.providedBy(user):
            interface.noLongerProvides(user, IImmutableFriendlyNamed)


class SharedConfiguringTestLayer(ApplicationTestLayer):

    set_up_packages = ('nti.app.site', 'nti.app.site.tests')

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls):
        pass

    @classmethod
    def testTearDown(cls):
        pass


class SiteLayerTest(ApplicationLayerTest):

    layer = SharedConfiguringTestLayer
