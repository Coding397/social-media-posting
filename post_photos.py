#!/usr/bin/env python3
"""Post 1-4 photos with a caption and per-image alt text to Mastodon (@sylvia on
wandering.shop) and Bluesky (akasylvia.bsky.social).

Credentials come from the environment, never from this repo:
  Mastodon  injected by the session proxy (no token needed)
  Bluesky   BSKY_HANDLE and BSKY_APP_PASSWORD env vars

Images are re-encoded as JPEG copies (originals untouched). Re-encoding drops
EXIF metadata, including GPS location. Nothing is posted without --post.

Usage:
  post_photos.py --caption "Text" \
      --image a.jpg --alt "Alt for a" \
      --image b.jpg --alt "Alt for b" [--platform mastodon] [--post]
"""
import argparse, datetime, io, os, sys, time
import requests
from PIL import Image, ImageOps

MASTODON = "https://wandering.shop"
BSKY = "https://bsky.social"
MAX_IMAGES = 4
LIMITS = {  # caption chars, alt chars, longest image edge, max bytes
    "mastodon": dict(caption=500, alt=1500, edge=2000, size=15_000_000),
    "bluesky": dict(caption=300, alt=2000, edge=800, size=950_000),
}


def prepare(path, edge, max_bytes):
    """Return JPEG bytes (and dimensions) no larger than `edge` px and `max_bytes`."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((edge, edge))
    for q in (90, 85, 80, 75, 70, 60, 50):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True)  # no exif= -> metadata dropped
        if buf.tell() <= max_bytes:
            return buf.getvalue(), img.size
    sys.exit(f"Could not get {path} under {max_bytes} bytes")


def post_mastodon(caption, items):
    ids = []
    for data, _size, alt in items:
        r = requests.post(f"{MASTODON}/api/v2/media",
                          files={"file": ("photo.jpg", data, "image/jpeg")},
                          data={"description": alt}, timeout=120)
        r.raise_for_status()
        m = r.json()
        if r.status_code == 202:  # still processing server-side
            for _ in range(30):
                time.sleep(2)
                if requests.get(f"{MASTODON}/api/v1/media/{m['id']}", timeout=30).status_code == 200:
                    break
            else:
                sys.exit("Timed out waiting for Mastodon to process an image")
        ids.append(m["id"])
    r = requests.post(f"{MASTODON}/api/v1/statuses", timeout=60,
                      data={"status": caption, "visibility": "public", "media_ids[]": ids})
    r.raise_for_status()
    return r.json()["url"]


def post_bluesky(caption, items):
    s = requests.post(f"{BSKY}/xrpc/com.atproto.server.createSession", timeout=30,
                      json={"identifier": os.environ["BSKY_HANDLE"],
                            "password": os.environ["BSKY_APP_PASSWORD"]})
    s.raise_for_status()
    s = s.json()
    auth = {"Authorization": f"Bearer {s['accessJwt']}"}
    images = []
    for data, (w, h), alt in items:
        r = requests.post(f"{BSKY}/xrpc/com.atproto.repo.uploadBlob", timeout=120,
                          headers={**auth, "Content-Type": "image/jpeg"}, data=data)
        r.raise_for_status()
        images.append({"alt": alt, "image": r.json()["blob"],
                       "aspectRatio": {"width": w, "height": h}})
    record = {"$type": "app.bsky.feed.post", "text": caption,
              "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
              "embed": {"$type": "app.bsky.embed.images", "images": images}}
    r = requests.post(f"{BSKY}/xrpc/com.atproto.repo.createRecord", timeout=60, headers=auth,
                      json={"repo": s["did"], "collection": "app.bsky.feed.post", "record": record})
    r.raise_for_status()
    rkey = r.json()["uri"].rsplit("/", 1)[1]
    return f"https://bsky.app/profile/{s['handle']}/post/{rkey}"


POSTERS = {"mastodon": post_mastodon, "bluesky": post_bluesky}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--caption", required=True)
    p.add_argument("--image", action="append", default=[])
    p.add_argument("--alt", action="append", default=[])
    p.add_argument("--platform", action="append", choices=list(POSTERS),
                   help="repeat to pick platforms; default is all")
    p.add_argument("--post", action="store_true", help="actually post (default is dry run)")
    a = p.parse_args()
    platforms = a.platform or list(POSTERS)

    if not 1 <= len(a.image) <= MAX_IMAGES:
        sys.exit(f"Need 1-{MAX_IMAGES} images, got {len(a.image)}")
    if len(a.alt) != len(a.image):
        sys.exit("Need exactly one --alt per --image, in the same order")
    for path in a.image:
        if not os.path.isfile(path):
            sys.exit(f"Not found: {path}")
    for plat in platforms:
        lim = LIMITS[plat]
        if len(a.caption) > lim["caption"]:
            sys.exit(f"Caption is {len(a.caption)} chars; {plat} allows {lim['caption']}")
        for alt in a.alt:
            if len(alt) > lim["alt"]:
                sys.exit(f"An alt text is {len(alt)} chars; {plat} allows {lim['alt']}")

    print(f"Caption: {a.caption}\nPlatforms: {', '.join(platforms)}")
    prepared = {}
    for plat in platforms:
        lim = LIMITS[plat]
        prepared[plat] = []
        for path, alt in zip(a.image, a.alt):
            data, size = prepare(path, lim["edge"], lim["size"])
            prepared[plat].append((data, size, alt))
            print(f"- [{plat}] {os.path.basename(path)} -> {size[0]}x{size[1]}, {len(data)//1024} KB\n  alt: {alt}")
    if not a.post:
        print("\nDry run. Add --post to publish.")
        return
    for plat in platforms:
        print(f"{plat}: {POSTERS[plat](a.caption, prepared[plat])}")


if __name__ == "__main__":
    main()
