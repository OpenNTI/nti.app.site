#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides functions for getting sites usage information from platform.
and pushing the usage into prometheus and/or pendo.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import time
import argparse
import requests

from urlparse import urljoin

from requests.auth import HTTPBasicAuth


SITES_USAGE_ENDPOINT = u'/dataserver2/@@get_sites_usage'


METRIC_NAMES = (('nti_site_user_count', 'users'),
                ('nti_site_site_admin_count', 'site_admins'),
                ('nti_site_instructor_count', 'instructors'),
                ('nti_site_editor_count', 'editors'),
                ('nti_site_site_admin_and_course_role_count', 'site_admin_and_course_roles'),
                ('nti_site_course_count', 'courses'),
                ('nti_site_child_course_count', 'child_courses'),
                ('nti_site_total_course_count', 'total_courses'))


# pendo
PENDO_ENDPOINT = "https://app.pendo.io/api/v1/metadata/account/custom/value"

PENDO_FIELD_NAMES = (('user_count', 'users'),
                     ('site_admin_count', 'site_admins'),
                     ('instructor_count', 'instructors'),
                     ('editor_count', 'editors'),
                     ('site_admin_and_course_role_count', 'site_admin_and_course_roles'),
                     ('course_count', 'courses'),
                     ('child_course_count', 'child_courses'),
                     ('total_course_count', 'total_courses'))


def fetch_sites_usage(base_url, username, password, sites=None):
    usage_url = urljoin(base_url, SITES_USAGE_ENDPOINT)
    params = {'sites': sites} if sites else {}
    resp = requests.get(usage_url,
                        params=params,
                        auth=HTTPBasicAuth(username, password))
    return resp


def push_to_prometheus(usage, push_gateway, job):
    from prometheus_client import CollectorRegistry, push_to_gateway, Gauge

    if not usage['Items']:
        return

    registry = CollectorRegistry()

    for metri_name, field_name in METRIC_NAMES:
        g = Gauge(metri_name,
                  'Last time a batch job successfully finished',
                  labelnames=['site'],
                  registry=registry)

        for item in usage['Items'] or ():
            site_name = item['site_name']
            metri_count = item['stats'][field_name]
            g.labels(site_name).set(metri_count)

    print("Start pushing usage to prometheus, gauges(metrics): %s, labels(sites) of each gauge: %s." \
          % (len(METRIC_NAMES),len(usage['Items'])))
    start = time.time()

    push_to_gateway(push_gateway, job=job, registry=registry)

    print("Finish pushing usage to prometheus, elapsed: %s seconds." % (time.time()-start))


def push_to_pendo(usage, pendo_integration_key):
    """
    Before pushing to pendo, making sure all custom fields created in pendo.
    https://developers.pendo.io/docs/?python#set-value-for-a-set-of-agent-or-custom-fields
    """
    if not usage['Items']:
        return

    data = []
    for item in usage['Items']:
        entry = { 'accountId': item['site_name'],
                  'values': {} }

        for metric_name, field_name in PENDO_FIELD_NAMES:
            entry['values'][metric_name] = item['stats'][field_name]

        data.append(entry)

    headers = {
        'x-pendo-integration-key': pendo_integration_key,
        'content-type': "application/json",
    }

    print("Start pushing usage to pendo, sites=%s." % len(usage['Items']))
    start = time.time()

    resp = requests.post(PENDO_ENDPOINT, json=data, headers=headers)
    if resp.status_code != 200:
        print("Failed to push usage to pendo, status code: %s, %s." % (resp.status_code, resp.text))
    else:
        result = resp.json()
        print("Successfully pushed usage to pendo, total=%s, updated=%s, failed=%s, elapsed: %s seconds." \
               % (result['total'], result['updated'], result['failed'], time.time() - start))

        if result['failed'] > 0:
            print("Existing failed: ")
            for kind in ('errors', 'missing'):
                msg = result.get(kind)
                if msg:
                    print(msg)


def main():
    parser = argparse.ArgumentParser(description=u'Push sites stats into prometheus gateway server.')

    parser.add_argument(u'--base-url',
                        type=str,
                        action=u'store',
                        dest=u'base_url',
                        help=u'The target url',
                        required=True)
    parser.add_argument(u'-u', u'--username',
                        dest=u'username',
                        type=str,
                        action=u'store',
                        help=u'The server username',
                        required=True)
    parser.add_argument(u'-p', u'--password',
                        dest=u'password',
                        type=str,
                        action=u'store',
                        help=u'The server password',
                        required=True)

    # Optional for the sites usage api.
    parser.add_argument(u'-s', u'--sites',
                        type=str,
                        action=u'store',
                        dest=u'sites',
                        required=False,
                        default=None,
                        help=u'If provided, it only push usages for these specified sites.')


    # Optional arguments for pushing data to a prometheus monitoring system
    parser.add_argument(u'-a', u'--addr',
                        type=str,
                        action=u'store',
                        dest=u'push_gateway',
                        required=False,
                        help=u'The host:port for a prometheus push gateway')
    parser.add_argument(u'-j', u'--job-name',
                        type=str,
                        action=u'store',
                        dest=u'job_name',
                        default=u'nti_site_usage_job',
                        required=False,
                        help=u'The push_gateway job name to use')

    # Optional arguments for pushing data to pendo
    parser.add_argument(u'-k', u'--pendo-integration-key',
                        type=str,
                        action=u'store',
                        dest=u'pendo_integration_key',
                        required=False,
                        help=u'The pendo integration key.')

    args = parser.parse_args()

    usage = fetch_sites_usage(args.base_url,
                              args.username,
                              args.password,
                              sites=args.sites).json()

    if args.push_gateway:
        push_to_prometheus(usage, args.push_gateway, args.job_name)

    if args.pendo_integration_key:
        push_to_pendo(usage, args.pendo_integration_key)

    return usage

if __name__ == '__main__':
    """
    usage:
        python src/nti/app/site/scripts/nti_sites_usage.py \
               --base-url http://alpha.dev:8081 \
               --username alex@nextthought.com \
               --password temp001 \
               --sites alpha.dev,demo.dev \
               --addr localhost:9091 \
               --pendo-integration-key
    """
    main()
