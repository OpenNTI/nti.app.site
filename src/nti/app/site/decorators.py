#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: decorators.py 125436 2018-01-11 20:05:13Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRequest

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import SeatAlgorithmContextSourceBinder

from nti.app.site.workspaces.interfaces import ISiteAdminWorkspace

from nti.app.site import VIEW_SITE_ADMINS

from nti.coremetadata.interfaces import IObjectJsonSchemaMaker

from nti.coremetadata.jsonschema import FIELDS

from nti.dataserver.authorization import is_admin_or_site_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator
from nti.externalization.interfaces import IExternalObjectDecorator

from nti.links.links import Link

from nti.traversal.traversal import find_interface

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ISiteAdminWorkspace, IRequest)
@interface.implementer(IExternalObjectDecorator)
class SiteAdminWorkspaceDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, unused_context, unused_result):
        return is_admin_or_site_admin(self.remoteUser)

    def _do_decorate_external(self, context, result_map):  # pylint: disable=arguments-differ
        links = result_map.setdefault("Links", [])
        rels = [VIEW_SITE_ADMINS]
        ds2 = find_interface(context, IDataserverFolder)
        for rel in rels:
            link = Link(ds2,
                        rel=rel,
                        elements=("%s" % rel,))
            links.append(link)


@component.adapter(ISiteSeatLimit, IRequest)
@interface.implementer(IExternalMappingDecorator)
class SiteSeatLimitDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, unused_context, unused_result):
        return is_admin_or_site_admin(self.remoteUser)

    def _do_decorate_external(self, context, result):
        schemafier = component.getUtility(IObjectJsonSchemaMaker)
        schema = schemafier.make_schema(ISiteSeatLimit)
        schema = schema[FIELDS]
        # Schema maker has no context so choices that are derived from 'source' field aren't built
        # we post process that in here.
        choice = SeatAlgorithmContextSourceBinder()
        choice_vocab = choice(context)
        schema['seat_algorithm']['choices'] = choice_vocab.by_value.keys()
        result['schema'] = schema
