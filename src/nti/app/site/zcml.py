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

from zope import interface

from zope.component.zcml import utility

from zope.configuration.config import GroupingContextDecorator

from zope.configuration.exceptions import ConfigurationError

from zope.configuration.fields import GlobalObject

from zope.configuration.interfaces import IConfigurationContext

from zope.interface.interfaces import IComponents

from zope.schema._bootstrapinterfaces import IFromUnicode

from nti.schema.field import Dict
from nti.schema.field import Object
from nti.schema.field import TextLine
from nti.schema.field import Tuple

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class BaseComponentResolveWrapper(object):
    """
    A custom resolve wrapper for GlobalObjects to allow
    BaseComponent resolution if a package name is not provided
    """

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        # delegate what we don't implement
        return getattr(self.wrapped, name)

    def resolve(self, name):
        try:
            comp = self.wrapped.resolve(name)
        except ConfigurationError:
            comp = self.wrapped.sites.get(name)
            if comp is None:
                raise ConfigurationError(u'Unable to find component %s' % name)
        return comp


class SiteComponent(GlobalObject):
    """
    A class to wrap context binding for GlobalObjects
    """

    def bind(self, context):
        new_field = super(SiteComponent, self).bind(context)
        assert new_field.__class__ == self.__class__
        new_field.context = BaseComponentResolveWrapper(new_field.context)
        return new_field


@interface.implementer(IFromUnicode)
class Tuple(Tuple):
    """
    An Tuple schema type that implements fromUnicode to allow schema validation from ZCML input
    """

    def fromUnicode(self, value):
        result = tuple(self.value_type.fromUnicode(tup) for tup in value.split(u',') if tup)
        return result


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

    site_component = BaseComponents(parent_name,
                                    name=site_name,
                                    bases=base_names)
    if site_name in site_registry:
        raise ConfigurationError(u'A site has already been registered with name %s' % site_name)
    site_registry[site_name] = site_component

    utility(_context, provides=IComponents, component=site_component, name=site_name)

    return site_component


class ICreateSites(interface.Interface):
    package = GlobalObject(title=u'The package in which these sites will be registered.',
                           required=True)


class ISites(interface.Interface):
    sites = Dict(title=u'The sites to be created.')

    package = GlobalObject(title=u'The package in which these sites will be registered.',
                           required=True)


def persistentSiteRegistration(package, sites):
    """
    This function is a placeholder for future development.
    We have discussed the desire to persist site registrations in a more accessible manner
    to allow for a site management API. This could be a logical place to persist these sites;
    however, it may be challenging depending upon what state the server is in during
    the initialization process at this point.
    """
    pass


@interface.implementer(IConfigurationContext, ISites)
class Sites(GroupingContextDecorator):
    """
    Handle the creation of sites
    """

    def __init__(self, context, package):
        self.context = context
        self.package = package
        self.sites = {}

    def after(self):
        self.action(
            discriminator=('PersistentSiteRegistration', self.package),
            callable=persistentSiteRegistration,
            args=(self.package, self.sites),
        )


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
