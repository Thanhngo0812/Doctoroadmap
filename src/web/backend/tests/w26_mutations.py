"""Sequential W-26 mutations; each must fail an assertion (not a setup error) and the bytes are restored."""
import hashlib
import json
import os
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

from w14_mutations import PACKAGE, ROOT

TEST = 'src/web/backend/tests/test_demo_local_w26.py'
DEMO = 'demo_local.py'
CASES = [
    ('db-name', DEMO, "if not DATABASE_NAME.fullmatch(name):", 'if False:', 'not_dedicated'),
    ('db-name-prepare', DEMO, "if not DATABASE_NAME.fullmatch(url.database or ''):", 'if False:', 'refuses_the_shared_database'),
    ('db-local-only', DEMO, "if url.host not in {'127.0.0.1', 'localhost'}:", 'if False:', 'only_uses_a_local_postgres'),
    ('book-cap', DEMO, "DEMO_BOOK_MAX_USD = Decimal('3')", "DEMO_BOOK_MAX_USD = Decimal('300')", 'book_cap or defaults_are'),
    ('daily-remainder', DEMO, 'limit = min(self.book_max_usd, self.daily_max_usd - spent)', 'limit = self.book_max_usd',
     'daily_cap_leaves'),
    ('daily-claim-cap', DEMO, 'system_daily_build_max_usd=DEMO_DAILY_BUILD_MAX_USD,', 'system_daily_build_max_usd=None,',
     'full_day or defaults_are'),
    ('vietnam-day', 'infrastructure/build_store.py',
     "return now.astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).replace(hour=0,minute=0,second=0,microsecond=0)",
     "return now.astimezone(ZoneInfo('UTC')).replace(hour=0,minute=0,second=0,microsecond=0)", 'full_day'),
    ('waiting-reason', DEMO, 'if queued and store.cap_reached(now, maximum):', 'if False:', 'full_day'),
    ('receipt-doubled', 'infrastructure/build_store.py', "cost_usd=delta['spent_usd'],input_tokens", "cost_usd=delta['spent_usd']*2,input_tokens",
     'exactly_once or two_accounts'),
    ('trace-billed', 'infrastructure/phase_b_store.py', 'if value.get("counted_in") == "build":', 'if False:', 'exactly_once'),
    ('flag-off-spends', 'infrastructure/real_build.py', 'language, progress, cancelled, allow_spend=False)',
     'language, progress, cancelled, allow_spend=True)', 'without_the_demo_command'),
    ('shared-worker-grant', 'worker.py', 'return make_real_worker(settings,media=media,mailer=mailer)',
     "return make_real_worker(settings,media=media,mailer=mailer,spend_approval=__import__('wayfinder.demo_local',fromlist=['x']).DemoSpendPolicy())",
     'shared_worker_command or without_the_demo_command'),
    ('grant-per-build', DEMO, "reference = 'demo-' + uuid4().hex", "reference = 'demo-fixed'", 'two_accounts'),
    ('cloudinary-media', DEMO, 'return DiskMediaStore(root)',
     'return __import__("wayfinder.infrastructure.media", fromlist=["x"]).CloudinaryMediaStore()', 'demo_media_is_the_disk_store'),
    ('cloudinary-samples', DEMO, 'seeder = SampleSeeder(courses, gateway, media,',
     'seeder = SampleSeeder(courses, gateway, __import__("wayfinder.infrastructure.media", fromlist=["x"]).CloudinaryMediaStore(),',
     'six_sample'),
    ('learner-cap-config', DEMO, 'DEMO_LEARNER_DAILY_MAX_USD = 3.0', 'DEMO_LEARNER_DAILY_MAX_USD = 1.0', 'learner_cap or defaults_are'),
    ('learner-cap-wiring', 'composition.py', 'learner_daily_max_usd=settings.learner_daily_max_usd', 'learner_daily_max_usd=1.0',
     'learner_cap'),
    ('mailer-console', DEMO, "mailer='smtp'", "mailer='console'", 'demo_mailer_is_smtp'),
    ('worker-mailer', DEMO, 'mailer=compose_mailer(settings),', 'mailer=None,', 'finished_notice'),
    ('smtp-required', DEMO, 'if not all((base.smtp_username, base.smtp_password, base.smtp_from)):', 'if False:', 'needs_smtp'),
    ('separate-process', DEMO, 'child = subprocess.Popen(command)', 'child = None', 'separate_process'),
    ('worker-role', DEMO, "'demo-local', '--role', 'worker',", "'demo-local', '--role', 'all',", 'separate_process'),
    ('token-expiry', 'infrastructure/disk_media.py', ' or now.timestamp() >= int(expires)', '', 'signed_server_link'),
    ('token-signature', 'infrastructure/disk_media.py', 'if not valid or', 'if False or', 'signed_server_link'),
    ('route-first', DEMO, 'app.router.routes.insert(0,', 'app.router.routes.append(', 'signed_server_link'),
    ('disk-path-safety', 'infrastructure/disk_media.py', 'return safe_path(self.root, public_id)', 'return self.root / public_id',
     'outside_its_root'),
    ('base-url', DEMO, 'public_base_url=origin, ', '', 'follow_the_demo_port or reaches_the_smtp'),
    ('no-localhost-origin', DEMO, "([f'http://localhost:{port}'] if host == '127.0.0.1' else [])", '[]', 'both_loopback_names'),
    ('daily-boundary', DEMO, 'if limit <= 0:', 'if limit < 0:', 'exactly_the_cap'),
    ('page-render', 'infrastructure/disk_media.py', "bitmap = sheet.render(scale=width / sheet.get_width())",
     "bitmap = sheet.render(scale=1)", 'real_images'),
]


def main():
    batch = sys.argv[1] if len(sys.argv) > 1 else ''
    output = ROOT / 'report/w26-evidence/mutations' / batch
    output.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[2:])
    records = []
    run_id = uuid4().hex[:8]
    for label, relative, old, new, selection in CASES:
        if only and label not in only:
            continue
        path = PACKAGE / relative
        original = path.read_bytes()
        source = original.decode('utf-8')
        assert source.count(old) == 1, (label, 'mutation target must occur exactly once', source.count(old))
        xml = output / (label + '.xml')
        command = [sys.executable, str(ROOT / 'scripts/w05_run_tests.py'), TEST, '-k', selection, '-o', 'addopts=', '-q',
                   '--tb=short', '-p', 'no:warnings', '--basetemp=tmp/w26-mut-' + run_id + '-' + label, '--junitxml=' + str(xml)]
        try:
            path.write_bytes(source.replace(old, new).encode('utf-8'))
            process = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            (output / (label + '.log')).write_bytes((process.stdout + process.stderr).encode('utf-8'))
            tree = ET.parse(xml)
            failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
            names = sorted({case.get('name') for case in tree.findall('.//testcase') if case.find('failure') is not None})
            assertions = sum(any(word in (f.text or '') for word in ('AssertionError', 'assert ', 'DID NOT RAISE', 'Failed:'))
                             for f in failures)
            record = {'label': label, 'exit_code': process.returncode, 'failures': len(failures), 'caught_by': names,
                      'assertion_failures': assertions, 'setup_errors': len(errors),
                      'original_sha256': hashlib.sha256(original).hexdigest()}
            assert process.returncode == 1 and assertions and not errors, record
        finally:
            path.write_bytes(original)
            assert path.read_bytes() == original
        record['source_restored'] = True
        records.append(record)
        (output / 'mutations.json').write_bytes((json.dumps(records, indent=2) + '\n').encode())
        print(label + ': caught by ' + ', '.join(names), flush=True)


if __name__ == '__main__':
    main()
