#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_entries
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.app.site import SITE_MIMETYPE

from nti.app.site.interfaces import ISite

from nti.app.site.model import Site

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.externalization.tests import externalizes


class TestModel(ApplicationLayerTest):

    def test_site(self):
        site = Site(Name=u"abydos.nextthought.com", Provider=u"SETI")
        assert_that(site, validly_provides(ISite))
        assert_that(site, verifiably_provides(ISite))

        assert_that(site,
                    externalizes(has_entries('MimeType', SITE_MIMETYPE,
                                             'Name', 'abydos.nextthought.com',
                                             'Provider', 'SETI')))
