# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Janne Cadamuro / LabMed Alliance Inc. — see LICENSE and NOTICE
"""Operator branding: organization name and logo shown in the header.

This never replaces the mandatory LabMed Alliance credit in the footer (NOTICE, term 1).
Logos live in `instance/branding/`, outside the repository.
"""
import os
import secrets
from io import BytesIO

from flask import current_app
from PIL import Image, UnidentifiedImageError

from helpers.settings import get_setting, get_stored, set_setting

MAX_LOGO_BYTES = 512 * 1024
MAX_NAME_LENGTH = 80
MAX_FAVICON_BYTES = 512 * 1024
MIN_FAVICON_SIZE = 32
MAX_FAVICON_SIZE = 512


#: Accepted image types, detected from the file content, not the file name.
#: SVG is left out on purpose: it can carry scripts.
MIMETYPES = {'png': 'image/png', 'jpg': 'image/jpeg', 'webp': 'image/webp'}


def logo_dir():
    return os.path.join(current_app.instance_path, 'branding')


def detect_type(data):
    """Return 'png', 'jpg', 'webp' or None."""
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    return None


def read_logo(file_storage):
    """Return (data, ext, error_key) for an uploaded file."""
    data = file_storage.read(MAX_LOGO_BYTES + 1)
    if len(data) > MAX_LOGO_BYTES:
        return None, None, 'settings_logo_too_large'
    ext = detect_type(data)
    if not ext:
        return None, None, 'settings_logo_invalid'
    return data, ext, None

def read_favicon(file_storage):
    """Return (data, ext, error_key) for a validated square favicon."""
    data = file_storage.read(MAX_FAVICON_BYTES + 1)

    if len(data) > MAX_FAVICON_BYTES:
        return None, None, 'settings_favicon_too_large'

    ext = detect_type(data)
    if not ext:
        return None, None, 'settings_favicon_invalid'

    try:
        with Image.open(BytesIO(data)) as img:
            width, height = img.size
            img.verify()
    except (UnidentifiedImageError, OSError):
        return None, None, 'settings_favicon_invalid'

    if width != height:
        return None, None, 'settings_favicon_not_square'

    if width < MIN_FAVICON_SIZE or width > MAX_FAVICON_SIZE:
        return None, None, 'settings_favicon_invalid_size'

    return data, ext, None


def save_logo(data, ext):
    """Store a new logo and remove the previous one. A new name per upload avoids stale caches."""
    os.makedirs(logo_dir(), exist_ok=True)
    name = f'logo-{secrets.token_hex(8)}.{ext}'
    with open(os.path.join(logo_dir(), name), 'wb') as f:
        f.write(data)
    remove_logo()
    set_setting('org_logo', name)


def remove_logo():
    old = get_stored('org_logo')
    if old:
        path = os.path.join(logo_dir(), os.path.basename(old))
        if os.path.exists(path):
            os.remove(path)
    set_setting('org_logo', '')


def save_favicon(data, ext):
    """Store a new favicon and remove the previous custom favicon."""
    os.makedirs(logo_dir(), exist_ok=True)
    name = f'favicon-{secrets.token_hex(8)}.{ext}'

    with open(os.path.join(logo_dir(), name), 'wb') as f:
        f.write(data)

    remove_favicon()
    set_setting('favicon', name)


def remove_favicon():
    old = get_stored('favicon')

    if old:
        path = os.path.join(logo_dir(), os.path.basename(old))
        if os.path.exists(path):
            os.remove(path)

    set_setting('favicon', '')


def get_branding():
    org_name = get_setting('org_name')
    header_title = get_setting('header_title') or org_name
    show_header_title = get_setting('show_header_title', '1') != '0'

    return {
        'org_name': org_name,
        'header_title': header_title,
        'show_header_title': show_header_title,
        'org_logo': get_stored('org_logo'),
        'favicon': get_stored('favicon'),
    }