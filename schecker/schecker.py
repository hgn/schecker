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

from dataclasses import dataclass
from typing import Iterator
from typing import List
from typing import Dict
from typing import Optional

class CoccinCheckError(Exception): pass
class InitializationCocci(CoccinCheckError): pass

COCCIN_SUFFIX = ['.c', '.cpp', '.cc']

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

INFO_PATH = 'checker-warnings'

class ModClangTidy:

    def __init__(self):
        self._check_environment()

    def _check_environment(self):
        if not shutil.which('clang-tidy'):
            raise CoccinCheckError('clang-tidy not installed or callable, please install clang-tidy')

    def execute(self, relpath, fullpath):
        cmd =  'clang-tidy {} {}'.format(TIDY_CHECKS, fullpath)
        stdout = execute(cmd)
        if len(stdout) >= 0:
            return "# {}\n{}".format(cmd, stdout)
        return ''

class ModCoccinelle:

    def __init__(self, coccinelle_script_dirs: List[str] = list()):
        self._coccinelle_script_dirs = coccinelle_script_dirs
        self._load_scripts()
        self._check_environment()

    def _load_scripts(self):
        self._scripts = list()
        for rootdir in self._coccinelle_script_dirs:
            for path, dirs, files in os.walk(rootdir):
                for file_ in files:
                    full_path = os.path.join(path, file_)
                    if not full_path.endswith('.cocci'):
                        continue
                    full_path = os.path.normpath(os.path.abspath(full_path))
                    self._scripts.append(full_path)


    def _check_environment(self):
        if not shutil.which('spatch'):
            raise CoccinCheckError('spatch not installed or callable, please install clang-tidy')

    def execute(self, relpath, fullpath):
        buf = ''
        for scriptpath in self._scripts:
            cmd =  'spatch -sp_file {} {}'.format(scriptpath, fullpath)
            stdout = execute(cmd)
            if len(stdout) >= 0:
                buf += "# {}\n{}".format(cmd, stdout)
        return buf


class Schecker:

    def __init__(self, directories: List[str], coccinelle_script_dirs: List[str] = list(),
                 modules_disabled: List[str] = list()) -> None:
        self._directories = directories
        self._coccinelle_script_dirs = coccinelle_script_dirs
        self._modules_disabled = modules_disabled
        self._init_modules()
        self._init_directories()

    def _init_modules(self):
        self._modules = list()
        if 'coccinelle' not in self._modules_disabled:
            self._modules.append(ModCoccinelle(self._coccinelle_script_dirs))
        if 'clang-tidy' not in self._modules_disabled:
            self._modules.append(ModClangTidy())

    def _init_directories(self):
        if not self._directories:
            raise CoccinCheckError('argument for analyzed directories is empty')
        if os.path.exists(INFO_PATH):
            shutil.rmtree(INFO_PATH)

    def account_warning(self, relpath, message):
        path = os.path.join(INFO_PATH, relpath)
        dirpath = os.path.dirname(path)
        os.makedirs(dirpath, exist_ok=True)
        with open(path, 'a') as fd:
            fd.write(message)

    def check(self):
        buf = io.StringIO()
        for relpath, fullpath in self._each_file():
            for module in self._modules:
                stdout = module.execute(relpath, fullpath)
                if len(stdout) <= 0:
                    continue
                buf.write(stdout)
                self.account_warning(relpath, stdout)
        return buf.getvalue()

    def _is_blacklisted(self, path):
        return False

    def _each_file(self):
        for rootdir in self._directories:
            rootdir = os.path.normpath(os.path.abspath(rootdir))
            for path, dirs, files in os.walk(rootdir):
                for file_ in files:
                    full_path = os.path.join(path, file_)
                    if self._is_blacklisted(full_path):
                        continue
                    file_suffix = os.path.splitext(file_)[1]
                    if file_suffix not in COCCIN_SUFFIX:
                        continue
                    rel_path = full_path[len(rootdir) + 1:]
                    yield rel_path, full_path




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
    path = ['../botan/src/']
    path = ['.']
    scripts = ['schecker/tests/cocci-scripts/']
    Schecker(path, scripts).check()
