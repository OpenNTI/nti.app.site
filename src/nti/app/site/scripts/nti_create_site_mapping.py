#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Remove an entity.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.monkey import patch_relstorage_all_except_gevent_on_import
from nti.app.site.model import PersistentSiteMapping
patch_relstorage_all_except_gevent_on_import.patch()

import os
import sys
import argparse

from zope import component

from nti.app.site.interfaces import ISiteMappingContainer

from nti.app.site.utils import create_site_mapping_container

from nti.base._compat import text_

from nti.dataserver.utils import run_with_dataserver

from nti.dataserver.utils.base_script import set_site
from nti.dataserver.utils.base_script import create_context

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import update_from_external_object

MIMETYPE = StandardExternalFields.MIMETYPE

logger = __import__('logging').getLogger(__name__)


def _create_site_mapping(source_site_name, target_site_name):
    set_site(target_site_name)
    container = component.queryUtility(ISiteMappingContainer)
    if container is None:
        container = create_site_mapping_container()
    # Run through internalization
    data = {'source_site_name': source_site_name,
            'target_site_name': target_site_name}
    site_mapping = PersistentSiteMapping()
    update_from_external_object(site_mapping, data, require_updater=True)
    result = container.add_site_mapping(site_mapping)
    if result is not site_mapping:
        print('Mapping already exists')
    else:
        print("Added mapping (%s) (%s)" % (result.source_site_name,
                                           result.target_site_name))


def main():
    arg_parser = argparse.ArgumentParser(description="Create and register a persistent site mapping")
    arg_parser.add_argument('-v', '--verbose', help="Be verbose", action='store_true',
                            dest='verbose')
    arg_parser.add_argument('-s', '--source_site_name',
                            dest='source_site_name',
                            help="The alias site name")

    arg_parser.add_argument('-t', '--target_site_name',
                            dest='target_site_name',
                            help="The target site name")
    args = arg_parser.parse_args()

    env_dir = os.getenv('DATASERVER_DIR')
    if not env_dir or not os.path.exists(env_dir) and not os.path.isdir(env_dir):
        raise IOError("Invalid dataserver environment root directory")

    if not args.source_site_name:
        raise ValueError("Must have source_site_name")

    if not args.target_site_name:
        raise ValueError("Must have target_site_name")

    conf_packages = ('nti.appserver',)
    context = create_context(env_dir, with_library=True)
    source_site_name = text_(args.source_site_name)
    target_site_name = text_(args.target_site_name)

    run_with_dataserver(environment_dir=env_dir,
                        xmlconfig_packages=conf_packages,
                        verbose=args.verbose,
                        context=context,
                        minimal_ds=True,
                        function=lambda: _create_site_mapping(source_site_name,
                                                              target_site_name))
    sys.exit(0)


if __name__ == '__main__':
    main()
