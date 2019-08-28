#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.app.site.communities import SiteCommunity

from nti.base.interfaces import ICreated

from nti.site.interfaces import IHostPolicyFolder

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicyFolder, IObjectCreatedEvent)
def _on_site_created(site, unused_event=None):
    if ICreated.providedBy(site):
        name = site.__name__
        if SiteCommunity.get_community(name) is None:
            SiteCommunity.create_community(username=name)
