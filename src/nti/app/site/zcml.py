#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class

from z3c.baseregistry.baseregistry import BaseComponents

from z3c.baseregistry.zcml import RegisterIn
from z3c.baseregistry.zcml import setActiveRegistry as z3c_setActiveRegistry

from zope import component

from zope import interface

from zope.interface.interfaces import ComponentLookupError

from zope.component.zcml import utility

from zope.configuration.config import GroupingContextDecorator

from zope.configuration.exceptions import ConfigurationError

from zope.configuration.fields import GlobalObject

from zope.configuration.interfaces import IConfigurationContext

from zope.interface.interfaces import IComponents

from nti.app.site.schema import Tuple
from nti.app.site.schema import SiteComponent
from nti.app.site.schema import BaseComponents as BCField

from nti.schema.field import Object
from nti.schema.field import TextLine

logger = __import__('logging').getLogger(__name__)


class ICreateSite(interface.Interface):

    site_name = TextLine(title=u'The name for this site',
                         required=True)

    base_names = Tuple(title=u'A comma separated list of dotted path BaseComponents that will comprise this site.',
                       required=True,
                       value_type=SiteComponent(value_type=Object(IComponents)))

    parent_name = SiteComponent(title=u'The dotted path of the parent BaseComponent.',
                                required=True,
                                value_type=Object(IComponents))


def createSite(_context,
               site_name,
               base_names,
               parent_name):
    site_registry = _context.sites
    if site_name in site_registry:
        raise ConfigurationError(
            u'A site has already been registered with name %s' % site_name
        )
    site_component = BaseComponents(parent_name,
                                    name=site_name,
                                    bases=base_names)
    site_registry[site_name] = site_component

    utility(_context, provides=IComponents,
            component=site_component, name=site_name)

    return site_component


class ICreateSites(interface.Interface):

    package = GlobalObject(title=u'The package in which these sites will be registered.',
                           required=True)


@interface.implementer(IConfigurationContext, ICreateSites)
class Sites(GroupingContextDecorator):
    """
    Handle the creation of sites
    """

    def __init__(self, context, package):
        GroupingContextDecorator.__init__(self, context)
        self.package = package
        self.sites = {}


@interface.implementer(IConfigurationContext, ICreateSite)
class Site(RegisterIn):
    """
    Implements a specific site within a createSites directive
    Subclasses RegisterIn so that registrations within this directive
    are specific to the site context
    """

    def __init__(self, context, site_name, parent_name, base_names):
        self.context = context
        # Create the site so we can do registrations
        registry = createSite(_context=self.context,
                              site_name=site_name,
                              parent_name=parent_name,
                              base_names=base_names)
        super(Site, self).__init__(self.context, registry)

class ICreateBaseComponents(interface.Interface):

    parent = BCField(title=u'Parent components',
                            required=True)

    name = TextLine(title=u'The name to use for these base components. This is also the name the components are globally registered with.',
                    required=True)


def _registry_lookup(name_or_components):
    if IComponents.providedBy(name_or_components):
        return name_or_components
    return component.getGlobalSiteManager().getUtility(IComponents, name=name_or_components)


def _create_and_register_globally(parent, name, parent_factory=_registry_lookup):
    gsm = component.getGlobalSiteManager()
    try:
        already_registered = gsm.getUtility(IComponents, name=name)
        if already_registered is not None:
            raise ConfigurationError(u'IComponents with name %s are already registered'%name, already_registered)
    except ComponentLookupError:
        pass

    try:
        parent = parent_factory(parent)
    except ComponentLookupError:
        raise ConfigurationError(u'parent base components named %s not found' %name)
    
    components = BaseComponents(parent, name=name, bases=(parent, ))
    gsm.registerUtility(components, IComponents, name=name)

def create_and_register_base_components(_context, parent, name):

    _context.action(
        discriminator = ('base_components', parent, name),
        callable = _create_and_register_globally,
        args = (parent, name),
        kw = None
        )

class IRegisterInNamedComponents(interface.Interface):

    registry = BCField(title=u'The registry',
                       description=u'The python path or global utility name of the registry to use',
                       required=True)


def setActiveRegistry(context, registry):
    """
    Wrap z3c.baseregistry.zcml.setActiveRegistry to lookup the
    registry by name if needed.
    """
    registry = _registry_lookup(registry)
    z3c_setActiveRegistry(context, registry)
    
class RegisterInNamedComponents(RegisterIn):

    def __init__(self, context, registry):
        super(RegisterInNamedComponents, self).__init__(context, registry)

    def before(self):
        """
        We need resolve the registry before making it active.
        """
        self.context.action(
            discriminator=None,
            callable=setActiveRegistry,
            args=(self, self.registry)
            )
