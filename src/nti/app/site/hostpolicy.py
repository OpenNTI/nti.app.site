#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for host policies and sites

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import re

from zope import component

from zope.component.hooks import getSite

from zope.interface.interfaces import IComponents

from zope.traversing.interfaces import IEtcNamespace

from nti.appserver.policies.sites import BASEADULT

from nti.site.folder import HostPolicyFolder
from nti.site.folder import HostPolicySiteManager

from nti.site.site import BTreePersistentComponents

from nti.site.utils import registerUtility

pattern = r'^([a-z0-9]|[a-z0-9][a-z0-9\-]{0,61}[a-z0-9])(\.([a-z0-9]|[a-z0-9][a-z0-9\-]{0,61}[a-z0-9]))*$'
pattern = re.compile(pattern)

logger = __import__('logging').getLogger(__name__)


def is_valid_site_name(name):
    return bool(pattern.match(name) is not None)


def create_site(name, default_base=BASEADULT):
    """
    create a site with the specified name

    :param name: Site name
    :keyword default_base: Default parent base specification for root sites
    """
    logger.info("Installing site policy %s", name)
    hostsites = component.getUtility(IEtcNamespace, name='hostsites')
    ds_folder = hostsites.__parent__  # by definiton
    #  get current components
    site_name = getattr(getSite(), '__name__', None) or ''
    parent = component.queryUtility(IComponents, name=site_name)
    if parent is None:
        parent = default_base
        secondary_comps = ds_folder.getSiteManager()
    else:
        secondary_comps = component.getSiteManager()
    # create site components
    comps = BTreePersistentComponents(name=name, bases=(parent,))
    comps.__parent__ = parent
    # register components
    registerUtility(ds_folder.getSiteManager(),
                    comps,
                    provided=IComponents,
                    name=name)
    # create policy folder
    result = HostPolicyFolder()
    hostsites[name] = result
    site_policy = HostPolicySiteManager(result)
    site_policy.__bases__ = (secondary_comps,)
    # set the site manager and return
    result.setSiteManager(site_policy)
    return result
