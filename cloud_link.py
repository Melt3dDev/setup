import configparser
import logging
import os
import re
import signal
import socket
import subprocess
import threading
from urllib.parse import urlsplit

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango

from ks_includes.screen_panel import ScreenPanel

OBICO_DIR = os.path.expanduser("~/moonraker-obico")
OBICO_CFG = os.path.expanduser("~/printer_data/config/moonraker-obico.cfg")
OBICO_SERVICE = "moonraker-obico"
OBICO_HOST = "meltvm.chocolate-cliff.ts.net"

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
CODE_RE = re.compile(r"manual linking and enter:\s*(\S+)")
SPINNER_RE = re.compile(r"Scanning the local network")
TOKEN_RE = re.compile(r"^\s*auth_token\s*[:=]", re.M)


class Panel(ScreenPanel):
    def __init__(self, screen, title):
        title = title or "Cloud Link"
        super().__init__(screen, title)

        self.proc = None
        self.confirm_sent = False
        self.linked = False
        self.online = False
        self.checking = False
        self.poll_id = None
        self.net_id = None

        self.code_pt = max(28, int(self._gtk.height / 9))

        self.status = Gtk.Label(hexpand=True, wrap=True, justify=Gtk.Justification.CENTER)
        self.status.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        self.code = Gtk.Label(hexpand=True, vexpand=True, selectable=True)
        self.code.set_halign(Gtk.Align.CENTER)
        self.code.set_valign(Gtk.Align.CENTER)

        self.start_btn = self._gtk.Button("cloud", _("Start"), "color1")
        self.start_btn.connect("clicked", self.start_link)
        self.stop_btn = self._gtk.Button("cancel", _("Stop"), "color3")
        self.stop_btn.connect("clicked", self.stop_link)
        self.unlink_btn = self._gtk.Button("delete", _("Unlink"), "color4")
        self.unlink_btn.connect("clicked", self.ask_unlink)

        buttons = Gtk.Box(spacing=5, hexpand=True, vexpand=False)
        for b in (self.start_btn, self.stop_btn, self.unlink_btn):
            buttons.add(b)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.add(self.status)
        box.add(self.code)
        box.add(buttons)
        self.content.add(box)

        self._set_code("")
        self._set_status(_("Checking connection to the cloud server..."))
        self._refresh_buttons()
        self.net_id = GLib.timeout_add_seconds(5, self._check_network)
        self._check_network()

    # UI helpers

    def _set_code(self, text, color=None):
        span = f'size="{self.code_pt * 1000}" weight="bold" font_family="monospace"'
        if color:
            span += f' foreground="{color}"'
        self.code.set_markup(f"<span {span}>{GLib.markup_escape_text(text)}</span>")

    def _set_status(self, text):
        self.status.set_label(text)

    def _running(self):
        return self.proc is not None and self.proc.poll() is None

    def _is_linked(self):
        try:
            with open(OBICO_CFG) as f:
                return bool(TOKEN_RE.search(f.read()))
        except OSError:
            return False

    def _refresh_buttons(self):
        running = self._running()
        linked = self._is_linked()
        self.start_btn.set_sensitive(self.online and not running and not linked)
        self.stop_btn.set_sensitive(running)
        self.unlink_btn.set_sensitive(not running and linked)

    # server reachability

    def _server_target(self):
        """(host, port) from the cfg, or None if it doesn't point at OBICO_HOST."""
        cp = configparser.ConfigParser()
        try:
            cp.read(OBICO_CFG)
            url = cp.get("server", "url").strip()
        except Exception:
            return None
        parts = urlsplit(url)
        if parts.hostname != OBICO_HOST:
            return None
        return parts.hostname, parts.port or (443 if parts.scheme == "https" else 80)

    def _check_network(self):
        if not self.checking:
            self.checking = True
            threading.Thread(target=self._probe_server, daemon=True).start()
        return True

    def _probe_server(self):
        target = self._server_target()
        reachable = False
        if target:
            try:
                with socket.create_connection(target, timeout=4):
                    reachable = True
            except Exception:
                reachable = False
        GLib.idle_add(self._network_result, reachable, target)

    def _network_result(self, reachable, target):
        self.checking = False
        was_online = self.online
        self.online = reachable
        if target is None:
            self._set_status(
                _("The config file does not point at %s.\nFix the url in [server] before linking.")
                % OBICO_HOST
            )
            self._set_code("!", color="#e74c3c")
            if self._running():
                self._kill()
        elif not reachable:
            self._set_status(
                _("Cannot reach %s:%s.\nCheck the printer's network, then try again.") % target
            )
            self._set_code("!", color="#e74c3c")
            if self._running():
                self._kill()
        elif not was_online:
            self._idle_status()
        self._refresh_buttons()
        return False

    def _idle_status(self):
        if self._is_linked():
            self._set_status(_("This printer is linked. Use Unlink to reset it."))
            self._set_code("LINKED", color="#2ecc71")
        else:
            self._set_status(_("Press Start to request a linking code."))
            self._set_code("")

    # linking

    def start_link(self, widget=None):
        if self._running() or not self.online or self._is_linked():
            return
        script = os.path.join(OBICO_DIR, "scripts", "link.sh")
        if not os.path.exists(script) or not os.path.exists(OBICO_CFG):
            self._set_status(_("Linking script not found. Check the paths in this panel."))
            return

        self.confirm_sent = False
        self.linked = False
        self._set_code("...")
        self._set_status(_("Requesting code from the cloud server..."))

        env = dict(os.environ, PYTHONUNBUFFERED="1", TERM="dumb")
        try:
            self.proc = subprocess.Popen(
                [script, "-q", "-c", OBICO_CFG],
                cwd=OBICO_DIR,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )
        except Exception as e:
            logging.exception("obico_link: failed to start link.sh")
            self._set_status(f"Failed to start: {e}")
            return

        threading.Thread(target=self._read_output, args=(self.proc,), daemon=True).start()
        self.poll_id = GLib.timeout_add_seconds(2, self._poll_linked)
        self._refresh_buttons()

    def stop_link(self, widget=None):
        self._kill()
        if not self.linked:
            self._idle_status()
        self._refresh_buttons()

    def _kill(self):
        if self.poll_id:
            GLib.source_remove(self.poll_id)
            self.poll_id = None
        proc, self.proc = self.proc, None
        if proc and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.terminate()

    def _read_output(self, proc):
        fd = proc.stdout.fileno()
        buf = ""
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            buf += ANSI_RE.sub("", chunk.decode("utf-8", "replace")).replace("\r", "\n")
            parts = buf.split("\n")
            buf = parts.pop()
            for line in parts:
                self._handle_line(line, proc)
            if buf:
                self._handle_line(buf, proc)
        GLib.idle_add(self._process_ended)

    def _handle_line(self, line, proc):
        line = line.strip()
        if not line or SPINNER_RE.search(line):
            return
        if "want to continue" in line and not self.confirm_sent:
            self.confirm_sent = True
            try:
                proc.stdin.write(b"y\n")
                proc.stdin.flush()
            except Exception:
                pass
            return
        m = CODE_RE.search(line)
        if m:
            GLib.idle_add(self._set_code, m.group(1))
            GLib.idle_add(
                self._set_status,
                _("Enter this code in the cloud app."),
            )

    def _poll_linked(self):
        if self._is_linked():
            self._on_linked()
            return False
        return True

    def _on_linked(self):
        self.linked = True
        self.poll_id = None
        self._kill()
        self._set_code("LINKED", color="#2ecc71")
        self._set_status(_("Printer linked. Restarting service..."))
        self._refresh_buttons()
        threading.Thread(target=self._restart_service, args=(True,), daemon=True).start()

    def _process_ended(self):
        if not self.linked:
            self._idle_status()
        self._refresh_buttons()
        return False

    # unlink

    def ask_unlink(self, widget=None):
        label = Gtk.Label(hexpand=True, vexpand=True, wrap=True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_markup(
            _("Remove this printer's link to the cloud server?\nYou will need to link it again to use the cloud.")
        )
        buttons = [
            {"name": _("Unlink"), "response": Gtk.ResponseType.OK, "style": "dialog-error"},
            {"name": _("Go Back"), "response": Gtk.ResponseType.CANCEL, "style": "dialog-info"},
        ]
        self._gtk.Dialog(_("Unlink Printer"), buttons, label, self.unlink_confirm)

    def unlink_confirm(self, dialog, response_id):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.OK:
            self.do_unlink()

    def do_unlink(self):
        try:
            with open(OBICO_CFG) as f:
                lines = f.readlines()
            kept = [ln for ln in lines if not TOKEN_RE.match(ln)]
            with open(OBICO_CFG + ".tmp", "w") as f:
                f.writelines(kept)
            os.replace(OBICO_CFG + ".tmp", OBICO_CFG)
        except OSError as e:
            self._set_status(f"Could not edit config: {e}")
            return
        self.linked = False
        self._set_code("")
        self._set_status(_("Unlinked. Restarting service..."))
        self._refresh_buttons()
        threading.Thread(target=self._restart_service, args=(False,), daemon=True).start()

    # service

    def _restart_service(self, linked):
        ok = False
        exception = ""
        try:
            r = subprocess.run(
                ["sudo", "-n", "systemctl", "restart", OBICO_SERVICE],
                timeout=30, capture_output=True,
            )
            ok = r.returncode == 0
        except Exception as e:
            exception = e
            ok = False
        if ok:
            msg = _("Printer linked.") if linked else _("Printer unlinked.")
        else:
            msg = _("Done, but could not restart the service. Restart it manually.")
        GLib.idle_add(self._set_status, msg)
        GLib.idle_add(self._refresh_buttons)


    def back(self):
        self._kill()
        return False

    def __del__(self):
        if self.net_id:
            try:
                GLib.source_remove(self.net_id)
            except Exception:
                pass
