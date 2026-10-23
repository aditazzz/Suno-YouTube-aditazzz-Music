"""Builds the fake pull-request diff that scrolls through the video."""
import random

PY = [
    "def get_session(user_id, token=None):", "    return cache.get(key) or db.fetch(key)", "    if not token:",
    "        raise AuthError('nope')", "    logger.info('refreshing token for %s', user_id)",
    "    for attempt in range(retries):", "        try:", "            resp = client.post(url, json=payload)",
    "        except Exception:", "            pass", "    return response.json()", "    self.client = Client(timeout=30)",
    "    payload = {'id': user_id, 'scope': scope}", "@retry(times=3)", "class SessionManager(BaseManager):",
    "    config = load_config(env)", "    if settings.DEBUG:", "    result = await fetch_all(ids)",
    "    data = json.loads(raw)", "    return None", "    elif mode == 'legacy':", "    # handle edge case",
    "    limit = int(os.environ.get('LIMIT', 100))", "    items = [normalize(i) for i in items]",
    "    assert user is not None", "    with transaction.atomic():", "        queue.publish(event)",
    "    metrics.incr('auth.login')", "    token = jwt.encode(claims, SECRET)", "    return wrapper",
    "def _helper2(x, y, z=None):", "    tmp = tmp2 or tmp3", "    time.sleep(1)", "        yield chunk",
    "    del cache[key]", "from utils import *", "import os, sys, re, json", "    if data is None: data = {}",
    "    self.retries = kwargs.get('retries', 3)", "    return [x for x in xs if x]", "def handle(event, context):",
    "    rows = db.execute(query, params).fetchall()", "    headers['Authorization'] = f'Bearer {token}'",
    "    total = sum(i.amount for i in invoice.items)", "    raise NotImplementedError", "    log.warning('should not happen')",
    "    return Response(status=200)", "    cursor.close()", "    user.save(update_fields=['last_seen'])",
    "    if retries > MAX_RETRIES: break", "    cfg.update(overrides or {})", "    return self._cache[key]",
]
SQL = [
    "ALTER TABLE accounts ADD COLUMN flag2 BOOLEAN;", "CREATE INDEX idx_tmp ON events (created_at);",
    "SELECT id, email FROM users WHERE id = $1;", "COMMIT;", "BEGIN;", "ALTER TABLE orders DROP CONSTRAINT fk_user;",
    "UPDATE settings SET value = 'true' WHERE key = 'new_flow';", "CREATE TABLE tmp_users_2 AS SELECT * FROM users;",
    "INSERT INTO audit_log (actor, action) VALUES ('system', 'cleanup');", "ALTER TABLE sessions ALTER COLUMN ttl SET DEFAULT 0;",
    "DELETE FROM sessions WHERE expires_at < now();", "GRANT ALL ON ALL TABLES IN SCHEMA public TO app;",
    "-- backfill", "ANALYZE;", "ALTER TABLE invoices RENAME COLUMN total TO total_old;",
]
YML = [
    "replicas: 3", "image: registry/app:latest", "timeout: 30s", "- name: LOG_LEVEL", "  value: debug", "resources:",
    "  limits:", "    memory: 512Mi", "enabled: true", "retries: 5", "strategy: Recreate", "  cpu: 250m",
    "- name: FEATURE_NEW_AUTH", "  value: \"true\"", "livenessProbe:", "  initialDelaySeconds: 0", "env: production",
    "autoscaling:", "  minReplicas: 1", "  maxReplicas: 1", "schedule: \"*/1 * * * *\"", "allow_failure: true",
]
TS = [
    "export const handler = async (req, res) => {", "  const { data } = await api.get(url);",
    "  if (!user) return res.status(401).end();", "  setState(prev => ({ ...prev, loading: false }));",
    "  // eslint-disable-next-line", "  return <Button onClick={submit}>Save</Button>;",
    "type Props = { id: string; onDone?: () => void };", "  console.log('here');", "  const total = items.reduce((a, b) => a + b.price, 0);",
    "  useEffect(() => { load(); }, []);", "};", "  const token = localStorage.getItem('token') as any;",
    "  if (err) throw err;", "export default Checkout;", "  await sleep(500);", "  return data as unknown as User;",
    "import { thing } from '../../../../utils';", "  const [open, setOpen] = useState(false);", "  // @ts-ignore",
]
POOLS = {"py": PY, "sql": SQL, "yml": YML, "ts": TS}
FILES = [
    ("services/api/handlers.py", "py"), ("web/src/Checkout.tsx", "ts"), ("deploy/prod.yaml", "yml"),
    ("billing/invoice.py", "py"), ("db/migrations/0109_more_flags.sql", "sql"), ("core/retry.py", "py"),
    ("web/src/hooks/useAuth.ts", "ts"), ("infra/k8s/cronjob.yaml", "yml"), ("services/payments/client.py", "py"),
    ("core/cache.py", "py"), ("web/src/pages/Admin.tsx", "ts"), ("db/migrations/0110_tmp_tables.sql", "sql"),
    ("services/notify/email.py", "py"), (".github/workflows/ci.yaml", "yml"), ("core/models/user.py", "py"),
    ("web/src/api/client.ts", "ts"), ("scripts/backfill.py", "py"), ("services/search/index.py", "py"),
]
# pause-bait: (kind, text). Sprinkled through the filler.
GAGS = [
    ("add", "DEPLOY_ON_FRIDAY = True"), ("add", "    except Exception: pass  # it's fine"),
    ("add", "    time.sleep(11)  # fixes the race condition"), ("add", "    # I am so sorry"),
    ("add", "    # reviewer: blink twice if you can read this"), ("add", "API_KEY = \"sk-live-do-not-commit\""),
    ("add", "    # written at 11:11pm, tested never"), ("add", "    git push --force  # it's Thursday"),
    ("add", "    cost_per_request = 0.0  # finance will not check"), ("add", "    // TODO: ask someone who understands this"),
    ("del", "    validate(input)"), ("add", "    # validate(input)  # was slow"),
    ("add", "    @skip('flaky')  # all of them"), ("add", "    retries = 1111"),
    ("add", "    SELECT * FROM prod.users;  -- quick check"), ("add", "    # LGTM"),
    ("add", "    rm -rf \"$DIR/\"  # DIR is always set"), ("add", "    # this works and nobody knows why"),
    ("add", "    if user.email == 'ceo@company.com': return True"), ("del", "    check_permissions(user)"),
    ("add", "    # no one will ever read this line"), ("add", "    console.log(password);"),
    ("add", "    // the tests pass because there are none"), ("add", "    DEBUG = True  # prod"),
    ("add", "    # dear future me: I was tired"), ("add", "    eval(request.body)"),
    ("add", "    # you could put anything here"), ("add", "    # a recipe for banana bread, even"),
    ("add", "    # 3 ripe bananas, 1/3 cup melted butter, 1 tsp baking soda"), ("add", "    # (still nobody)"),
    ("add", "    0 0 * * 5  ./deploy.sh --prod --yolo"), ("add", "    # copied from a forum post, 2011"),
    ("add", "    disable_backups: true"), ("add", "    # hi mom"),
]


def build(seed=1111):
    rng = random.Random(seed)
    doc, anchors = [], {}
    st = {"fi": 0, "lang": "py", "old": 1, "new": 1, "gi": 0}

    def push(kind, text, tag=None):
        o = n = None
        if kind == "ctx":
            o, n = st["old"], st["new"]; st["old"] += 1; st["new"] += 1
        elif kind == "add":
            n = st["new"]; st["new"] += 1
        elif kind == "del":
            o = st["old"]; st["old"] += 1
        doc.append({"k": kind, "t": text, "o": o, "n": n, "tag": tag})
        if tag:
            anchors[tag] = len(doc) - 1

    def hunk(old, new, ctx=""):
        st["old"], st["new"] = old, new
        push("hunk", f"@@ -{old},{rng.randint(6, 40)} +{new},{rng.randint(6, 40)} @@ {ctx}")

    def file(path, lang, tag=None, start=None):
        push("gap", "")
        st["lang"] = lang
        push("file", path, tag)
        s = start or rng.randint(8, 900)
        hunk(s, s, rng.choice(["def process(self):", "class Handler:", "", "module", "export default"]))

    def fill(n):
        made = 0
        since_file = rng.randint(0, 20)
        while made < n:
            if since_file > rng.randint(45, 95):
                p, l = FILES[st["fi"] % len(FILES)]; st["fi"] += 1
                file(p, l); since_file = 0; made += 3; continue
            if rng.random() < 0.035:
                s = st["new"] + rng.randint(20, 300); hunk(s, s, ""); made += 1; continue
            if rng.random() < 0.06:
                g = GAGS[st["gi"] % len(GAGS)]; st["gi"] += 1
                push(g[0], g[1]); made += 1; since_file += 1; continue
            kind = rng.choices(["ctx", "add", "del"], [0.42, 0.38, 0.20])[0]
            run = rng.randint(1, 5 if kind != "ctx" else 3)
            for _ in range(run):
                push(kind, rng.choice(POOLS[st["lang"]])); made += 1; since_file += 1

    # ---- opening file ----
    doc.append({"k": "file", "t": "services/api/handlers.py", "o": None, "n": None, "tag": "top"}); anchors["top"] = 0
    hunk(11, 11, "import everything")
    fill(770)

    # ---- verse 1 anchors ----
    file("services/auth/session.py", "py", tag="auth", start=38)
    push("ctx", "def require_login(request):")
    push("del", "    if not request.user.is_authenticated:")
    push("del", "        raise Unauthorized()")
    push("add", "    if True:  # TODO: put auth back")
    push("add", "        pass")
    push("ctx", "    return handler(request)")
    push("add", "ADMIN_PASSWORD = \"hunter2\"  # rotate before launch")
    fill(22)
    file("db/migrations/0111_small_cleanup.sql", "sql", tag="schema", start=1)
    push("add", "-- small cleanup, should be safe")
    push("add", "DROP TABLE users;")
    push("add", "DROP TABLE users_backup;  -- we won't need this")
    push("del", "-- DO NOT RUN IN PROD")
    push("add", "ALTER TABLE payments ALTER COLUMN amount TYPE varchar(11);")
    fill(22)
    file("core/legacy/bridge.py", "py", start=209)
    push("ctx", "def bridge(old, new):")
    push("ctx", "    # TEMPORARY: remove later", tag="temp")
    push("ctx", "    return old or new or old")
    push("add", "    # TEMPORARY 2: remove after we remove the one above")
    push("add", "    return new or old or new")
    fill(22)
    file("tests/test_auth.py", "py", tag="tests", start=1)
    push("del", "def test_login_requires_password():")
    push("del", "    assert login(user, password=None) is False")
    push("del", "def test_expired_token_is_rejected():")
    push("del", "    assert check(expired_token) is False")
    push("add", "def test_everything():")
    push("add", "    assert True  # green")
    fill(1640)

    # ---- verse 2: the mess ----
    file("core/everything.py", "py", tag="mess", start=3301)
    push("del", "<<<<<<< HEAD")
    push("add", "    result = do_it_my_way(data)")
    push("del", "=======")
    push("del", "    result = do_it_his_way(data)")
    push("del", ">>>>>>> thursday")
    push("add", "    result = do_it_both_ways(data)  # compromise")
    push("add", "    # TODO: figure out which one of us wrote this")
    push("add", "    # (git blame says: both)")
    push("del", "<<<<<<< HEAD")
    push("del", "=======")
    push("add", "    return result or not result")
    push("del", ">>>>>>> thursday")
    fill(86)

    # ---- verse 3: line four hundred ----
    file("core/utils.py", "py", tag="utils", start=396)
    st["old"], st["new"] = 396, 396
    doc[-1]["t"] = "@@ -396,9 +396,10 @@ def process(data, data2, flag=False):"
    push("ctx", "def process(data, data2, flag=False):")
    push("ctx", "    out = []")
    push("del", "    for thing in data:")
    push("add", "    for thing in data + data2 + data:")
    push("ctx", "        tmp = transform(thing)")
    push("add", "        tmp2 = transform(tmp, tmp, flag, not flag, None)", tag="l400")
    push("ctx", "        out.append(tmp2 or tmp)")
    push("add", "    os.system(f\"rm -rf {out}\")  # cleanup")
    push("add", "    requests.post(PROD_URL, json=out, verify=False)")
    push("ctx", "    return out")
    assert doc[anchors["l400"]]["n"] == 400
    fill(1180)
    push("add", "    # if you are reading this, you are the first")
    push("add", "    # nobody has ever scrolled this far")
    push("gap", "")
    push("end", "end of diff  ·  187 files  ·  0 viewed", tag="end")
    for _ in range(40):
        push("gap", "")
    return doc, anchors


if __name__ == "__main__":
    d, a = build()
    print(len(d), a)
