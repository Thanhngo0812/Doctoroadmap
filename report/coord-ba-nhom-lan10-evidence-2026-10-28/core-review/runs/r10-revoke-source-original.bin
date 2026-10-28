from wayfinder.application.accounts import AuthError
from wayfinder.application.admin_ports import AdminStore
from wayfinder.application.auth_ports import AuditEvent
from wayfinder.domain.auth import Actor, decide


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
            if target.role == 'admin' and changes.get('role', target.role) == 'user' and self.store.admin_count() <= 1:
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

    @staticmethod
    def _page(limit, offset):
        if type(limit) is not int or not 1 <= limit <= 100:
            AdminService._invalid('limit')
        if type(offset) is not int or not 0 <= offset <= 100000:
            AdminService._invalid('offset')

    @staticmethod
    def _invalid(field):
        raise AuthError('validation', 'Dữ liệu yêu cầu không hợp lệ.', fields=[{'loc':field,'message':'Giá trị không hợp lệ.'}])
