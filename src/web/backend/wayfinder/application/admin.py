from wayfinder.application.accounts import AuthError
from wayfinder.application.admin_ports import AdminStore
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.application.seed_samples import SAMPLE_DOCS
from wayfinder.domain.auth import Actor, decide

BUILD_STATUSES = {'awaiting_confirmation', 'queued', 'reading', 'running', 'rejected', 'succeeded', 'failed', 'cancelled'}
# Fixed texts keyed by the known codes: build.error_message is never read, so raw exceptions cannot reach the admin API.
BUILD_ERROR_MESSAGES = {
    'ban_quet': 'Tài liệu không đủ văn bản; hãy chọn bản có chữ',
    'chu_loi': 'Văn bản của tài liệu bị lỗi',
    'ngon_ngu_khong_ho_tro': 'Chỉ hỗ trợ tài liệu tiếng Việt',
    'loi_mang': 'Kết nối bị gián đoạn; bạn có thể thử lại',
    'het_tran_he_thong': 'Đã chạm trần dựng hôm nay',
    'loi_noi_bo': 'Không thể hoàn tất bản dựng',
    'confirmation_expired': 'Đã hết hạn xác nhận dựng',
}


class AdminService:
    def __init__(self, store: AdminStore, *, settings, clock):
        self.store, self.settings, self.clock = store, settings, clock

    def authorize(self, actor: Actor | None) -> None:
        decision = decide(actor, 'admin_users', None, None)
        if not decision.allowed:
            raise AuthError(decision.code, 'Không có quyền quản trị.')
        # A previously authenticated Actor must not keep privileges after demotion/disable.
        account = self.store.get_account(actor.user_id)
        if account is None or account.status != 'active' or account.role != 'admin':
            raise AuthError('forbidden', 'Không có quyền quản trị.')

    def list_users(self, actor, *, email='', role=None, status=None, limit=50, offset=0):
        self.authorize(actor)
        self._page(limit, offset)
        if not isinstance(email, str) or len(email) > 254 or role not in {None, 'user', 'admin'} or status not in {None, 'active', 'disabled'}:
            self._invalid('filters')
        return self.store.list_users(email=email.strip().lower(), role=role, status=status,
            limit=limit, offset=offset, now=self.clock.now(), default_max=self.settings.build_monthly_max)

    def update_user(self, actor, uid, changes, *, ip=None):
        self.authorize(actor)
        if not isinstance(changes, dict) or not changes or set(changes) - {'role','status','build_monthly_max'}:
            self._invalid('body')
        for field, value in changes.items():
            if field == 'role' and value not in {'user','admin'}:
                self._invalid(field)
            if field == 'status' and value not in {'active','disabled'}:
                self._invalid(field)
            if field == 'build_monthly_max' and value is not None and (type(value) is not int or not 1 <= value <= 2147483647):
                self._invalid(field)
        target = self.store.get_account(uid)
        if target is None:
            raise AuthError('not_found', 'Không tìm thấy tài khoản.')
        # Share account locks with login/reset; serialize all role transitions across runtimes.
        with self.store.atomic(['admin:users', f'account:{uid}', f'account:{target.email_normalized}']):
            self.authorize(actor)
            target = self.store.get_account(uid)
            if target is None:
                raise AuthError('not_found', 'Không tìm thấy tài khoản.')
            protected = self.store.first_admin_id()
            blocked = [field for field in ('status','role') if
                field in changes and (changes[field]=='disabled' if field=='status' else changes[field]!='admin')]
            if blocked and (protected is None or uid == protected):
                raise AuthError('bootstrap_required' if protected is None else 'protected_admin',
                    'Cần xác lập định danh admin đầu tiên.' if protected is None else 'Không thể khoá hoặc hạ quyền admin đầu tiên.',
                    fields=[{'loc':field,'message':'Tài khoản được bảo vệ bởi chính sách admin đầu tiên.'} for field in blocked])
            was_active_admin = target.role == 'admin' and target.status == 'active'
            will_be_active_admin = (changes.get('role', target.role) == 'admin'
                                    and changes.get('status', target.status) == 'active')
            if was_active_admin and not will_be_active_admin and self.store.admin_count() <= 1:
                raise AuthError('conflict', 'Không thể hạ quyền quản trị viên cuối cùng.')
            now = self.clock.now()
            actual = {key:value for key,value in changes.items() if getattr(target,key) != value}
            if actual:
                self.store.update_user(uid, actual, now)
                if actual.get('status') == 'disabled':
                    self.store.delete_account_sessions(uid)
                for field, value in actual.items():
                    action = ({'disabled':'admin_user_disabled','active':'admin_user_enabled'}[value]
                        if field == 'status' else 'admin_user_role_changed' if field == 'role' else 'admin_user_quota_changed')
                    self.store.append_audit(AuditEvent(now, actor.user_id, action, 'account', uid, ip))
            return self.store.user_summary(uid, now, self.settings.build_monthly_max)

    def list_audit(self, actor, *, actor_id=None, action=None, since=None, until=None, limit=50, offset=0):
        self.authorize(actor)
        self._page(limit, offset)
        for field,value in (('since',since),('until',until)):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                self._invalid(field)
        if since is not None and until is not None and since >= until:
            self._invalid('until')
        return self.store.list_audit(actor_id=actor_id,action=action,since=since,until=until,limit=limit,offset=offset)

    def list_builds(self, actor, *, q='', status=None, usage_complete=None, since=None, until=None, limit=50, offset=0):
        self.authorize(actor)
        self._page(limit, offset)
        if not isinstance(q, str) or len(q) > 254:
            self._invalid('q')
        if status not in {None, *BUILD_STATUSES}:
            self._invalid('status')
        if usage_complete not in {None, True, False}:
            self._invalid('usage_complete')
        for field, value in (('since', since), ('until', until)):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                self._invalid(field)
        if since is not None and until is not None and since >= until:
            self._invalid('until')
        page = self.store.list_builds(q=q.strip().lower(), status=status, usage_complete=usage_complete,
            since=since, until=until, limit=limit, offset=offset)
        page['items'] = [self._build_view(row) for row in page['items']]
        return page

    @staticmethod
    def _build_view(row):
        code = row['error_code']
        return {
            'build_id': row['id'], 'doc_id': row['doc_id'], 'status': row['status'], 'step': row['step'],
            'pipeline_version': row['pipeline_version'],
            'requested_by': {'user_id': row['requester_id'], 'email': row['requester_email']} if row['requester_id'] else None,
            'upload': ({'kind': row['upload_kind'], 'page_count': row['upload_pages'], 'size_bytes': row['upload_size']}
                if row['upload_kind'] else None),
            'course_count': row['course_count'], 'counts_quota': row['counts_quota'],
            'cancel_requested': row['cancel_requested'], 'claim_count': row['claim_count'],
            'created_at': row['created_at'], 'queued_at': row['queued_at'],
            'started_at': row['started_at'], 'finished_at': row['finished_at'],
            'error': ({'code': code if code in BUILD_ERROR_MESSAGES else 'khong_ro',
                       'message': BUILD_ERROR_MESSAGES.get(code, 'Mã lỗi không nhận diện được'),
                       'retryable': row['retryable']} if code else None),
            'usage': {'spent_usd': float(row['spent_usd']), 'model_calls': row['model_calls'],
                      'input_tokens': row['input_tokens'], 'output_tokens': row['output_tokens'],
                      'usage_complete': row['usage_complete'], 'elapsed_seconds': row['elapsed_seconds']},
            'graph_version': row['graph_version'], 'module_count': row['module_count'],
        }

    def set_sample_course(self, actor, cid, is_sample, *, ip=None):
        self.authorize(actor)
        if type(is_sample) is not bool:
            self._invalid('is_sample')
        if self.settings.env != 'dev':
            raise AuthError('conflict', 'Khoá mẫu chỉ dùng được ở môi trường dev.',
                fields=[{'loc': 'env', 'message': 'Môi trường hiện tại không phải dev.'}])
        # Serialize all sample flags: the one-sample-per-document rule is a check-then-write across rows.
        with self.store.atomic(['admin:samples']):
            self.authorize(actor)
            course = self.store.lock_course(cid)
            if course is None:
                raise AuthError('not_found', 'Không tìm thấy khoá học.')
            if course['doc_id'] not in SAMPLE_DOCS:
                raise AuthError('conflict', 'Chỉ khoá của sáu cuốn phát triển mới đánh dấu được là khoá mẫu.',
                    fields=[{'loc': 'doc_id', 'message': 'Tài liệu không thuộc danh sách khoá mẫu phát triển.'}])
            if is_sample and not course['is_sample'] and self.store.other_sample_exists(course['doc_id'], cid):
                raise AuthError('conflict', 'Tài liệu này đã có một khoá mẫu khác.',
                    fields=[{'loc': 'is_sample', 'message': 'Đã có khoá mẫu cho cùng tài liệu.'}])
            if course['is_sample'] != is_sample:
                now = self.clock.now()
                course = self.store.set_course_sample(cid, is_sample, now)
                self.store.append_audit(AuditEvent(now, actor.user_id,
                    'admin_course_sample_set' if is_sample else 'admin_course_sample_unset', 'course', cid, ip))
            return {'course_id': course['id'], 'doc_id': course['doc_id'], 'title': course['title'],
                'status': course['status'], 'is_sample': course['is_sample'],
                'published_graph_version': course['published_graph_version'],
                'module_count': course['module_count'], 'updated_at': course['updated_at']}

    @staticmethod
    def _page(limit, offset):
        if type(limit) is not int or not 1 <= limit <= 100:
            AdminService._invalid('limit')
        if type(offset) is not int or not 0 <= offset <= 100000:
            AdminService._invalid('offset')

    @staticmethod
    def _invalid(field):
        raise AuthError('validation', 'Dữ liệu yêu cầu không hợp lệ.', fields=[{'loc':field,'message':'Giá trị không hợp lệ.'}])
