#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import component

from nti.app.site.interfaces import ISiteMappingContainer

from nti.app.site.model import SiteMappingContainer

from nti.site.localutility import install_utility

logger = __import__('logging').getLogger(__name__)


def create_site_mapping_container():
    """
    Create a site mapping container in the current site.
    """
    result = SiteMappingContainer()
    install_utility(result,
                    'SiteMappings',
                    ISiteMappingContainer,
                    component.getSiteManager())
    return result
