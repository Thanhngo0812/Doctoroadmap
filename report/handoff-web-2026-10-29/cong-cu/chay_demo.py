"""Run `wayfinder.cli demo-local` non-interactively: the first-admin password comes from a local file."""
import getpass
import pathlib
import sys

password = pathlib.Path(sys.argv.pop(1)).read_text(encoding='utf-8').strip()
getpass.getpass = lambda prompt='': password
from wayfinder.cli import main
sys.exit(main())
