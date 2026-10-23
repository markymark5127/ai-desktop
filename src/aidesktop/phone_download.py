"""Local, offline KDE Connect app-store QR codes for the welcome wizard.

The matrices were generated offline with QR error correction M and four-module
quiet zones. Nothing is fetched from a QR-code server and no user data is
encoded in them. They target KDE Connect on the PHONE, not GSConnect on GNOME.
"""

from __future__ import annotations

import base64
import hashlib
import zlib
from functools import lru_cache

PHONE_APPS = {
    "iphone": {
        "label": "KDE Connect for iPhone · App Store",
        "url": "https://apps.apple.com/us/app/kde-connect/id1580245991",
        "size": 41,
        "compressed": "eNpjYMACGP+K+tQzNG0wWNAQW3BsuoNej+zpBeKxj69e4FBL2cXB/jU09A8DQ0EGA6P9toPTGVZsNuxjsJy6ebuDWsoWkwMsL/6VCXCJ9W11YLic9nED4xQW7iiGqXtFfjDsnSij1VCb2v/bQVJ1hvIDocCFQQ3cPd1TF7BW+2WeYfq2WdOL8Ziw4U8Ghq2d3Qz1FfOvMihsPvD4gHhcjz0D95rUWAnWC65vzjBxhin8Y/x78eEGbI5nAAAV2UcJ",
        "sha256": "57de9af2823d7f873b507a69037d3c11a2cda30ca8866e8566d92da7f14da8f3",
    },
    "android": {
        "label": "KDE Connect for Android · Google Play",
        "url": "https://play.google.com/store/apps/details?id=org.kde.kdeconnect_tp",
        "size": 45,
        "compressed": "eNpjYMAKGP/+Syz/wKFod2JBQ6xO3dQSptce6a8XiIeKPI9laPppx8XB/jU0NP4Ag3XFCgZG8U9p+hPYp72d3ssQODVs1wemK4rzLh+QdrO6cJ7BtPvhjgMsU9/a9zOIqTomZjD+fW7Ed4DjXnJxP4Nr8467AQzB/EVhB/h8Oz48YRDUXm7ZwDiZy/88g0rWjwVZjGlKaWoP+AM92+cx8E4vnXWAoe3ivCULZL+tvv6XgWHxwYwJ7F89a0MaFLqe81kxlq4UkL/AvVDZuKAhVn3XTwUmTvYCrwPy105OUsfuSwYAEt5XbQ==",
        "sha256": "3f7a637cdd4479b2b8cc01bace97d9b31bf1a1ae714098b9841cc3262894a790",
    },
}


def app_info(phone: str) -> dict:
    if phone not in PHONE_APPS:
        raise ValueError("Unsupported phone type")
    return PHONE_APPS[phone]


@lru_cache(maxsize=2)
def qr_matrix(phone: str) -> tuple[tuple[bool, ...], ...]:
    """Return precomputed QR modules, including an unmarked four-cell quiet zone."""
    value = app_info(phone)
    width = value["size"]
    try:
        packed = zlib.decompress(base64.b64decode(value["compressed"], validate=True))
    except (ValueError, zlib.error) as exc:
        raise ValueError("Corrupted bundled QR code") from exc
    if hashlib.sha256(packed).hexdigest() != value["sha256"]:
        raise ValueError("Bundled QR code checksum did not match")
    bits = bin(int.from_bytes(packed, "big"))[2:].zfill(width * width)[-width * width:]
    return tuple(
        tuple(symbol == "1" for symbol in bits[row * width:(row + 1) * width])
        for row in range(width)
    )
