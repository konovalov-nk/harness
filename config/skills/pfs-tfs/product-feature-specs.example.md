# [Example] Painless Product/Technical Specs, 2025 Edition — "Magic Link Sign-In"

Tiny, living specs beat tribal knowledge. Code explains **how**, this spec preserves **why**. Each feature ships with:

* **PFS** (Product Feature Spec) — user-view “what/why”, **everybody can read/update**
* **TFS** (Technical Feature Spec) — architect/engineers/ops “how”

> Hat tip: Joel Spolsky’s classic “**[Painless Functional Specifications](https://www.joelonsoftware.com/2000/10/02/painless-functional-specifications-part-1-why-bother/)**.” This is that idea, automated.

---

## PFS — Product (user view)

### Goal

Let users sign in without passwords via **email magic link**. Works on mobile/desktop, is safe against abuse, and takes <10 seconds.

### Stories

* As a user, I can request a sign-in link by entering my email.
* If I’m new, I’m guided through lightweight account creation after the link.
* Link expires in **1 hour**, is **single-use**, and survives email clients that prefetch images/links.
* I see clear states: sending, sent (with copy), expired, already used, rate-limited.
* Copy is finalized, localized (i18n), and accessible (WCAG AA).
* Analytics event `auth.magic_link.clicked` fires on success.

### Acceptance Criteria (Given/When/Then)

* **G** valid email, **W** request link, **T** email arrives, page shows “check your inbox,” rate limit not tripped.
* **G** click expired link, **W** open, **T** see “expired” with “resend” CTA.
* **G** click link twice, **W** second open, **T** “already used,” offer fresh link.
* **G** wrong device, **W** open link, **T** continue in web; if app installed, deep-link via Universal Links/App Links.

### Non-Functional

* p95 E2E under **150 ms** for API; deliver email in < **5 s** median.
* Availability **99.95%** monthly; error rate alert at **0.1%** in 15-min SLO window.

---

## TFS — Technical (architect view)

### High-level

* Endpoint `POST /v1/auth/magic-link` (idempotent).
* Create **opaque token** `tkn` (ULID) stored in **Redis** with payload `{user_id, email, intent, issued_at, ua_hash, ip_cidr}` and **TTL=3600s**.
* Email uses SES (or SendGrid) with fast template; both **HTML+TXT**; localized subject/body; no trackers beyond required.
* Click goes to `GET /v1/auth/callback?t=...`. Server validates: exists, not used, TTL ok, optional **UA/IP binding** fuzzy match.
* On success: **consume** token (delete), create session/JWT, set secure cookies, emit audit events, redirect to app.

### Threat Model & Mitigations

* **Replay**: single-use token + Redis delete; reuse records “used\_at,” fingerprints.
* **Link theft**: short TTL, optional IP/UA binding, notify user on first use.
* **Prefetchers**: `rel="nofollow noopener"`, use **one-time confirmation page** with “Continue” button for suspicious clients.
* **Enumeration**: uniform response (“If it exists, we’ll email you”), shadow rate-limits per **email/IP/AS**.
* **Abuse**: CAPTCHA after thresholds; greylisting unknown ASNs; SES template throttle.

### Deliverability

* SPF/DKIM/DMARC aligned; subdomain `auth.mail.example.com`.
* Bounce/complaint webhook → **suppress list**; dashboard for hard/soft bounces.
* Warm-up plan (gradual volume); monitoring for blocklists.

### Observability

* Metrics: request rate, send latency, bounce rate, callback success, p95, error codes.
* Tracing spans: `auth.request`, `email.send`, `token.issue`, `token.consume`.
* Logs are structured, PII minimized.
* Alerts: error>0.1%, bounce>0.5%, SES throttle, Redis miss ratio>0.5%.

### Rollout

* Feature flag `auth_magic_link`.
* Canary: 10% → 50% → 100% over 24h with rollback.
* Kill-switch: reject new requests, leave existing tokens valid for TTL.

---

## API (contract)

```http
POST /v1/auth/magic-link
Headers: Idempotency-Key: <uuidv4>
Body: { "email": "user@example.com", "intent": "login" }
200 { "status": "sent" } // always 200 to avoid enum
429 { "retry_after": 120 } // rate limited
```

```http
GET /v1/auth/callback?t=<opaque>
302 Location: /app
401/410 for invalid/expired/used
```

---

## Data & Infra

### Redis key

```
ML:<tkn> -> { user_id, email, ua_hash, ip_cidr, issued_at, used_at? } TTL=3600
```

### Audit/Event

```
auth.magic_link.requested { email_hash, ip_cidr, ua_hash }
auth.magic_link.sent { user_id?, provider, msg_id }
auth.magic_link.clicked { user_id, ip_cidr, ua_hash }
auth.magic_link.failed { reason }
```

### Terraform (sketch)

* SES domain identity + DKIM.
* Secrets in AWS Secrets Manager.
* Redis (Elasticache) or self-hosted with AOF; multi-AZ.

---

## Security Checklist

* [x] Tokens opaque, random, **>=128 bits** entropy.
* [x] Single-use enforced (DELETE on consume).
* [x] TTL ≤ 1h; leeway ±5m for clock skew.
* [x] Cookies: `Secure`, `HttpOnly`, `SameSite=Lax`.
* [x] CSRF on follow-up POSTs.
* [ ] Abuse controls (rate limiters per email/IP/ASN).
* [ ] Email content doesn’t reveal account existence.

---

## Accessibility & UX

* Semantic buttons/links, focus states, ARIA labels.
* Plain-text email renders cleanly; no essential content in images.
* Copy variants A/B tested for comprehension in 3 locales.

---

## Testing Strategy

* Unit: token issue/consume, TTL, replay.
* Contract: OpenAPI + Dredd/Newman.
* E2E: “happy path,” expired, reused, prefetch simulation.
* Property tests: random UA/IP; ensure no leak of account existence.
* Chaos: Redis failover, SES throttle.

---

## Runbooks (abridged)

* **Spike in 401 on callback** → check Redis evictions, clock skew, prefetchers; disable “auto-open links” for Outlook via confirm page.
* **Bounce surge** → pause sends to high-bounce domains, verify DMARC alignment, contact ESP support.
* **SES throttle** → backoff, queue, raise limits, temporarily route via backup provider.

---

## Cost (napkin)

* SES: ~$0.10 per 1k emails + $0.12/GB attachments (we send none).
* Redis: r6g.large multi-AZ ~$90–120/mo (load dependent).
* Misc infra negligible vs product value.

---

## Example Implementation (pseudo-code)

```python
# POST /v1/auth/magic-link
def request_magic_link(email, intent, idem_key):
    if is_rate_limited(email, request.ip): return ok({"status": "sent"})
    user = find_or_invite(email)
    tkn = ulid()
    redis.setex(f"ML:{tkn}", 3600, {
        "user_id": user.id, "email": email,
        "ua_hash": sha1(request.ua), "ip_cidr": cidr(request.ip),
        "issued_at": now()
    })
    send_email(email, template="magic_link",
               link=f"https://example.com/v1/auth/callback?t={tkn}")
    audit("auth.magic_link.sent", user_id=user.id)
    return ok({"status": "sent"})
```

```python
# GET /v1/auth/callback
def callback(t):
    rec = redis.getdel(f"ML:{t}")     # atomic fetch+delete (or Lua script)
    if not rec or expired(rec): return err(410)
    if suspicious(rec, request): return show_confirm(rec)
    session = create_session(rec["user_id"])
    set_session_cookie(session)
    track("auth.magic_link.clicked", user_id=rec["user_id"])
    return redirect("/app")
```
