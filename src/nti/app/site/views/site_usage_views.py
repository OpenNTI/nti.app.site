import six

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from zope import component
from zope.component.hooks import site as current_site

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.site import MessageFactory as _

from nti.app.users.utils import get_site_admins
from nti.app.users.utils import get_user_creation_site

from nti.contenttypes.courses.interfaces import ICourseCatalog

from nti.contenttypes.courses.utils import get_editors
from nti.contenttypes.courses.utils import get_instructors

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IDataserverFolder

from nti.dataserver.users.utils import get_users_by_site

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.site.hostpolicy import get_host_site
from nti.site.hostpolicy import get_all_host_sites

ITEMS = StandardExternalFields.ITEMS
MIMETYPE = StandardExternalFields.MIMETYPE
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IDataserverFolder,
             request_method='GET',
             permission=nauth.ACT_NTI_ADMIN,
             name='get_sites_usage')
class GetSitesUsageView(AbstractAuthenticatedView):
    """
    An endpoint to return site usages for give sites or all sites.
    """
    def _get_parent_courses(self):
        result = set()
        catalog = component.getUtility(ICourseCatalog)
        for level in catalog.values():
            for course in level.values():
                result.add(course)
        return result

    def _get_child_courses(self, courses):
        result = set()
        for course in courses or ():
            for x in course.SubInstances.values():
                result.add(x)
        return result

    def _get_site_admins(self, site):
        admins = get_site_admins(site=site)
        admins = [x for x in admins if get_user_creation_site(x) == site]
        return admins

    def _get_site_admins_and_course_roles(self, site):
        site_admins = set(self._get_site_admins(site))
        instructors = get_instructors(site.__name__)
        editors = get_editors(site.__name__)

        total = site_admins.union(instructors).union(editors)
        return {'total': len(total),
                'site_admins': len(site_admins),
                'instructors': len(instructors),
                'editors': len(editors)}

    def _get_site_usage(self, site):
        # users
        users = get_users_by_site(site.__name__)

        # site admins
        role_users = self._get_site_admins_and_course_roles(site)

        # parent/child courses
        courses = self._get_parent_courses()
        child_courses = self._get_child_courses(courses)

        return {'users': len(users),
                'site_admins': role_users['site_admins'],
                'instructors': role_users['site_admins'],
                'editors': role_users['site_admins'],
                'site_admin_and_course_roles': role_users['site_admins'],
                'courses': len(courses),
                'child_courses': len(child_courses),
                'total_courses': len(courses) + len(child_courses)}

    def _get_items(self):
        items = []
        for site in self._get_sites():
            with current_site(site):
                stats = self._get_site_usage(site)
                items.append({'site_name': site.__name__,
                              'stats': stats})
        return items

    def _get_sites(self):
        try:
            site_names = self.request.params.get('sites')
            if site_names is None:
                site_names = self.request.json_body['sites']
        except ValueError, KeyError:
            return get_all_host_sites()

        if not isinstance(site_names, (list,six.string_types)):
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Sites should be list or a comma delimited string."),
                             },
                             None)

        if isinstance(site_names, six.string_types):
            site_names = [x.strip() for x in site_names.split(',')]

        sites = set()
        for x in site_names:
            site = get_host_site(x, safe=True)
            if site is not None and site not in sites:
                sites.add(site)
        return list(sites)

    def __call__(self):
        result = LocatedExternalDict()
        items = self._get_items()
        result[ITEMS] = items
        result[ITEM_COUNT] = len(items)
        return result
