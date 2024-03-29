#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.appserver.workspaces import ICollection

from nti.appserver.workspaces.interfaces import IWorkspace


class ISiteAdminWorkspace(IWorkspace):
    """
    Workspace for a particular site admin
    """


class ISiteAdminCollection(ICollection):
    """
    Collection contained by the site admin workspace
    """
