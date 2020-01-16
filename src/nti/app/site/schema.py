#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.interface.interfaces import IComponents

from zope.configuration.exceptions import ConfigurationError

from zope.configuration.fields import DottedName
from zope.configuration.fields import GlobalObject

from zope.schema._bootstrapinterfaces import IFromUnicode

from nti.schema.field import Object

from nti.schema.field import Variant
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
            self.value_type.fromUnicode(tup) for tup in value.split(',') if tup
        )
        return result


class _NamedBaseComponents(DottedName):
    """
    A field representing the name of an IComponents object registered as
    a global utility.
    """

class _GlobalBaseComponents(GlobalObject):

    def __init__(self):
        super(_GlobalBaseComponents, self).__init__(value_type=Object(IComponents))

    def fromUnicode(self, value):
        try:
            return super(_GlobalBaseComponents, self).fromUnicode(value)
        except ImportError:
            raise TypeError('Failed to import global BaseComponent %s' % (value, ))


@interface.implementer(IFromUnicode)
class BaseComponents(Variant):
    """
    A field that represents an IBaseComponent. Provided as a convenience
    for getting IBaseComponent objects from a global or utility
    """

    def __init__(self, **kwargs):
        fields = [_GlobalBaseComponents(),
                  _NamedBaseComponents()]
        super(BaseComponents, self).__init__(fields, **kwargs)

    def fromUnicode(self, value):
        return self.fromObject(value)


