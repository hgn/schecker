#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import io
import re
import sys
import glob
import types
import subprocess
import tempfile
import datetime
import shutil

from typing import Iterator
from typing import List
from typing import Dict
from typing import Optional

class ScheckerError(Exception): pass

# Default file extension, can be replaced by extension()
FILE_EXTENSION = ['.c', '.C', '.cpp', '.cxx', '.cc', '.c++' ]

TIDY_CHECKS  = '-checks=-\*'
TIDY_CHECKS += ',clang-analyzer-\*'
TIDY_CHECKS += ',clang-analyzer-cplusplus\*'
TIDY_CHECKS += ',bugprone-\*'
TIDY_CHECKS += ',cert-\*'
TIDY_CHECKS += ',cppcoreguidelines-\*'
TIDY_CHECKS += ',google-\*'
TIDY_CHECKS += ',llvm-\*'
TIDY_CHECKS += ',misc-\*'
TIDY_CHECKS += ',performance-\*'
TIDY_CHECKS += ',readability-\*'
TIDY_CHECKS += ',-clang-diagnostic-error'

DEFAULT_OUTPUT_DIR = 'schecker-results'


class Info:

    def __init__(self, filepath_rel, filepath_abs):
        self._filepath_rel = filepath_rel
        self._filepath_abs = filepath_abs

    @property
    def filepath_rel(self) -> str:
        return self._filepath_rel

    @property
    def filepath_abs(self) -> str:
        return self._filepath_abs


class ModClangTidy:

    def __init__(self):
        self._check_environment()

    def _check_environment(self):
        if not shutil.which('clang-tidy'):
            raise ScheckerError('clang-tidy not installed or callable, please install clang-tidy')

    def execute(self, relpath, fullpath):
        cmd =  'clang-tidy {} {}'.format(TIDY_CHECKS, fullpath)
        stdout = execute(cmd)
        if len(stdout) >= 0:
            return "# {}\n{}".format(cmd, stdout)
        return ''


class ModCoccinelle:

    def __init__(self):
        self._check_environment()
        self._scripts = list()

    def script_dirs(self, script_dirs: List[str]):
        self._script_dirs = script_dirs
        self._load_scripts()

    def _load_scripts(self):
        self._scripts = list()
        for rootdir in self._script_dirs:
            for path, dirs, files in os.walk(rootdir):
                for file_ in files:
                    full_path = os.path.join(path, file_)
                    if not full_path.endswith('.cocci'):
                        continue
                    full_path = os.path.normpath(os.path.abspath(full_path))
                    self._scripts.append(full_path)

    def _check_environment(self):
        if not shutil.which('spatch'):
            raise ScheckerError('spatch not installed or callable, please install clang-tidy')

    def execute(self, relpath, fullpath):
        buf = ''
        for scriptpath in self._scripts:
            cmd =  'spatch -sp_file {} {}'.format(scriptpath, fullpath)
            stdout = execute(cmd)
            if len(stdout) >= 0:
                buf += "# {}\n{}".format(cmd, stdout)
        return buf


class Schecker:

    def __init__(self, directories: List[str], excludes: List[str] = list(),
                 outdir: str = DEFAULT_OUTPUT_DIR,
                 modules_disabled: List[str] = list()) -> None:
        self._directories = directories
        self._excludes = excludes
        self._outdir = outdir
        self._modules_disabled = modules_disabled
        self._init_system()

    def options_coccinelle(self, script_dirs: List[str] = list()):
        self._options_coccinelle_script_dirs = script_dirs
        self._modules['coccinelle'].module.script_dirs(self._options_coccinelle_script_dirs)


    def _init_system(self):
        self._init_modules()
        self._init_default_extensions()
        self._init_directories()

    def _init_default_extensions(self):
        self._extensions = FILE_EXTENSION

    def _init_modules(self):
        self._modules = dict()
        if 'coccinelle' not in self._modules_disabled:
            self._modules['coccinelle'] = types.SimpleNamespace()
            self._modules['coccinelle'].module = ModCoccinelle()
        if 'clang-tidy' not in self._modules_disabled:
            self._modules['clang-tidy'] = types.SimpleNamespace()
            self._modules['clang-tidy'].module = ModClangTidy()

    def _init_directories(self):
        if not self._directories:
            raise ScheckerError('argument for analyzed directories is empty')
        if self._outdir and os.path.exists(self._outdir):
            shutil.rmtree(self._outdir)

    def _account_warning(self, relpath, message):
        if not self._outdir:
            return
        path = os.path.join(self._outdir, relpath)
        dirpath = os.path.dirname(path)
        os.makedirs(dirpath, exist_ok=True)
        with open(path, 'a') as fd:
            fd.write(message)

    def _is_excluded(self, path):
        for exclude in self._excludes:
            if exclude in path:
                return True
        return False

    def _each_file(self):
        for rootdir in self._directories:
            rootdir = os.path.normpath(os.path.abspath(rootdir))
            for path, dirs, files in os.walk(rootdir):
                for file_ in files:
                    # if file is within exclude list, if so: skip
                    full_path = os.path.join(path, file_)
                    if self._is_excluded(full_path):
                        continue
                    # if file a valid file (ends of .c, .cpp)?
                    file_suffix = os.path.splitext(file_)[1]
                    if file_suffix not in self._extensions:
                        continue
                    # valid! return this path (and rel path)
                    rel_path = full_path[len(rootdir) + 1:]
                    yield rel_path, full_path

    @property
    def extensions(self) -> List[str]:
        return self._extensions

    @extensions.setter
    def extensions(self, value : List[str]) -> None:
        self._extensions = value

    def check(self, io_object):
        for relpath, fullpath in self._each_file():
            info = Info(relpath, fullpath)
            for module_name, module in self._modules.items():
                stdout = module.module.execute(relpath, fullpath)
                if len(stdout) <= 0:
                    continue
                io_object.write(stdout)
                self._account_warning(relpath, stdout)
            yield info

    def check_all(self, io_object):
        list(self.check(io_object))




def execute(command: str, shell: bool = True, cwd: Optional[str] = None,
            env: Optional[Dict[str, str]] = None):
    if not shell:
        # raw syscall, required command array
        command = command.split()
    stderr_fd = sys.stderr
    stdout_fd = sys.stdout
    completed = subprocess.run(command, cwd=cwd, env=env, shell=shell,
                               capture_output=True, universal_newlines=True)
    return completed.stdout



if __name__ == "__main__":
    buf = io.StringIO()
    paths = ['.', '../botan/src/']
    excludes = ['fuzzer', 'tests/test']
    scripts = ['schecker/tests/cocci-scripts/']

    schecker = Schecker(paths, excludes=excludes)
    schecker.options_coccinelle(script_dirs=scripts)

    for file_info in schecker.check(buf):
        print('check {}'.format(file_info.filepath_abs))

    print(buf.getvalue())
