import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from ks_includes.screen_panel import ScreenPanel


class Panel(ScreenPanel):
    def __init__(self, screen, title):
        title = title or _("Bed Angle")
        super().__init__(screen, title)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(100)

        main_menu = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        aangle_btn = self._gtk.Button("menu", _("A Angle"), "color3")
        bangle_btn = self._gtk.Button("menu", _("B Angle"), "color4")

        aangle_btn.connect("clicked", self.show_submenu, "aangle")
        bangle_btn.connect("clicked", self.show_submenu, "bangle")

        main_menu.attach(aangle_btn, 0, 0, 1, 1)
        main_menu.attach(bangle_btn, 1, 0, 1, 1)

        aangle = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        aangle_buttons = [
            ("arrow-up", "G14 A1 B0 R", _("A Angle +1°")),
            ("arrow-up", "G14 A5 B0 R", _("A Angle +5°")),
            ("arrow-up", "G14 A10 B0 R", _("A Angle +10°")),
            ("arrow-down", "G14 A-1 B0 R", _("A Angle -1°")),
            ("arrow-down", "G14 A-5 B0 R", _("A Angle -5°")),
            ("arrow-down", "G14 A-10 B0 R", _("A Angle -10°")),
        ]
        for i, (icon, gcode, label) in enumerate(aangle_buttons):
            btn = self._gtk.Button(icon, label, "color1")
            btn.connect("clicked", self.send_gcode, gcode)
            aangle.attach(btn, i % 3, i // 3, 1, 1)

        back_btn1 = self._gtk.Button("back", _("Back"), "color2")
        back_btn1.connect("clicked", self.show_submenu, "main_menu")
        aangle.attach(back_btn1, 0, 2, 3, 1)

        bangle = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        bangle_buttons = [
            ("arrow-up", "G14 A0 B1 R", _("B Angle +1°")),
            ("arrow-up", "G14 A0 B5 R", _("B Angle +5°")),
            ("arrow-up", "G14 A0 B10 R", _("B Angle +10°")),
            ("arrow-down", "G14 A0 B-1 R", _("B Angle -1°")),
            ("arrow-down", "G14 A0 B-5 R", _("B Angle -5°")),
            ("arrow-down", "G14 A0 B-10 R", _("B Angle -10°")),
        ]
        for i, (icon, gcode, label) in enumerate(bangle_buttons):
            btn = self._gtk.Button(icon, label, "color2")
            btn.connect("clicked", self.send_gcode, gcode)
            bangle.attach(btn, i % 3, i // 3, 1, 1)

        back_btn2 = self._gtk.Button("back", _("Back"), "color3")
        back_btn2.connect("clicked", self.show_submenu, "main_menu")
        bangle.attach(back_btn2, 0, 2, 3, 1)

        self.stack.add_named(main_menu, "main_menu")
        self.stack.add_named(aangle, "aangle")
        self.stack.add_named(bangle, "bangle")

        self.content.add(self.stack)

        self.stack.set_visible_child_name("main_menu")

    def show_submenu(self, widget, menu_name):
        self.stack.set_visible_child_name(menu_name)

    def send_gcode(self, widget, gcode):
        self._screen._send_action(widget, "printer.gcode.script", {"script": gcode})
