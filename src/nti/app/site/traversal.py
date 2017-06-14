#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.traversing.interfaces import ITraversable

from pyramid.interfaces import IRequest

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.traversal import ContainerAdapterTraversable


@interface.implementer(ITraversable)
@component.adapter(IHostPolicyFolder, IRequest)
class HostPolicyTraversable(ContainerAdapterTraversable):

    def traverse(self, key, remaining_path):
        raise KeyError(key)