import yaml
from collections import OrderedDict

import os
from os.path import join as pjoin
import requests
import json
from glob import glob
import shutil

from jinja2 import Template


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """
    From http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load_all(stream, OrderedLoader)


def mk_cache(path='__cache__'):
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def get_user_info():
    cache = mk_cache()

    info = {}
    json_files = glob(pjoin(cache, '*.json'))
    for jf in json_files:
        user_data = json.load(open(jf))
        info[user_data['login']] = user_data

    return info


def update_users(team):
    cache = mk_cache()
    user_info = get_user_info()
    users = user_info.keys()

    for user in team.difference(users):
        print("Requesting user '{}' from GitHub...".format(user))

        r = requests.get('https://api.github.com/users/{}'.format(user))
        json_info = r.text
        user_id = json.loads(json_info)['id']

        r = requests.get('https://avatars3.githubusercontent.com/u/{}?v=3&s=40'.format(user_id))
        jpeg = r.content

        with open(pjoin(cache, '{}.json'.format(user)), 'w') as f:
            f.write(json_info)

        with open(pjoin(cache, '{}.jpeg'.format(user)), 'wb') as f:
            f.write(jpeg)


def copy_files(pattern, src, dst):
    cache = mk_cache()

    for full_path in glob(pjoin(src, pattern)):
        fn = os.path.basename(full_path)
        print("Copying '{}' to '{}'".format(fn, dst))
        shutil.copy(full_path, pjoin(dst, fn))


def render_site(projects):
    path = 'output'

    if os.path.exists(path):
        shutil.rmtree(path)

    out = mk_cache(path)
    cache = mk_cache()

    copy_files('*.jpeg', src=cache, dst=out)
    copy_files('*.css', src='templates', dst=out)

    print()

    for in_file in glob(pjoin('templates', '*.html')):
        print('Rendering {}...'.format(in_file))
        template = Template(open(in_file).read())
        with open(pjoin(out, os.path.basename(in_file)), 'w') as f:
            f.write(template.render(projects=projects))


if __name__ == "__main__":
    status = next(ordered_load(open('status.yaml'), yaml.SafeLoader))
    projects = status['projects'].items()

    team = set()
    for project, info in projects:
        team.update(info.get('members', ()))

    update_users(team)
    render_site(projects)
