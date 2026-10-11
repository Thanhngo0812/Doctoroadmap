"""Chứng minh các assertion v4-16 bắt được hồi quy; chỉ đột biến trong process này."""
import argparse
import sys

import pytest

from tests.unit.presentation import test_v416_a1_cli as tests


def main():
    mode = sys.argv[1]
    if mode == 'selector':
        original = argparse.ArgumentParser.add_argument

        def mutated(self, *args, **kwargs):
            if args and args[0] == '--a1':
                kwargs['default'] = 'docling'
            return original(self, *args, **kwargs)

        argparse.ArgumentParser.add_argument = mutated
        tests.test_cli_default_light_and_explicit_docling(pytest.MonkeyPatch())
    elif mode == 'cache':
        original = tests.parse_config

        def mutated(parser, *args):
            config = original(parser, *args)
            if 'pipeline' in config:
                config['pipeline'] = {k: v for k, v in config['pipeline'].items() if k != 'models'}
            return config

        tests.parse_config = mutated
        tests.test_cache_separates_paths_models_and_versions_without_changing_legacy_key()
    else:
        raise ValueError(mode)
    raise RuntimeError('Đột biến lọt: assertion phải đỏ')


if __name__ == '__main__':
    main()
