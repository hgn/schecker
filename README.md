# Schecker

A Security/Safety Checker for C/C++ based on Clang-Tidy and Coccinelle.

## Usage

```
pip install schecker
```

```
#!/usr/bin/python

import sys
import schecker

paths = [ './path/to/your/c/project' ]
excludes = [ './path/to/your/c/project/third-party' ]
scripts = ['schecker/tests/cocci-scripts/']

schecker = schecker.Schecker(paths, excludes=excludes)
schecker.options_coccinelle(script_dirs=scripts)

# now start the actual test, this may take some time
schecker.check_all(sys.stderr)
```


# Dependencies

Schecker depends on clang-tidy and coccinelle, though it is possible to disable
the modules seperatly. E.g. you don't need coccinelle: `Schecker(...,
modules_disabled=['coccinelle'])`

```
sudo aptitude install clang-tidy coccinelle
```

# Documentation

## Coccinelle

### Getting Comfy with Coccinelle

- https://lwn.net/Articles/315686/
- https://lwn.net/Articles/380835/
- https://events.static.linuxfound.org/sites/events/files/slides/Introduction%20to%20Coccinelle.pdf

### Defect Spotting with Coccinelle

- https://web.imt-atlantique.fr/x-info/coccinelle/stuart_thesis.pdf
