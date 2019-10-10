#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

from nti.appserver.policies.sites import BASEADULT

from nti.testing.base import ConfiguringTestBase

from zope import component

from zope.configuration.exceptions import ConfigurationError

from zope.dottedname import resolve as dottedname

from zope.interface.interfaces import ComponentLookupError
from zope.interface.interfaces import IComponents

from nti.appserver.policies.interfaces import ICommunitySitePolicyUserEventListener

ZCML_REGISTRATION = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>
        <appsite:createSites package="nti.app.sites.ifsta">
            <appsite:createSite site_name="test_one_base"
                                   base_names="nti.app.sites.ifsta.sites.IFSTA,"
                                   parent_name="nti.app.sites.ifsta.sites.IFSTA">

		        <utility factory=".policy.IFSTAFirehouseSitePolicyEventListener" />
            </appsite:createSite>

            <appsite:createSite site_name="test_no_username"
                                   base_names="nti.app.sites.ifsta.sites.IFSTA_CHILD,"
                                   parent_name="nti.app.sites.ifsta.sites.IFSTA_CHILD" />

            <appsite:createSite site_name="test_sequential_registration"
                                   base_names="test_one_base,"
                                   parent_name="test_one_base" />
        </appsite:createSites>
    </configure>
</configure>"""

DOUBLE_ZCML_REGISTRATION = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>
        <appsite:createSites package="nti.app.sites.ifsta">
            <appsite:createSite site_name="test_one_base"
                                   base_names="nti.app.sites.ifsta.sites.IFSTA,"
                                   parent_name="nti.app.sites.ifsta.sites.IFSTA">
            </appsite:createSite>

            <appsite:createSite site_name="test_one_base"
                                   base_names="nti.app.sites.ifsta.sites.IFSTA_CHILD,"
                                   parent_name="nti.app.sites.ifsta.sites.IFSTA_CHILD" />
        </appsite:createSites>
    </configure>
</configure>"""

MISSING_ZCML_REGISTRATION = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>
        <appsite:createSites package="nti.app.sites.ifsta">
            <appsite:createSite site_name="test_one_base"
                                   base_names="missing,"
                                   parent_name="missing">

		        <utility factory=".policy.IFSTAFirehouseSitePolicyEventListener" />
            </appsite:createSite>
        </appsite:createSites>
    </configure>
</configure>"""


class TestSiteZCMLRegistration(ConfiguringTestBase):

    def test_zcml_errors(self):
        # Coverage on error cases
        with self.assertRaises(ConfigurationError):
            self.configure_string(DOUBLE_ZCML_REGISTRATION)

        with self.assertRaises(ConfigurationError):
            self.configure_string(MISSING_ZCML_REGISTRATION)

    def test_zcml_directive(self):
        self.configure_string(ZCML_REGISTRATION)
        test_one_base = component.getUtility(IComponents, name='test_one_base')
        ifsta_base = dottedname.resolve('nti.app.sites.ifsta.sites.IFSTA')
        assert_that(test_one_base.__parent__, is_(ifsta_base))
        assert_that(test_one_base._getBases(), is_((ifsta_base,)))

        test_policy = test_one_base.getUtility(ICommunitySitePolicyUserEventListener)
        assert_that(test_policy, is_not(none()))

        test_no_username = component.getUtility(IComponents,
                                                name='test_no_username')
        ifsta_child_base = dottedname.resolve(
            'nti.app.sites.ifsta.sites.IFSTA_CHILD'
        )
        assert_that(test_no_username.__parent__, is_(ifsta_child_base))
        assert_that(test_no_username._getBases(), is_((ifsta_child_base,)))

        test_policy = test_no_username.queryUtility(ICommunitySitePolicyUserEventListener)
        assert_that(test_policy, is_(none()))

        test_sequential_registration = component.getUtility(IComponents,
                                                            name='test_sequential_registration')
        assert_that(test_sequential_registration.__parent__,
                    is_(test_one_base))
        assert_that(test_sequential_registration._getBases(),
                    is_((test_one_base,)))

        # This child site should share the parent component registry
        test_policy = test_sequential_registration.getUtility(ICommunitySitePolicyUserEventListener)
        assert_that(test_policy, is_not(none()))


REGISTER_BASE_COMPONENTS = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>

    <!-- We can reference a global object as our parent -->
    <appsite:createBaseComponents parent="nti.appserver.policies.sites.BASEADULT" 
                                  name="foo" />


    <!-- Or we can reference IComponents registered globally by name -->
    <appsite:createBaseComponents parent="foo" 
                                  name="bar" /> 
    </configure>
</configure>"""

REGISTER_BASE_COMPONENTS_BAD_NAME = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>

    <!-- Foo doesn't exist -->
    <appsite:createBaseComponents parent="foo" 
                                  name="bar" />
 
    </configure>
</configure>"""

REGISTER_BASE_COMPONENTS_BAD_GLOBAL = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>

    <!-- Foo doesn't exist -->
    <appsite:createBaseComponents parent="nti.appserver.policies.sites" 
                                  name="bar" />
 
    </configure>
</configure>"""

REGISTER_BASE_COMPONENTS_CLOBBER = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>

    <utility
            component="nti.appserver.policies.sites.BASEADULT"
            provides="zope.component.interfaces.IComponents"
            name="genericadultbase" />

    <!-- We can reference a global object as our parent -->
    <appsite:createBaseComponents parent="nti.appserver.policies.sites.BASEADULT" 
                                  name="genericadultbase" />

    </configure>
</configure>"""

class TestBaseComponentCreation(ConfiguringTestBase):

    def test_zcml_creation(self):
        self.configure_string(REGISTER_BASE_COMPONENTS)

        # We expect two globally registerd IComponents
        # "foo" whose base is BASEADULT and "bar" whose parent and base if "foo"

        foo = component.getGlobalSiteManager().getUtility(IComponents, name=u'foo')
        bar = component.getGlobalSiteManager().getUtility(IComponents, name=u'bar')

        assert_that(foo.__parent__, is_(BASEADULT))
        assert_that(foo.__name__, is_(u'foo'))

        assert_that(bar.__parent__, is_(foo))
        assert_that(bar.__name__, is_(u'bar'))

    def test_zcml_bad_named(self):
        with self.assertRaises(ConfigurationError):
            self.configure_string(REGISTER_BASE_COMPONENTS_BAD_NAME)

    def test_zcml_bad_global(self):
        with self.assertRaises(ConfigurationError):
            self.configure_string(REGISTER_BASE_COMPONENTS_BAD_GLOBAL)

    def test_zcml_clobber_registered(self):
        with self.assertRaises(ConfigurationError):
            self.configure_string(REGISTER_BASE_COMPONENTS_CLOBBER)

REGISTER_IN_NAMED = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:appsite="http://nextthought.com/ntp/appsite">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <appsite:createBaseComponents parent="nti.appserver.policies.sites.BASEADULT" 
                                  name="foo" />

    <appsite:createBaseComponents parent="nti.appserver.policies.sites.BASEADULT" 
                                  name="bar" />

    <appsite:registerInNamedComponents registry="foo">
        <utility factory="nti.app.sites.ifsta.policy.IFSTAFirehouseSitePolicyEventListener" />
    </appsite:registerInNamedComponents>

</configure>
"""

class TestRegisterInNamedComponents(ConfiguringTestBase):

    def test_register_in_named(self):
        self.configure_string(REGISTER_IN_NAMED)

        foo_cmps = component.getGlobalSiteManager().getUtility(IComponents, name='foo')
        bar_cmps = component.getGlobalSiteManager().getUtility(IComponents, name='bar')

        assert_that(foo_cmps.getUtility(ICommunitySitePolicyUserEventListener), is_not(none()))

        with self.assertRaises(ComponentLookupError):
            bar_cmps.getUtility(ICommunitySitePolicyUserEventListener)
