#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from pyramid.interfaces import IRequest

from pyramid.traversal import find_interface

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.app.site.workspaces.workspaces import ISiteAdminWorkspace

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import SingletonDecorator

from nti.links.links import Link

SYNC_LIBRARIES = 'SyncAllLibraries'
REMOVE_LOCK = 'RemoveSyncLocks'

@component.adapter(ISiteAdminWorkspace, IRequest)
@interface.implementer(IExternalObjectDecorator)
class AdminSyncLibrariesDecorator(AbstractAuthenticatedRequestAwareDecorator):

    __metaclass_ = SingletonDecorator

    def _do_decorate_external(self, context, result_map):
        links = result_map.setdefault("Links", [])
        rels = [SYNC_LIBRARIES, REMOVE_LOCK]
        ds2 = find_interface(context, IDataserverFolder)
        for rel in rels:
            link = Link(ds2,
                        rel=rel,
                        elements=("@@%s" % rel,))
            links.append(link)
