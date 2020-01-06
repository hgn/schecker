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

COCCIN_SUFFIX = ['.c', '.cpp']

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
TIDY_CHECKS += ',-google-readability-namespace-comments'
TIDY_CHECKS += ',-clang-diagnostic-error'
TIDY_CHECKS += ',-misc-unused-parameters'
TIDY_CHECKS += ',-llvm-namespace-comment'
TIDY_CHECKS += ',-google-runtime-references'
TIDY_CHECKS += ',-clang-diagnostic-error'

INFO_PATH = 'checker-warnings'

class Coccincheck:

    def __init__(self, directories: List[str]) -> None:
        self._directories = directories
        self._check_environment()
        self._init_directories()

    def _check_environment(self):
        if not shutil.which('clang-tidy'):
            raise CoccinCheckError('clang-tidy not installed or callable, please install clang-tidy')

    def _init_directories(self):
        if not self._directories:
            raise CoccinCheckError('argument for analyzed directories is empty')
        for directory in self._directories:
            if not directory.startswith('/'):
                raise CoccinCheckError('directory argument must be full path')
        if os.path.exists(INFO_PATH):
            shutil.rmtree(INFO_PATH)

    def account_warning(self, rel_path, message):
        path = os.path.join(INFO_PATH, rel_path)
        dirpath = os.path.dirname(path)
        os.makedirs(dirpath, exist_ok=True)
        with open(path, 'w') as fd:
            fd.write(message)

    def check(self):
        buf = io.StringIO()
        for relpath, fullpath in self._each_file():
            cmd =  'clang-tidy {} {}'.format(TIDY_CHECKS, fullpath)
            space = ' ' * 128
            sys.stderr.write('\rprocessing {}{}'.format(relpath, space))
            stdout = execute(cmd)
            if len(stdout) <= 0:
                continue
            buf.write(stdout)
            self.account_warning(relpath, stdout)
        sys.stderr.write('\r')
        print(buf.getvalue())
        print('please take a look at {} for file specific warnings'.format(INFO_PATH))

    def _is_blacklisted(self, path):
        return False

    def _each_file(self):
        for rootdir in self._directories:
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
    #Coccincheck([os.path.abspath('.')]).check()
    Coccincheck([os.path.abspath('../botan/src/')]).check()
