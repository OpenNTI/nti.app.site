#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.configuration.exceptions import ConfigurationError

from zope.configuration.fields import GlobalObject

from zope.schema._bootstrapinterfaces import IFromUnicode

from nti.schema.field import Tuple as SchemaTuple

logger = __import__('logging').getLogger(__name__)


class BaseComponentResolveWrapper(object):
    """
    A custom resolve wrapper for GlobalObjects to allow
    BaseComponent resolution if a package name is not provided
    """

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):  # pragma: no cover
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
class Tuple(SchemaTuple):
    """
    A Tuple schema type that implements fromUnicode to allow schema validation from ZCML input
    """

    def fromUnicode(self, value):
        result = tuple(
            self.value_type.fromUnicode(tup) for tup in value.split(u',') if tup
        )
        return result
