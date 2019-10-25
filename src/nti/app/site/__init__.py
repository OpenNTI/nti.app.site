#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

SITE_ADMIN = "SiteAdmin"
SITE_PROVIDER = 'PROVIDER'
SITE_MIMETYPE = 'application/vnd.nextthought.site'

VIEW_SITE_ADMINS = "SiteAdmins"
VIEW_SITE_BRAND = "SiteBrand"
SITE_SEAT_LIMIT = "SeatLimit"

#: Deleted directory marker
DELETED_MARKER = u"__nti_deleted_marker__"
