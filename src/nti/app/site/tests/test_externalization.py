#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import has_properties

from nti.testing.matchers import verifiably_provides

from nti.app.site.model import SiteBrand
from nti.app.site.model import SiteBrandImage
from nti.app.site.model import SiteBrandAssets

from nti.app.site.interfaces import ISiteBrand
from nti.app.site.interfaces import ISiteBrandImage
from nti.app.site.interfaces import ISiteBrandAssets

from nti.app.site.tests import SiteLayerTest

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

CLASS = StandardExternalFields.CLASS
MIMETYPE = StandardExternalFields.MIMETYPE
CREATED_TIME = StandardExternalFields.CREATED_TIME
LAST_MODIFIED = StandardExternalFields.LAST_MODIFIED


class TestExternalization(SiteLayerTest):

    def test_brand(self):
        web_image = SiteBrandImage(source=u'/content/path/web.png',
                                   two_times=u'/content/path/web2x.png')
        mobile_image = SiteBrandImage(source=u'/content/path/mobile')
        login_image = SiteBrandImage(source=u'/content/path/login')
        site_brand_assets = SiteBrandAssets(web=web_image,
                                            mobile=mobile_image,
                                            login=login_image)
        site_brand = SiteBrand(brand_name=u'brand name',
                               assets=site_brand_assets)
        assert_that(web_image,
                    verifiably_provides(ISiteBrandImage))
        assert_that(mobile_image,
                    verifiably_provides(ISiteBrandImage))
        assert_that(login_image,
                    verifiably_provides(ISiteBrandImage))
        assert_that(site_brand_assets,
                    verifiably_provides(ISiteBrandAssets))
        assert_that(site_brand,
                    verifiably_provides(ISiteBrand))

        ext_obj = to_external_object(site_brand)
        assert_that(ext_obj[CLASS], is_('SiteBrand'))
        assert_that(ext_obj[MIMETYPE],
                    is_(SiteBrand.mime_type))
        assert_that(ext_obj[CREATED_TIME], not_none())
        assert_that(ext_obj[LAST_MODIFIED], not_none())

        assets = ext_obj.get('assets')
        assert_that(assets, not_none())
        assert_that(assets[CLASS], is_('SiteBrandAssets'))
        assert_that(assets[MIMETYPE],
                    is_(SiteBrandAssets.mime_type))
        assert_that(assets[CREATED_TIME], not_none())
        assert_that(assets[LAST_MODIFIED], not_none())
        assert_that(assets['background'], none())

        web = assets.get('web')
        assert_that(web, not_none())
        assert_that(web[CLASS], is_('SiteBrandImage'))
        assert_that(web[MIMETYPE],
                    is_(SiteBrandImage.mime_type))
        assert_that(web[LAST_MODIFIED], not_none())
        assert_that(web['source'], is_(web_image.source))
        assert_that(web['two_times'], is_(web_image.two_times))
        assert_that(web['three_times'], none())

        mobile = assets.get('mobile')
        assert_that(mobile, not_none())
        assert_that(mobile[CLASS], is_('SiteBrandImage'))
        assert_that(mobile[MIMETYPE],
                    is_(SiteBrandImage.mime_type))
        assert_that(mobile[CREATED_TIME], not_none())
        assert_that(mobile[LAST_MODIFIED], not_none())
        assert_that(mobile['source'], is_(mobile_image.source))
        assert_that(mobile['two_times'], none())
        assert_that(mobile['three_times'], none())

        login = assets.get('login')
        assert_that(login, not_none())
        assert_that(login[CLASS], is_('SiteBrandImage'))
        assert_that(login[MIMETYPE],
                    is_(SiteBrandImage.mime_type))
        assert_that(login[CREATED_TIME], not_none())
        assert_that(login[LAST_MODIFIED], not_none())
        assert_that(login['source'], is_(login_image.source))
        assert_that(login['two_times'], none())
        assert_that(login['three_times'], none())

        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj, require_updater=True)
        assert_that(new_io, has_properties("brand_name", "brand name",
                                           "assets", has_properties("web",
                                                                    has_properties("source", is_(web_image.source),
                                                                                   "two_times", is_(web_image.two_times)),
                                                                    "mobile",
                                                                    has_properties("source", is_(mobile_image.source)),
                                                                    "login",
                                                                    has_properties("source", is_(login_image.source),
                                                                                   "two_times", none()))))
