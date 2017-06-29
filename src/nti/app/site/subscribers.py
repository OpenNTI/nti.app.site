#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.lifecycleevent.interfaces import IObjectCreatedEvent
    
from nti.base.interfaces import ICreated

from nti.dataserver.users.communities import Community

from nti.site.interfaces import IHostPolicyFolder


@component.adapter(IHostPolicyFolder, IObjectCreatedEvent)
def _on_site_created(site, event):
    if ICreated.providedBy(site):
        name = site.__name__
        if Community.get_community(name) is None:
            Community.create_community(username=name)
