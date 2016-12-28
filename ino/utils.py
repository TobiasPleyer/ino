# -*- coding: utf-8; -*-

import shutil
import os.path
import itertools


try:
    from collections import OrderedDict
except ImportError:
    # Python < 2.7
    from ordereddict import OrderedDict


class SpaceList(list):
    def __add__(self, other):
        return SpaceList(super(SpaceList, self).__add__(other))

    def __str__(self):
        return ' '.join(map(str, self))

    def paths(self):
        return SpaceList(getattr(x, 'path', x) for x in self)


class FileMap(OrderedDict):
    def sources(self):
        return SpaceList(self.iterkeys())

    def targets(self):
        return SpaceList(self.itervalues())

    def iterpaths(self):
        for source, target in self.iteritems():
            yield (source.path, target.path)

    def target_paths(self):
        return SpaceList(x.path for x in self.targets())


def list_subdirs(dirname, recursive=False, exclude=[]):
    entries = [e for e in os.listdir(dirname) if e not in exclude and not e.startswith('.')]
    paths = [os.path.join(dirname, e) for e in entries]
    dirs = filter(os.path.isdir, paths)
    if recursive:
        sub = itertools.chain.from_iterable(
            list_subdirs(d, recursive=True, exclude=exclude) for d in dirs)
        dirs.extend(sub)
    return dirs


def format_available_options(items, head_width, head_color='cyan', 
                             default=None, default_mark="[DEFAULT]", 
                             default_mark_color='red'):
    from ino.filters import colorize
    default_mark = colorize(default_mark + ' ', default_mark_color)
    lines = ['%s: %s%s' % (colorize('%%%ds' % head_width % key, head_color), 
                           default_mark if key == default else '', 
                           val) 
             for key, val in items]
    return '\n'.join(lines)


def copytree(src, dst, symlinks=False, ignore=None):
    """
    Tweaked version of shutil.copy tree that allows to copy
    to current directory
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if dst == '.':
        if os.listdir(dst):
            raise shutil.Error('Current directory is not empty')
    else:
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error, err:
            errors.extend(err.args[0])
    if errors:
        raise shutil.Error(errors)
