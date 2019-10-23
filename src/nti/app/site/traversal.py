#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRequest

from zope import component
from zope import interface

from zope.traversing.interfaces import ITraversable

from nti.site.interfaces import IHostPolicyFolder
from nti.site.interfaces import IHostPolicySiteManager

from nti.traversal.traversal import ContainerAdapterTraversable

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ITraversable)
@component.adapter(IHostPolicyFolder, IRequest)
class HostPolicyTraversable(ContainerAdapterTraversable):

    def traverse(self, key, remaining_path):
        raise KeyError(key)


@interface.implementer(ITraversable)
@component.adapter(IHostPolicySiteManager, IRequest)
class HostSiteManagerTraversable(ContainerAdapterTraversable):
    pass
