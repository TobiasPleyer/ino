# -*- coding: utf-8; -*-

import os
import os.path
import shutil

from configobj import ConfigObj

from ino.commands.base import Command
from ino.exc import Abort
from ino.filters import colorize
from ino.utils import format_available_options, list_subdirs, copytree


class Template(Command):
    """
    Manage templates in the builtin template directory
    """

    name = 'template'
    help_line = "Manage templates in the builtin template (aka examples) directory"

    def setup_arg_parser(self, parser):
        super(Template, self).setup_arg_parser(parser)
        parser.add_argument('-u', '--update', action='store_true',
                            help='Fetch all examples from the associated arduino installation and copy them to the template directory')
        parser.add_argument('-r', '--remove', nargs='+',
                            help='Remove all specified templates below the provided directory level')
        parser.add_argument('-a', '--add', nargs='+',
                            help='Add the provided directory to the templates directory. Every provided directory is expected to have a src/ subdirectory containing .ino files')
        parser.add_argument('-l', '--list', action='store_true',
                            help='List all available templates. This option will deactivate all other options provided with the same command.')
        parser.add_argument('-p', '--prefix', nargs=1,
                            help='Used only in conjunction with the --add option. Specifies the path where to save the template within the templates directory (hierarchy).')

    def run(self, args):
        templates_dir = self.e.templates_dir
        if args.list:
            def is_ino(filename):
                return filename.endswith('.ino')
            def strip_path(path):
                path = path.replace(templates_dir,'')
                if path.endswith('/src'):
                    path = path.replace('/src','')
                if path.startswith('/'):
                    path = path[1:]
                return path
            w = os.walk(templates_dir)
            ts = [dirname for dirname,_,fs in w if any(map(is_ino, fs))]
            # Sort the array inplace
            ts.sort()
            ts = map(strip_path, ts)
            curr_head = ""
            curr_indent = 0
            for template in ts:
                head,tail = os.path.split(template)
                if tail:
                    if not head:
                        print colorize(tail, 'yellow')
                    elif head == curr_head:
                        print '\t'*curr_indent + colorize(tail, 'yellow')
                    else:
                        curr_head = head
                        curr_indent = 0
                        for level in head.split('/'):
                            print '\t'*curr_indent + colorize(level, 'yellow')
                            curr_indent += 1
                        print '\t'*curr_indent + colorize(tail, 'yellow')
        else:
            # It makes no sense to allow the list option with any of the other options, because it is not
            # clear which state to print out: before or after the other commands
            if args.update:
                try:
                    self.e.find_arduino_dir('arduino_examples_dir', ['examples'],
                                            human_name='Arduino standard examples')
                except Abort:
                    # None of the available directories has an 'examples' subdirectory -> let the user know about it
                    print colorize("Unable to locate examples subdirectory in any of the search directories", 'red')
                else:
                    # We found an 'examples' subdirectory
                    arduino_examples = os.walk(self.e.arduino_examples_dir)
                    # The following statement is a neat little trick to descent the directory structure until we actually
                    # reach the .ino sketches. The variable 'directory' will be the full path relative to the top level
                    # examples directory and files will be the sketches. From there on we just have to copy the files into
                    # the template dir, preserving the example 'categories' (e.g. 01.Basics/Blink)
                    copy_candidates = [(directory, files) for (directory,_,files) in arduino_examples if files]
                    for src_dir, files in copy_candidates:
                        # Reroot the subsrc_dir to our templates src_dir
                        dst_dir = src_dir.replace(self.e.arduino_examples_dir, templates_dir)
                        # Check if this template already exists, if so skip copy
                        if os.path.isdir(dst_dir):
                            print colorize("Template destination already exists. Nothing will be done.", 'yellow')
                        else:
                            dst_dir_lib = os.path.join(dst_dir, 'lib')
                            dst_dir_src = os.path.join(dst_dir, 'src')
                            # Create empty lib folder as arduino examples don't have external libraries
                            os.makedirs(dst_dir_lib)
                            print colorize("Copying %s to %s"%(src_dir, dst_dir_src), 'green')
                            copytree(src_dir, dst_dir_src)
            if args.remove:
                for src_dir in args.remove:
                    try:
                        shutil.rmtree(os.path.join(templates_dir, src_dir))
                    except OSError:
                        w = os.walk(templates_dir)
                        found = False
                        for dirname, dirs, _ in w:
                            if src_dir in dirs:
                                found = True
                                shutil.rmtree(os.path.join(templates_dir, dirname, src_dir))
                                break
                        if not found:
                            print colorize("Template does not exist", 'red')
            if args.add:
                for src_dir in args.add:
                    content = os.listdir(src_dir)
                    if not 'src' in content:
                        print colorize("Provided directory %s does not contain a src/ subdirectory!"%src_dir, 'red')
                    else:
                        name = src_dir.split('/')[-1]
                        if args.prefix:
                            prefix = args.prefix[0]
                            dst_dir = os.path.join(templates_dir, prefix)
                        else:
                            dst_dir = os.path.join(templates_dir, name)
                        print colorize("Copying %s to %s"%(src_dir, dst_dir), 'green')
                        try:
                            copytree(src_dir, dst_dir)
                        except OSError:
                            print colorize("Template already exists!", 'red')
