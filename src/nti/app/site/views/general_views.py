#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.site.interfaces import ACT_SITE_ADMIN

from nti.app.site.views import SitesPathAdapter

from nti.externalization.externalization import StandardExternalFields

from nti.externalization.interfaces import LocatedExternalDict

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


@view_config(name="all")
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='GET',
               context=SitesPathAdapter,
               permission=ACT_SITE_ADMIN)
class AllSitesView(AbstractAuthenticatedView):

    def __call__(self):
        result = LocatedExternalDict()
        result[ITEMS] = items = []
        result[TOTAL] = result[ITEM_COUNT] = len(items)
        return result
