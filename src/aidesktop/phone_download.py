"""Local, offline KDE Connect app-store QR codes for the welcome wizard.

The matrices were generated offline with QR error correction M and four-module
quiet zones. Nothing is fetched from a QR-code server and no user data is
encoded in them. They target KDE Connect on the PHONE, not GSConnect on GNOME.
"""

from __future__ import annotations

PHONE_APPS = {
    "iphone": {
        "label": "KDE Connect for iPhone · App Store",
        "url": "https://apps.apple.com/us/app/kde-connect/id1580245991",
        "size": 41,
        "bits": "0000000000000000000000000000000000000000001fd154c7f0082b030a0805d70c697402e8c1dcba0175de3d5d0082664ba0807f55555fc0000706800013fb6c19700a8b3318e003995b3b7402664b434c004e8fe76100a168eb54000d366f1b00194040b5a0095bd14f800bd911c2a807d658ffb4019259823e01251a152800b8c8b95a0057b4e69cc02f6b3294a01c61331f90000b5898b007f789fd50020b3c0e3c0175e8c3f000bac655d1805d045eccc02095620fe01fdd1e1b0000000000000000000000000000000000000",
    },
    "android": {
        "label": "KDE Connect for Android · Google Play",
        "url": "https://play.google.com/store/apps/details?id=org.kde.kdeconnect_tp",
        "size": 45,
        "bits": "00000000000000000000000000000000000000000000001fdfe6177f008213ec8a0805d2c7e957402eb4867eba0175514e75d0082f93e0a0807f555555fc0003b78a8000117f2662f900796ed978d00519556baf002d4219ed3c01b463ad0cf00358be1b8c00495ed3f8f00162541616801fde7320ec008de63738f004583b8dd5000530f7256c00e4d88f0e400112ba7398001930a4fcf00246af8a06a0166226626e00f5149879e000d97759ac00086d19ea4a01df6abd7fd0000a3c1689007f5497d5480208ae70e3a0175a9101fd00ba1233370805d27baf920020907704ac01fd6c992270000000000000000000000000000000000000000",
    },
}


def app_info(phone: str) -> dict:
    if phone not in PHONE_APPS:
        raise ValueError("Unsupported phone type")
    return PHONE_APPS[phone]


def qr_matrix(phone: str) -> tuple[tuple[bool, ...], ...]:
    """Return precomputed QR modules, including an unmarked four-cell quiet zone."""
    value = app_info(phone)
    width = value["size"]
    bits = bin(int(value["bits"], 16))[2:].zfill(width * width)[-width * width:]
    return tuple(
        tuple(symbol == "1" for symbol in bits[row * width:(row + 1) * width])
        for row in range(width)
    )
