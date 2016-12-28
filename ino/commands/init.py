# -*- coding: utf-8; -*-

import os.path
import shutil

from configobj import ConfigObj

from ino.commands.base import Command
from ino.exc import Abort
from ino.utils import format_available_options, list_subdirs, copytree


class Init(Command):
    """
    Setup a new project in the current directory.

    The directory must be empty.
    """

    name = 'init'
    help_line = "Setup a new project in the current directory"

    default_template = 'empty'

    def setup_arg_parser(self, parser):
        super(Init, self).setup_arg_parser(parser)
        parser.add_argument('-t', '--template', default=self.default_template, 
                            help='Project template to use')

        parser.epilog = "Available project templates:\n\n"

        template_items = []
        for tdir in list_subdirs(self.e.templates_dir):
            try:
                description = ConfigObj(os.path.join(tdir, 'manifest.ini'))['description']
            except KeyError:
                description = ''
            template_items.append((os.path.basename(tdir), description))

        parser.epilog += format_available_options(template_items, head_width=12, 
                                                  default=self.default_template)

    def run(self, args):
        templates_dir = self.e.templates_dir
        template = args.template
        candidate = os.path.join(templates_dir, template)
        if not os.path.isdir(candidate):
            w = os.walk(self.e.templates_dir)
            found = False
            for dirname, dirs, _ in w:
                if template in dirs:
                    found = True
                    candidate = os.path.join(templates_dir, dirname, template)
                    break
            if not found:
                raise Abort("Template does not exist")
        try:
            copytree(candidate, '.', ignore=lambda *args: ['manifest.ini'])
        except shutil.Error as e:
            raise Abort(str(e))
