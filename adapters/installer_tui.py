#!/usr/bin/env python3
"""Interactive animated installer for the VCPS agent adapters."""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

AGENTS = (
    ("codex", "Codex", "codex", (".codex", ".agents")),
    ("claude-code", "Claude Code", "claude", (".claude",)),
)
FRAMES = ("VCPS", "CPSV", "PSVC", "SVCP")
SPINNER = "|/-\\"
PURPLE = "\033[95m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
RESET = "\033[0m"


class Terminal:
    def __enter__(self):
        try:
            self.input = open("/dev/tty", "r", encoding="utf-8", buffering=1)
            self.output = open("/dev/tty", "w", encoding="utf-8", buffering=1)
        except OSError:
            self.input, self.output = sys.stdin, sys.stdout
        self.fd = self.input.fileno()
        self.old = None
        if os.name == "posix":
            import termios
            import tty
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        self.clear()
        return self

    def __exit__(self, *_):
        if self.old is not None:
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        self.output.write("\033[0m\033[?25h\n")
        if self.input not in (sys.stdin, sys.stdout):
            self.input.close()
        if self.output not in (sys.stdin, sys.stdout):
            self.output.close()

    def clear(self):
        self.output.write("\033[2J\033[H\033[?25l")

    def key(self):
        if os.name == "nt":
            import msvcrt
            return msvcrt.getwch()
        value = self.input.read(1)
        if value == "\x1b" and os.name == "posix":
            import select
            if select.select([self.input], [], [], 0.02)[0]:
                value += self.input.read(2)
        return value

    def draw(self, lines):
        self.clear()
        self.output.write("\n".join(lines) + "\n")


def discover(target: Path):
    found = []
    home = Path.home()
    for key, label, executable, markers in AGENTS:
        paths = [home / marker for marker in markers]
        paths.extend(target / marker for marker in markers)
        command = shutil.which(executable)
        if command or any(path.exists() for path in paths):
            evidence = command or next(str(path) for path in paths if path.exists())
            found.append({"key": key, "label": label, "evidence": evidence})
    return found


def banner(frame=0):
    logo = FRAMES[frame % len(FRAMES)]
    return [
        f"{PURPLE}       ╭──────────────────────────────╮{RESET}",
        f"{PURPLE}       │{CYAN}       {logo[0]} {logo[1]} {logo[2]} {logo[3]}        {PURPLE}│{RESET}",
        f"{PURPLE}       ╰──────────────────────────────╯{RESET}",
        f"{DIM}          Evidence before confidence{RESET}",
    ]


def choose_agents(term, found):
    selected = {agent["key"] for agent in found}
    while True:
        lines = banner()
        lines += ["", f"{CYAN}VCPS INSTALLER{RESET}  ·  Sistem ajanları tarandı", ""]
        for index, agent in enumerate(found, 1):
            mark = "●" if agent["key"] in selected else "○"
            lines.append(f"  {index}. [{mark}] {agent['label']}  {DIM}{agent['evidence']}{RESET}")
        lines += ["", "Numara: seçimi aç/kapat   a: hepsini seç   Enter: devam   q: çık", ""]
        term.draw(lines)
        key = term.key().lower()
        if key in ("q", "\x03"):
            return None
        if key in ("\r", "\n"):
            if selected:
                return [agent for agent in found if agent["key"] in selected]
        elif key == "a":
            selected = {agent["key"] for agent in found}
        elif key.isdigit() and 1 <= int(key) <= len(found):
            name = found[int(key) - 1]["key"]
            if name in selected:
                selected.remove(name)
            else:
                selected.add(name)


def choose_scope(term):
    while True:
        term.draw(banner() + [
            "", f"{CYAN}KURULUM KAPSAMI{RESET}", "",
            "  1. Proje geneli   Bu depoda çalışan ajan için",
            "  2. Kullanıcı geneli   Bu bilgisayardaki kullanıcı için tüm projelerde",
            "", "1 veya 2 seç.   q: çık", "",
        ])
        key = term.key().lower()
        if key == "1":
            return "project"
        if key == "2":
            return "user"
        if key in ("q", "\x03"):
            return None


def make_command(python, installer, source, target, agent, scope, plan=False):
    command = [python, str(installer), "--adapter", agent["key"], "--source", str(source)]
    if scope == "user":
        command.append("--global")
    else:
        command += ["--target", str(target)]
    if agent["key"] == "claude-code":
        command += ["--mode", "copy"]
        if scope == "project":
            command.append("--vendor-core")
    if plan:
        command.append("--plan")
    return command


def run_animated(term, command, title, index, total):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace")
    tick = 0
    while process.poll() is None:
        term.draw(banner(tick) + [
            "", f"{CYAN}{title}{RESET}", "",
            f"  {GREEN}{SPINNER[tick % len(SPINNER)]}{RESET}  VCPS hazırlanıyor  ·  ajan {index}/{total}",
            f"  {DIM}Bileşenler aktarılıyor ve doğrulanıyor{RESET}", "",
        ])
        time.sleep(0.12)
        tick += 1
    output = process.stdout.read() if process.stdout else ""
    return process.returncode, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", default=Path.cwd(), type=Path)
    args = parser.parse_args()
    source, target = args.source.resolve(), args.target.resolve()
    if not sys.stdout.isatty() or not (Path("/dev/tty").exists() or sys.stdin.isatty()):
        print("Interactive VCPS setup needs a terminal. Use install.sh --adapter codex|claude-code.", file=sys.stderr)
        return 2

    found = discover(target)
    if not found:
        print("Codex or Claude Code not detected. Install one first, then run this installer again.", file=sys.stderr)
        return 2

    installer = source / "adapters" / "install.py"
    with Terminal() as term:
        agents = choose_agents(term, found)
        if agents is None:
            return 130
        scope = choose_scope(term)
        if scope is None:
            return 130

        destination = target if scope == "project" else Path.home()
        plan_results = []
        for agent in agents:
            command = make_command(sys.executable, installer, source, target, agent, scope, plan=True)
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            if completed.returncode != 0:
                term.draw(banner() + ["", f"{YELLOW}Ön kontrol başarısız{RESET}", completed.stdout or completed.stderr,
                                      "", "Enter: çık"])
                term.key()
                return completed.returncode
            import json
            report = json.loads(completed.stdout)
            plan_results.append((agent, report))

        lines = banner() + ["", f"{CYAN}KURULUM PLANI{RESET}", "",
                            f"  Kapsam: {'Proje' if scope == 'project' else 'Kullanıcı geneli'}",
                            f"  Hedef:  {destination}", ""]
        for agent, report in plan_results:
            lines.append(f"  {agent['label']}: {len(report.get('actions', []))} yol")
            if not report.get("ready"):
                lines.append(f"    {YELLOW}Çakışma: {', '.join(report.get('conflicts', []))}{RESET}")
                lines.extend(f"    Eksik kaynak: {item}" for item in report.get("missing_sources", []))
        lines += ["", "Devam etmek için y.   q: iptal", ""]
        term.draw(lines)
        if term.key().lower() != "y":
            return 130
        if any(not report.get("ready") for _, report in plan_results):
            return 1

        for index, agent in enumerate(agents, 1):
            command = make_command(sys.executable, installer, source, target, agent, scope)
            status, output = run_animated(term, command, f"{agent['label']} kuruluyor", index, len(agents))
            if status:
                term.draw(banner() + ["", f"{YELLOW}{agent['label']} kurulumu başarısız{RESET}", "", output, "", "Enter: çık"])
                term.key()
                return status

        term.draw(banner(1) + ["", f"{GREEN}VCPS hazır{RESET}", "",
                               f"  Kapsam: {'Proje' if scope == 'project' else 'Kullanıcı geneli'}",
                               f"  Hedef: {destination}", "",
                               "  Codex: $vcps    Claude Code: /vcps", "",
                               "Enter: kapat", ""])
        term.key()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
