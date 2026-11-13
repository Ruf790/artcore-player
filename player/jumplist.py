"""The taskbar Jump List (right click on the player's taskbar button / Start tile): "Recent" with the films
from the player's own recent list — each with its format icon and the place where you stopped — and the
tasks "Open file…" / "Open address…". Built with ICustomDestinationList (comtypes, no type library needed),
so it works in the portable version too, without file associations. Off Windows it does nothing."""
from __future__ import annotations

import os
import sys

IS_WIN = sys.platform == "win32"
MAX_ITEMS = 10

if IS_WIN:
    import ctypes
    from ctypes import POINTER, Structure, byref, c_int, c_uint, c_ushort, c_void_p, c_wchar_p, create_unicode_buffer
    from ctypes.wintypes import DWORD

    import comtypes
    from comtypes import CLSCTX_INPROC_SERVER, GUID, HRESULT, IUnknown, STDMETHOD

    class PROPERTYKEY(Structure):
        _fields_ = [("fmtid", GUID), ("pid", DWORD)]

    class PROPVARIANT(Structure):                        # only the VT_LPWSTR / VT_BOOL shapes are used
        _fields_ = [("vt", c_ushort), ("r1", c_ushort), ("r2", c_ushort), ("r3", c_ushort),
                    ("val", c_void_p), ("pad", c_void_p)]

    class IObjectArray(IUnknown):
        _iid_ = GUID("{92CA9DCD-5622-4BBA-A805-5E9F541BD8C9}")
        _methods_ = [
            STDMETHOD(HRESULT, "GetCount", [POINTER(c_uint)]),
            STDMETHOD(HRESULT, "GetAt", [c_uint, POINTER(GUID), POINTER(c_void_p)]),
        ]

    class IObjectCollection(IObjectArray):
        _iid_ = GUID("{5632B1A4-E38A-400A-928A-D4CD63230295}")
        _methods_ = [
            STDMETHOD(HRESULT, "AddObject", [POINTER(IUnknown)]),
            STDMETHOD(HRESULT, "AddFromArray", [POINTER(IObjectArray)]),
            STDMETHOD(HRESULT, "RemoveObjectAt", [c_uint]),
            STDMETHOD(HRESULT, "Clear", []),
        ]

    class ICustomDestinationList(IUnknown):
        _iid_ = GUID("{6332DEBF-87B5-4670-90C0-5E57B408A49E}")
        _methods_ = [
            STDMETHOD(HRESULT, "SetAppID", [c_wchar_p]),
            STDMETHOD(HRESULT, "BeginList", [POINTER(c_uint), POINTER(GUID), POINTER(POINTER(IObjectArray))]),
            STDMETHOD(HRESULT, "AppendCategory", [c_wchar_p, POINTER(IObjectArray)]),
            STDMETHOD(HRESULT, "AppendKnownCategory", [c_int]),
            STDMETHOD(HRESULT, "AddUserTasks", [POINTER(IObjectArray)]),
            STDMETHOD(HRESULT, "CommitList", []),
            STDMETHOD(HRESULT, "GetRemovedDestinations", [POINTER(GUID), POINTER(POINTER(IObjectArray))]),
            STDMETHOD(HRESULT, "DeleteList", [c_wchar_p]),
            STDMETHOD(HRESULT, "AbortList", []),
        ]

    class IShellLinkW(IUnknown):
        _iid_ = GUID("{000214F9-0000-0000-C000-000000000046}")
        _methods_ = [                                    # the vtable order of shobjidl.h
            STDMETHOD(HRESULT, "GetPath", [c_wchar_p, c_int, c_void_p, DWORD]),
            STDMETHOD(HRESULT, "GetIDList", [c_void_p]),
            STDMETHOD(HRESULT, "SetIDList", [c_void_p]),
            STDMETHOD(HRESULT, "GetDescription", [c_wchar_p, c_int]),
            STDMETHOD(HRESULT, "SetDescription", [c_wchar_p]),
            STDMETHOD(HRESULT, "GetWorkingDirectory", [c_wchar_p, c_int]),
            STDMETHOD(HRESULT, "SetWorkingDirectory", [c_wchar_p]),
            STDMETHOD(HRESULT, "GetArguments", [c_wchar_p, c_int]),
            STDMETHOD(HRESULT, "SetArguments", [c_wchar_p]),
            STDMETHOD(HRESULT, "GetHotkey", [c_void_p]),
            STDMETHOD(HRESULT, "SetHotkey", [c_ushort]),
            STDMETHOD(HRESULT, "GetShowCmd", [c_void_p]),
            STDMETHOD(HRESULT, "SetShowCmd", [c_int]),
            STDMETHOD(HRESULT, "GetIconLocation", [c_wchar_p, c_int, c_void_p]),
            STDMETHOD(HRESULT, "SetIconLocation", [c_wchar_p, c_int]),
            STDMETHOD(HRESULT, "SetRelativePath", [c_wchar_p, DWORD]),
            STDMETHOD(HRESULT, "Resolve", [c_void_p, DWORD]),
            STDMETHOD(HRESULT, "SetPath", [c_wchar_p]),
        ]

    class IPropertyStore(IUnknown):
        _iid_ = GUID("{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}")
        _methods_ = [
            STDMETHOD(HRESULT, "GetCount", [POINTER(DWORD)]),
            STDMETHOD(HRESULT, "GetAt", [DWORD, POINTER(PROPERTYKEY)]),
            STDMETHOD(HRESULT, "GetValue", [POINTER(PROPERTYKEY), POINTER(PROPVARIANT)]),
            STDMETHOD(HRESULT, "SetValue", [POINTER(PROPERTYKEY), POINTER(PROPVARIANT)]),
            STDMETHOD(HRESULT, "Commit", []),
        ]

    CLSID_DestinationList = GUID("{77F10CF0-3DB5-4966-B520-B7C54FD35ED6}")
    CLSID_EnumerableObjectCollection = GUID("{2D3468C1-36A7-43B6-AC24-D3F02FD9607A}")
    CLSID_ShellLink = GUID("{00021401-0000-0000-C000-000000000046}")
    PKEY_Title = PROPERTYKEY(GUID("{F29F85E0-4FF9-1068-AB91-08002B27B3D9}"), 2)
    VT_LPWSTR = 31


def _launcher() -> tuple[str, str]:
    """(exe, arguments before ours): the frozen exe, or python + run.py from the source tree."""
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    run = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run.py")
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return (pyw if os.path.isfile(pyw) else exe), f'"{run}" '


def _quote(arg: str) -> str:
    return '"' + arg.replace('"', '') + '"'


def _link(title: str, args: str, icon: str = "", icon_index: int = 0, tip: str = ""):
    exe, pre = _launcher()
    link = comtypes.CoCreateInstance(CLSID_ShellLink, IShellLinkW, CLSCTX_INPROC_SERVER)
    link.SetPath(exe)
    link.SetArguments(pre + args)
    link.SetWorkingDirectory(os.path.dirname(exe))
    link.SetIconLocation(icon or exe, icon_index if icon else 0)
    if tip:
        link.SetDescription(tip[:259])
    store = link.QueryInterface(IPropertyStore)
    text = c_wchar_p(title)
    pv = PROPVARIANT()
    pv.vt = VT_LPWSTR
    pv.val = ctypes.cast(text, c_void_p).value
    key = PROPERTYKEY(PKEY_Title.fmtid, PKEY_Title.pid)
    store.SetValue(byref(key), byref(pv))
    store.Commit()
    return link


def _removed(arr) -> set[str]:
    """Arguments of the items the user took off the list (BeginList hands them over): they must not come
    back — Windows refuses a list that has them."""
    out: set[str] = set()
    try:
        n = c_uint(0)
        arr.GetCount(byref(n))
        for i in range(n.value):
            p = c_void_p()
            arr.GetAt(i, byref(IShellLinkW._iid_), byref(p))
            if not p.value:
                continue
            link = ctypes.cast(p, POINTER(IShellLinkW))      # released by comtypes when it goes
            buf = create_unicode_buffer(2048)
            link.GetArguments(buf, 2048)
            out.add(buf.value)
    except Exception:
        pass
    return out


def update(app_id: str, recent: list[tuple[str, str, str]], tasks: list[tuple[str, str, str]],
           category: str) -> tuple[bool, str, list[str]]:
    """recent: (title, argument, icon file); tasks: (title, argument, icon file).
    → (committed, error, arguments the user removed from the list)."""
    if not IS_WIN:
        return False, "not Windows", []
    try:
        dl = comtypes.CoCreateInstance(CLSID_DestinationList, ICustomDestinationList, CLSCTX_INPROC_SERVER)
        dl.SetAppID(app_id)
        slots = c_uint(0)
        arr = POINTER(IObjectArray)()
        dl.BeginList(byref(slots), byref(IObjectArray._iid_), byref(arr))
        _, pre = _launcher()
        removed = _removed(arr)
        gone = [a[len(pre):] if a.startswith(pre) else a for a in removed]
        items = [r for r in recent if _quote(r[1]) not in gone][:max(1, min(MAX_ITEMS, slots.value or MAX_ITEMS))]
        if items:
            col = comtypes.CoCreateInstance(CLSID_EnumerableObjectCollection, IObjectCollection, CLSCTX_INPROC_SERVER)
            for title, arg, icon in items:
                col.AddObject(_link(title, _quote(arg), icon, 0, arg).QueryInterface(IUnknown))
            dl.AppendCategory(category, col.QueryInterface(IObjectArray))
        if tasks:
            col = comtypes.CoCreateInstance(CLSID_EnumerableObjectCollection, IObjectCollection, CLSCTX_INPROC_SERVER)
            for title, arg, icon in tasks:
                col.AddObject(_link(title, arg, icon).QueryInterface(IUnknown))
            dl.AddUserTasks(col.QueryInterface(IObjectArray))
        dl.CommitList()
        return True, "", [g.strip('"') for g in gone]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", []


def clear(app_id: str) -> None:
    if not IS_WIN:
        return
    try:
        dl = comtypes.CoCreateInstance(CLSID_DestinationList, ICustomDestinationList, CLSCTX_INPROC_SERVER)
        dl.DeleteList(app_id)
    except Exception:
        pass
