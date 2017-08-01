#!/usr/bin/env python3

import docker
import datetime
import argparse
import sys

# Some helper functions
def pretty_print_image(img):
    now = datetime.datetime.now()
    created = sec_to_datetime(img.attrs['Created'])
    days = timediff_days(created, now)
    tag = img.tags[0] if len(img.tags) > 0 else 'UNTAGGED'
    return "%s %6s days (%s) %s" % (img.id[:20], days, created, tag)

def unixtime_to_text(sec):
    return datetime.datetime.fromtimestamp(
        int(sec)).strftime('%Y-%m-%d %H:%M:%S')

def sec_to_datetime(sec):
    return datetime.datetime.fromtimestamp(
        int(sec))

def timediff_days(begin, end):
    return (end - begin).days

def confirm(msg):
    while True:
        ans = input(msg)
        if ans == 'y':
            return True
        if ans == 'n':
            return False

def group_by_repo(imgs):

    repos = {}
    for img in imgs:
        for repotag in img.tags:
            idx = repotag.rfind(':')
            repo = repotag[:idx] if idx != -1 else repotag

            try:
                repoimgs = repos[repo]
                if img not in repoimgs:
                    repoimgs.append(img)
            except KeyError:
                repos[repo] = [img]

    return repos

def get_older_than_n(imgs,n):
    """Returns images from the list that are older than the newest n images"""
    if len(imgs) <= n:
        return []
    else:
        imgs.sort(key=lambda img: img.attrs['Created'], reverse=True)
        return imgs[n:]

def parse_arguments():
    parser = argparse.ArgumentParser(description='A small utility to cleanup old images on Docker hosts')
    parser.add_argument('--yes', dest='yes', action='store_true', help='Assume yes, do not ask for confirmation')
    parser.add_argument('--keep', dest='keep', default=2, metavar='N', help='Keep the latest N images for each repository')
    return parser.parse_args()

if __name__=='__main__':
    args = parse_arguments()

    client = docker.from_env()

    allimgs = client.images.list()

    # We consider images without any tags to be deletable
    delete = []
    delete.extend(filter(lambda img: len(img.tags)==0, allimgs))

    # Deletable images are everything but the latest n from each repository
    repoimgs = group_by_repo(allimgs)

    for repo, imgs in repoimgs.items():
        delete.extend(get_older_than_n(imgs,int(args.keep)))

    if len(delete) == 0:
        print("Nothing to delete: no repository contains more than %d images" % int(args.keep))
        sys.exit(0)

    if not args.yes:
        for img in delete:
            print(pretty_print_image(img))

        if not confirm("Delete these %d images? (y/n)" % len(delete)):
            print('Cancelled by user')
            sys.exit(1)

    # Carry out the actual deletion
    for i,img in enumerate(delete):
        print('Deleting %d/%d: %s ... ' % (i+1, len(delete), pretty_print_image(img)), end='')
        try:
            client.images.remove(img.id, force=True)
        except docker.errors.APIError as e:
            if e.explanation.find('image is being used by running container') != -1:
                print('Uname to delete: being used by running container!')
                continue
            else:
                raise e
        print('OK')
