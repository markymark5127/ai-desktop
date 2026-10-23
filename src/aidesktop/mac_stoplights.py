"""Compact macOS-like titlebar controls for AI Desktop GTK4 windows.

Native GNOME window buttons are hidden *only for our two windows*, and the
3 accessible buttons are packed in the GtkHeaderBar. We do not require a
GNOME-global appearance setting to draw properly sized circles.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


def install_stoplights(window: Gtk.Window, header: Gtk.HeaderBar) -> Gtk.Box:
    """Show three 13px non-stretched controls with standard window actions."""
    header.set_show_title_buttons(False)

    controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    controls.add_css_class("mac-stoplights")
    controls.set_valign(Gtk.Align.CENTER)

    def toggle_maximize(*_unused) -> None:
        if window.is_maximized():
            window.unmaximize()
        else:
            window.maximize()

    actions = (
        ("close", "Close window", window.close),
        ("minimize", "Minimize window", window.minimize),
        ("maximize", "Maximize or restore window", toggle_maximize),
    )
    for name, title, callback in actions:
        button = Gtk.Button()
        button.add_css_class("mac-stoplight")
        button.add_css_class("mac-" + name)
        button.set_size_request(13, 13)
        button.set_halign(Gtk.Align.CENTER)
        button.set_valign(Gtk.Align.CENTER)
        button.set_hexpand(False)
        button.set_vexpand(False)
        button.set_tooltip_text(title)
        # Accessible.update_property has slightly different GI overrides
        # across GTK4 versions. A tooltip still identifies each control if
        # a particular binding does not expose the property helper.
        try:
            button.update_property([Gtk.AccessibleProperty.LABEL], [title])
        except (AttributeError, TypeError, ValueError):
            pass
        button.connect("clicked", lambda _button, action=callback: action())
        controls.append(button)

    header.pack_start(controls)
    return controls
