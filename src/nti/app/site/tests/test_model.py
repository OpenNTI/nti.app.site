#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_not
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_properties
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.app.site import SITE_MIMETYPE

from nti.app.site.interfaces import ISite

from nti.app.site.model import Site
from nti.app.site.model import PersistentSiteMapping

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.externalization import to_external_object

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.externalization.tests import externalizes

from nti.site.site import SiteMapping


class TestModel(ApplicationLayerTest):

    def test_site(self):
        site = Site(Name=u"abydos.nextthought.com", Provider=u"SETI")
        assert_that(site, validly_provides(ISite))
        assert_that(site, verifiably_provides(ISite))

        assert_that(site,
                    externalizes(has_entries('MimeType', SITE_MIMETYPE,
                                             'Name', 'abydos.nextthought.com',
                                             'Provider', 'SETI')))

    def test_site_mapping(self):
        mapping = SiteMapping(source_site_name=u"source",
                              target_site_name=u"target")
        ext_obj = to_external_object(mapping)
        assert_that(ext_obj,
                    has_entries('Class', 'SiteMapping',
                                'source_site_name', 'source',
                                'target_site_name', 'target'))

    def test_persistent_site_mapping(self):
        mapping = PersistentSiteMapping(source_site_name=u"source",
                                        target_site_name=u"target")
        ext_obj = to_external_object(mapping)
        assert_that(ext_obj,
                    has_entries('Class', 'SiteMapping',
                                'source_site_name', 'source',
                                'CreatedTime', not_none(),
                                'Last Modified', not_none(),
                                'MimeType', mapping.mimeType,
                                'target_site_name', 'target'))

        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj, require_updater=True)
        assert_that(new_io, has_properties("source_site_name", "source",
                                           'target_site_name', "target"))

        # Casing
        ext_obj['source_site_name'] = u'SOURCE'
        ext_obj['target_site_name'] = u'TARGET'
        new_io = factory()
        update_from_external_object(new_io, ext_obj, require_updater=True)
        assert_that(new_io, has_properties("source_site_name", "source",
                                           'target_site_name', "target"))
