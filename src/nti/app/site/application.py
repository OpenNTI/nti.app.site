#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: application.py 123134 2017-10-14 02:42:39Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from zope import component

from zope.configuration import xmlconfig

from nti.processlifetime import IApplicationProcessStarting

logger = __import__('logging').getLogger(__name__)


@component.adapter(IApplicationProcessStarting)
def _on_process_starting(event):
    DATASERVER_DIR = os.getenv('DATASERVER_DIR', '')
    dataserver_dir_exists = os.path.isdir(DATASERVER_DIR)
    if dataserver_dir_exists:
        DATASERVER_DIR = os.path.abspath(DATASERVER_DIR)

    def dataserver_file(*args):
        return os.path.join(DATASERVER_DIR, *args)

    def is_dataserver_file(*args):
        return dataserver_dir_exists and os.path.isfile(dataserver_file(*args))

    xml_conf_machine = event.xml_conf_machine
    site_assets_zcml = None
    if is_dataserver_file('etc', 'site_assets.zcml'):
        site_assets_zcml = dataserver_file('etc', 'site_assets.zcml')

    if site_assets_zcml:
        site_assets_zcml = os.path.normpath(os.path.expanduser(site_assets_zcml))
        logger.debug("Loading site_assets settings from %s", site_assets_zcml)
        xml_conf_machine = xmlconfig.file(site_assets_zcml,
                                          package='nti.appserver',
                                          context=xml_conf_machine,
                                          execute=False)

    xml_conf_machine.execute_actions()
