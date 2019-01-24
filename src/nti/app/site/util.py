#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def queryUtilityOnlyInManager(sm, required, name=''):
    """
    Queries for a utility scoped to a manager
    """
    utility =  sm._utility_registrations.get((required, name))
    if utility is not None:
        return utility[0]
    return None
