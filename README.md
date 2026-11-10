# social-media-posting

Sylvia's personal photo posting. She gives 1-4 images and a caption in the chat;
Claude drafts alt text, she approves it, Claude posts.

## Workflow for Claude (read this first)

1. Images uploaded to the chat arrive as files (the message shows a path like
   `/tmp/.../images/1.webp`). Look at each one and draft alt text.
2. Show the caption and each alt text. **Wait for approval before posting.**
   Posts are public.
3. Run a dry run, then the real post:

```bash
python3 post_photos.py --caption "CAPTION" \
  --image /path/1.webp --alt "ALT 1" \
  --image /path/2.webp --alt "ALT 2" --post
```

Omit `--post` for a dry run (resizes and prints what would be posted).
`--platform mastodon` or `--platform bluesky` limits it to one; default is both.

Threads: add `--platform bluesky --reply-to <bsky.app post link>` or
`--platform mastodon --reply-to <wandering.shop post link>` (one platform per
run, since the links differ). Reply to the latest post in the thread, so the
posts stay in order. For a thread on both, run each platform separately and
chain each one's own links.
Needs `requests` and `Pillow`.

4. Report the post URLs. Don't commit photos to this repo.

## Platforms

| Platform | Account | Credentials | Status |
|---|---|---|---|
| Mastodon | @sylvia on wandering.shop | Environment API credential (Bearer) on `wandering.shop`, injected by the proxy | Working: posted a photo with alt text successfully |
| Bluesky | akasylvia.bsky.social | `BSKY_HANDLE`, `BSKY_APP_PASSWORD` env vars | Working: posted a photo with alt text successfully |

Images are re-encoded as JPEG copies: 800px longest edge for Bluesky (its upload
limit is about 1 MB), 2000px for Mastodon. Originals are untouched. Re-encoding
drops EXIF metadata, including GPS location.

Alt text limits: 1500 characters on Mastodon, 2000 on Bluesky. Caption limits:
500 on Mastodon, 300 on Bluesky.

## Mastodon token: what to know

One app and one token on wandering.shop serve @sylvia (her only account), for
both this repo and Fear of Landing (`Coding397/marketing`). The token needs
`write:statuses` and `write:media`. It can't read statuses back (403 on
`GET /api/v1/statuses/:id`); that's expected, not a fault. Don't change the
scopes to fix it: changing scopes kills the token (see below).

If posting breaks, check first:

```bash
curl -sS https://wandering.shop/api/v1/accounts/verify_credentials
```

- 200 with `"username":"sylvia"`: token is fine.
- 401 "access token is invalid": the token is dead. Fix: on wandering.shop,
  Preferences → Development → the app → **Regenerate** the access token, then
  replace the Mastodon secret in the Social Media environment (header
  `Authorization`, prefix `Bearer`, value = token only). It takes effect
  immediately in running sessions; no new session needed.
- 403 "outside the authorized scopes": a scope is missing on the app.

Changing the app's scopes on 2026-10-30 invalidated the old token, and a token
copied straight after the edit was also rejected; regenerating fixed it. Never
ask Sylvia to paste a token into the chat.

## Deliberately not included

- **Personal Facebook feed.** Facebook's API only posts to Pages, not personal
  profiles (removed in 2018), so a new connection would not help. The Facebook
  credential in the environment is the Fear of Landing Page; do not use it for
  personal photos. For Facebook, give Sylvia the caption and alt text to paste.
- **X/Twitter.** Image posting costs money; dropped.
- **Substack.** No official API; only unofficial tools that need a browser
  session cookie. Left out for now.
- **Metricool.** Sylvia doesn't want it.
