#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generic views for any user (or sometimes, entities).

.. $Id: authorization_views.py 125436 2018-01-11 20:05:13Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unicodecsv as csv

from pyramid import httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from pyramid.view import view_config

from requests.structures import CaseInsensitiveDict

from zope import component

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from zope.event import notify

from zope.intid.interfaces import IIntIds

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.internalization import read_body_as_external_object

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.users.views.view_mixins import UsersCSVExportMixin
from nti.app.users.views.view_mixins import AbstractUserViewMixin

from nti.app.site import VIEW_SITE_ADMINS

from nti.app.site import MessageFactory as _

from nti.app.site.interfaces import ISiteSeatLimit
from nti.app.site.interfaces import SiteAdminAddedEvent
from nti.app.site.interfaces import SiteAdminRemovedEvent
from nti.app.site.interfaces import SiteAdminSeatLimitExceededError

from nti.app.users.utils import get_site_admins
from nti.app.users.utils import get_user_creation_site
from nti.app.users.utils import set_user_creation_site

from nti.common.string import is_true

from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.authorization import is_admin
from nti.dataserver.authorization import is_site_admin

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IDataserverFolder
from nti.dataserver.interfaces import ISiteAdminUtility

from nti.dataserver.users.users import User

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

TOTAL = StandardExternalFields.TOTAL
ITEMS = StandardExternalFields.ITEMS
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


def raise_error(data, tb=None,
                factory=hexc.HTTPUnprocessableEntity,
                request=None):
    request = request or get_current_request()
    raise_json_error(request, factory, data, tb)


class SiteAdminAbstractView(AbstractAuthenticatedView):

    def _do_call(self):
        raise NotImplementedError()

    @Lazy
    def is_admin(self):
        return is_admin(self.remoteUser)

    def _predicate(self):
        if not self.is_admin and not is_site_admin(self.remoteUser):
            raise hexc.HTTPForbidden(_('Cannot view site administrators.'))

    def _get_site_admins(self, site=None):
        site_admins = get_site_admins(site)
        result = []
        site = getSite() if site is None else site
        for site_admin in site_admins:
            if      self.can_administer_user(site_admin) \
                and self.is_user_created_in_site(site, site_admin):
                result.append(site_admin)
        return result

    @Lazy
    def site_admin_utility(self):
        return component.getUtility(ISiteAdminUtility)

    def is_user_created_in_site(self, site, user):
        return site == get_user_creation_site(user)

    def can_administer_user(self, user):
        result = True
        if not self.is_admin:
            # pylint: disable=no-member
            result = self.site_admin_utility.can_administer_user(self.remoteUser, user)
        return result

    def _get_site_admin_external(self):
        result = LocatedExternalDict()
        site_admins = self._get_site_admins()
        ext_site_admins = []
        for site_admin in ext_site_admins:
            ext_site_admin = to_external_object(site_admin,
                                                name='admin-summary')
            ext_site_admins.append(ext_site_admin)
        result[ITEMS] = ext_site_admins
        result[ITEM_COUNT] = result[TOTAL] = len(site_admins)
        return result

    def __call__(self):
        self._predicate()
        return self._do_call()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             name=VIEW_SITE_ADMINS,
             accept='application/json',
             request_method='GET')
class SiteAdminGetView(SiteAdminAbstractView,
                       AbstractUserViewMixin):
    """
    Return all site admins for the given site.
    """

    def get_entity_intids(self, site=None):
        intids = component.getUtility(IIntIds)
        for user in self._get_site_admins(site):
            doc_id = intids.getId(user)
            yield doc_id

    def get_externalizer(self, unused_user):
        # Only admins should be able to fetch these
        return 'admin-summary'

    def _do_call(self):
        return AbstractUserViewMixin._do_call(self)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             name=VIEW_SITE_ADMINS,
             accept='text/csv',
             request_method='GET')
class SiteAdminCSVView(SiteAdminGetView,
                       UsersCSVExportMixin):

    def _get_filename(self):
        return u'admin_export.csv'

    def __call__(self):
        return self._create_csv_response()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             name=VIEW_SITE_ADMINS,
             request_method='POST',
             request_param='format=text/csv')
class SiteAdminCSVPOSTView(SiteAdminCSVView, 
                           ModeledContentUploadRequestUtilsMixin):
    
    def readInput(self):
        if self.request.POST:
            result = {'usernames': self.request.params.getall('usernames') or []}
        elif self.request.body:
            result = super(SiteAdminCSVPOSTView, self).readInput()
        else:
            result = self.request.params
        return CaseInsensitiveDict(result)
    
    @Lazy
    def _params(self):
        return self.readInput()

    def _get_result_iter(self):
        usernames = self._params.get('usernames', ())
        if not usernames:
            return super(SiteAdminCSVPOSTView, self)._get_result_iter()
        intids = component.getUtility(IIntIds)
        result = []
        for username in usernames:
            user = User.get_user(username)
            if user is None:
                continue
            user_intid = intids.queryId(user)
            if user_intid is None:
                continue
            # Validate the user is in the original result set
            if user_intid in self.filtered_intids:
                result.append(user) 
        return result


class SiteAdminAbstractUpdateView(SiteAdminAbstractView,  # pylint: disable=abstract-method
                                  ModeledContentUploadRequestUtilsMixin):

    def readInput(self, unused_value=None):
        if self.request.body:
            values = read_body_as_external_object(self.request)
        else:
            values = self.request.params
        result = CaseInsensitiveDict(values)
        return result

    @Lazy
    def _params(self):
        return self.readInput()

    def _get_usernames(self):
        # pylint: disable=no-member
        values = self._params
        result = values.get('name') \
              or values.get('user') \
              or values.get('users') \
              or values.get('username') \
              or values.get('usernames')
        if not result and self.request.subpath:
            result = self.request.subpath[0]
        if not result:
            raise_error({
                'message': _(u"No users given."),
                'code': 'NoUsersGiven',
            })
        result = result.split(',')
        return result

    def validate_user(self, user):
        if not IUser.providedBy(user):
            raise_error({
                    'message': _(u"User not found."),
                    'code': 'UserNotFoundError',
                    },
                    factory=hexc.HTTPNotFound)
        if not self.can_administer_user(user):
            raise_error({
                    'message': _(u"Cannot admin this user."),
                    'code': 'UserAdminPermissionError',
                    },
                    factory=hexc.HTTPForbidden)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             name=VIEW_SITE_ADMINS,
             request_method='POST')
class SiteAdminInsertView(SiteAdminAbstractUpdateView):
    """
    Insert a site admin. The site admin must have a user creation site of the
    current site. If not, we will update when given the `update_site` flag.
    """

    @Lazy
    def update_creation_site(self):
        # pylint: disable=no-member
        values = self._params
        result = values.get('update_site') \
              or values.get('update_creation_site')
        return is_true(result)

    def _validate_site_admin(self, username, site):
        user = User.get_user(username)
        self.validate_user(user)
        user_creation_site = get_user_creation_site(user)
        if      user_creation_site is not None \
            and user_creation_site != site:
            if self.update_creation_site:
                logger.info('Updating user creation site (new=%s) (old=%s) (user=%s)',
                            site.__name__,
                            user_creation_site.__name__,
                            username)
                set_user_creation_site(user, site)
            else:
                raise_error({
                    'message': _(u"Site admin created in incorrect site."),
                    'code': 'InvalidSiteAdminCreationSite',
                    })
        elif user_creation_site is None:
            set_user_creation_site(user, site)

    def post_validate(self):
        """
        Validate site admin counts
        """
        if      is_true(self._params.get('force')) \
            and self.is_admin:
            return
        seat_limit = component.queryUtility(ISiteSeatLimit)
        try:
            seat_limit.validate_admin_seats()
        except SiteAdminSeatLimitExceededError as e:
            raise_error({
                    'message': e.message,
                    'code': 'MaxAdminSeatsExceeded',
                    })

    def _do_call(self):
        site = getSite()
        if site.__name__ == 'dataserver2':
            raise_error({
                    'message': _(u"Must assign a site admin to a valid site."),
                    'code': 'InvalidSiteAdminSiteError',
                    })
        principal_role_manager = IPrincipalRoleManager(site)
        for username in self._get_usernames():
            self._validate_site_admin(username, site)
            logger.info("Adding user to site admin role (site=%s) (user=%s)",
                        site.__name__,
                        username)
            # pylint: disable=too-many-function-args
            principal_role_manager.assignRoleToPrincipal(ROLE_SITE_ADMIN.id,
                                                         username)
            user = User.get_user(username)
            notify(SiteAdminAddedEvent(user))
        self.post_validate()
        return self._get_site_admin_external()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             name=VIEW_SITE_ADMINS,
             request_method='DELETE')
class SiteAdminDeleteView(SiteAdminAbstractUpdateView):
    """
    Remove the given site admin.
    """

    def _do_call(self):
        site = getSite()
        principal_role_manager = IPrincipalRoleManager(site)
        for username in self._get_usernames():
            user = User.get_user(username)
            self.validate_user(user)
            user_creation_site = get_user_creation_site(user)
            if user_creation_site != site:
                raise_error({
                    'message': _(u"Admin roles cannot be changed for users created in other sites."),
                    'code': 'AdminRoleChangeError',
                    },
                    factory=hexc.HTTPUnprocessableEntity)
            logger.info("Removing user from site admin role (site=%s) (user=%s)",
                        site.__name__,
                        username)
            # pylint: disable=too-many-function-args
            principal_role_manager.removeRoleFromPrincipal(ROLE_SITE_ADMIN.id,
                                                           username)
            user = User.get_user(username)
            notify(SiteAdminRemovedEvent(user))
        return self._get_site_admin_external()
