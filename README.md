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
Needs `requests` and `Pillow`.

4. Report the post URLs. Don't commit photos to this repo.

## Platforms

| Platform | Account | Credentials | Status |
|---|---|---|---|
| Mastodon | @sylvia on wandering.shop | Injected by the session proxy; no token needed | Token must have `write:media` and `write:statuses` scopes (see Open items) |
| Bluesky | akasylvia.bsky.social | `BSKY_HANDLE`, `BSKY_APP_PASSWORD` env vars | Working: posted a photo with alt text successfully |

Images are re-encoded as JPEG copies: 800px longest edge for Bluesky (its upload
limit is about 1 MB), 2000px for Mastodon. Originals are untouched. Re-encoding
drops EXIF metadata, including GPS location.

Alt text limits: 1500 characters on Mastodon, 2000 on Bluesky. Caption limits:
500 on Mastodon, 300 on Bluesky.

## Open items

**Mastodon token scopes.** The original token was read-only: uploads failed with
403 "This action is outside the authorized scopes". Sylvia then added
`write:media` and `write:statuses` to her existing app on wandering.shop, which
invalidated the old token (401 "The access token is invalid"). She is putting the
new token in the environment settings (Network secrets / API credentials); a new
session picks it up, a running one does not. One app and one token serve her only
account, @sylvia, and will also serve Fear of Landing later.

At the start of a session, check it before anything else:

```bash
curl -sS https://wandering.shop/api/v1/accounts/verify_credentials
```

A 200 with `"username":"sylvia"` means the token works. Still 401: the new token
isn't in the environment yet. Still 403 on upload: the scopes are missing. Never
ask Sylvia to paste a token into the chat.

**Mastodon post still to do.** Bluesky was posted on 2026-10-30, Mastodon was not.
Photo of a crow on a wooden chair next to a small sculpture; Sylvia needs to
re-upload it (it is not stored in this repo). Use the same wording as Bluesky:

- Caption: `Crow and Sculpture, performance art by Remington, 2026`
- Alt text: `A crow perched on the back of a wooden chair next to a small sculpture.`
- Run with `--platform mastodon`. Sylvia has approved this post; check with her
  only if the wording changes.

## Deliberately not included

- **Personal Facebook feed.** Facebook's API only posts to Pages, not personal
  profiles (removed in 2018), so a new connection would not help. The Facebook
  credential in the environment is the Fear of Landing Page; do not use it for
  personal photos. For Facebook, give Sylvia the caption and alt text to paste.
- **X/Twitter.** Image posting costs money; dropped.
- **Substack.** No official API; only unofficial tools that need a browser
  session cookie. Left out for now.
- **Metricool.** Sylvia doesn't want it.
