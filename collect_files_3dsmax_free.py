# -*- coding: utf-8 -*-
"""
CF3F - Collect Files for 3ds Max (Free Edition, After Effects style)
Non-destructive, ultra-fast in-process scene, texture & XRef collector (.max)
3ds Max 2021 - 2027 (PySide2 / PySide6 compatible, Zero external dependencies)
Bilingual UI (Japanese / English)
"""

import os
import re
import glob
import shutil
import pymxs
from pymxs import runtime as rt

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

try:
    import qtmax
except ImportError:
    qtmax = None


WINDOW_OBJECT_NAME = "CF3FCollectFilesDialog"
SETTINGS_ORG = "CF3F_3dsMax"
SETTINGS_APP = "CollectFilesFree"

# ---------------------------------------------------------------------------
# 多言語対応 (日本語 / English)
# ---------------------------------------------------------------------------
_EN = {
    "CF3F - Collect Files for 3ds Max (ファイル収集)": "CF3F - Collect Files for 3ds Max",
    "1. 保存先とフォルダ名": "1. Destination & Folder Name",
    "保存先の親フォルダを選択...": "Select destination parent folder...",
    "参照...": "Browse...",
    "保存先フォルダ:": "Destination Folder:",
    "新規フォルダ名:": "New Folder Name:",
    "2. 収集オプション": "2. Collection Options",
    "テクスチャ・キャッシュ等の外部ファイルを収集する": "Collect external assets (textures, caches, IFL, audio, etc.)",
    "XRef (外部参照シーン / オブジェクト) を収集する": "Collect XRef files (scenes / objects)",
    "サブフォルダに分けて整理する (scenes / maps)": "Organize into subfolders (scenes / maps)",
    "プロジェクト設定 (.mxp) を生成して相対パス化する（推奨）": "Generate project file (.mxp) for relative paths (Recommended)",
    "収集完了後にフォルダを開く": "Open folder after collection",
    "待機中...": "Ready...",
    "XRef (外部参照) をスキャン・収集中...": "Scanning and collecting XRef files...",
    "テクスチャ・外部アセットを収集中...": "Collecting textures and external assets...",
    "リンクを書き換えてシーンを保存中...": "Relinking paths and saving scene...",
    "収集を実行 (Collect Files)": "Collect Files",
    "閉じる": "Close",
    "保存先フォルダを選択": "Select Destination Folder",
    "エラー": "Error",
    "上書き確認": "Confirm Overwrite",
    "CF3F 完了": "CF3F Complete",
    "有効な保存先フォルダを指定してください。": "Please specify a valid destination folder.",
    "収集フォルダ名を入力してください。": "Please enter a folder name.",
    "既に空でない同名フォルダが存在します:\n{path}": "A non-empty folder with the same name already exists:\n{path}",
    "既に同名のフォルダが存在します:\n{path}\n\n既存のフォルダを削除して上書きしますか？": (
        "A non-empty folder with the same name already exists:\n{path}\n\nDo you want to delete the existing folder and overwrite it?"
    ),
    "元データを含むフォルダは上書きできません:\n{path}": "Cannot overwrite a folder that contains source files:\n{path}",
    "収集が完了しました！\n\n出力先:\n{root}\n\nコピーした外部ファイル数: {count} 件": (
        "Collection complete!\n\nOutput folder:\n{root}\n\nExternal files copied: {count}"
    ),
    "\n...他 {count} 件": "\n...and {count} more",
    "\n\n【注意】リンク切れのためスキップされたファイル ({count} 件):\n{preview}{extra}": (
        "\n\n[Warning] Skipped missing/broken files ({count}):\n{preview}{extra}"
    ),
}

_CURRENT_LANG = None


def _get_settings():
    return QtCore.QSettings(SETTINGS_ORG, SETTINGS_APP)


def get_lang():
    global _CURRENT_LANG
    if _CURRENT_LANG in ("JA", "EN"):
        return _CURRENT_LANG

    try:
        saved = _get_settings().value("ui_language", "")
        if saved in ("JA", "EN"):
            _CURRENT_LANG = saved
            return _CURRENT_LANG
    except Exception:
        pass

    try:
        lang_info = rt.sysInfo.getLanguage(user=True)
        lang_str = str(lang_info).upper()
        _CURRENT_LANG = "JA" if ("1041" in lang_str or "JPN" in lang_str or "JAPANESE" in lang_str) else "EN"
    except Exception:
        _CURRENT_LANG = "JA"

    return _CURRENT_LANG


def set_lang(lang):
    global _CURRENT_LANG
    if lang not in ("JA", "EN"):
        return
    _CURRENT_LANG = lang
    try:
        _get_settings().setValue("ui_language", lang)
    except Exception:
        pass


def tr(text):
    if get_lang() == "EN":
        return _EN.get(text, text)
    return text


def get_max_main_window():
    if qtmax is not None:
        try:
            return qtmax.GetQMaxMainWindow()
        except Exception:
            pass
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, QtWidgets.QMainWindow):
            return w
    return None


def norm_key(path):
    """OSのパス表記揺れを吸収した比較用正規化キーを返す"""
    if not path:
        return ""
    return os.path.normcase(os.path.abspath(path)).replace("\\", "/")


def to_win_path(path):
    return path.replace("/", "\\")


def _is_unsafe_overwrite_target(collect_root, protected_paths=None):
    """ドライブルートや元データ（シーン・テクスチャ・XRef）を含むフォルダの誤削除を防ぐ安全チェック"""
    abs_root = os.path.abspath(collect_root)
    if os.path.dirname(abs_root) == abs_root:
        return True

    norm_root = norm_key(abs_root)
    for p in (protected_paths or []):
        if not p:
            continue
        norm_p = norm_key(p)
        if norm_p == norm_root or norm_p.startswith(norm_root + "/"):
            return True

    return False


def _gather_current_protected_paths():
    """上書き削除から保護すべき元シーン・元XRef・元アセットの実パス一覧を収集する"""
    protected = []
    orig_max_dir = str(rt.maxFilePath or "")
    orig_max_name = str(rt.maxFileName or "")
    if orig_max_dir and orig_max_name:
        protected.append(os.path.join(orig_max_dir, orig_max_name))

    try:
        xref_count = int(rt.xrefs.getXRefFileCount())
        for idx in range(1, xref_count + 1):
            raw_x = str(rt.xrefs.getXRefFile(idx).filename or "")
            if raw_x:
                protected.append(str(rt.pathConfig.resolvePathSymbols(raw_x)))
    except Exception:
        pass

    try:
        rec_count = int(rt.objXRefMgr.recordCount)
        for idx in range(1, rec_count + 1):
            raw_x = str(rt.objXRefMgr.GetRecord(idx).srcFileName or "")
            if raw_x:
                protected.append(str(rt.pathConfig.resolvePathSymbols(raw_x)))
    except Exception:
        pass

    try:
        for bmp in list(rt.getClassInstances(rt.Bitmaptexture)):
            raw_b = str(bmp.filename or "")
            if raw_b:
                protected.append(str(rt.pathConfig.resolvePathSymbols(raw_b)))
    except Exception:
        pass

    try:
        rt.ATSOps.Refresh()
        ats_files = rt.Array()
        rt.ATSOps.GetFiles(pymxs.byref(ats_files))
        for item in list(ats_files):
            s = str(item or "")
            if s and rt.ATSOps.IsInputFile(s):
                resolved = str(rt.pathConfig.resolvePathSymbols(s))
                if "<UDIM>" in resolved:
                    protected.append(os.path.dirname(resolved))
                else:
                    protected.append(resolved)
    except Exception:
        pass

    return protected


def write_minimal_mxp(project_dir, project_name):
    """他のPCや別ドライブへ移動してもプロジェクト構成を認識できるように.mxpを生成する"""
    mxp_content = (
        "[Directories]\n"
        "Scenes=.\\scenes\n"
        "Images=.\\maps\n"
        "Textures=.\\maps\n"
        "Previews=.\\previews\n"
        "Animations=.\\scenes\n"
        "Sounds=.\\sound\n"
        "Import=.\\import\n"
        "Export=.\\export\n"
    )
    mxp_path = os.path.join(project_dir, f"{project_name}.mxp")
    with open(mxp_path, "w", encoding="utf-8") as f:
        f.write(mxp_content)


def expand_wildcard_files(filepath):
    """UDIM (<UDIM>) に該当する実ファイルをすべて取得する"""
    if not filepath:
        return []

    norm_path = filepath.replace("\\", "/")
    if "<UDIM>" in norm_path:
        pattern = norm_path.replace("<UDIM>", "*")
        matched = glob.glob(pattern)
        return sorted([p.replace("\\", "/") for p in matched if os.path.isfile(p)])

    if os.path.isfile(norm_path):
        return [norm_path]

    return []


def read_text_lines_fallback(filepath):
    for enc in ("utf-8-sig", "cp932", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.readlines()
        except Exception:
            continue
    return []


def _resolve_mapped_entry(raw_str, orig_max_dir, collect_root, exact_map, bname_map):
    """元のパス文字列（相対・絶対・シンボリックパス含む）から収集先パスエントリを引く"""
    clean = (raw_str or "").strip().replace("\\", "/")
    if not clean:
        return None

    cands = []
    try:
        resolved = str(rt.pathConfig.resolvePathSymbols(raw_str)).replace("\\", "/")
        if resolved:
            cands.append(resolved)
    except Exception:
        pass

    if os.path.isabs(clean):
        cands.append(clean)
    else:
        if orig_max_dir:
            cands.append(os.path.join(orig_max_dir, clean))
        cands.append(os.path.join(collect_root, clean))

    for c in cands:
        k = norm_key(c)
        if k in exact_map:
            return exact_map[k]

    bname = os.path.basename(clean).lower()
    return bname_map.get(bname)


def _save_relinked_scene_in_process(
    dest_scene_path,
    collect_root,
    orig_max_dir,
    create_project,
    use_subfolders,
    was_modified,
    asset_map,
    asset_bname_map,
    xref_map,
    xref_bname_map,
):
    """
    外部プロセス(3dsmaxbatch.exe)を起動せず、現在の3ds Maxプロセス内で
    Bitmaptexture・XRef・ATSOpsのリンクを一時書き換えしてコピー先へ保存し、
    finally で作業中シーンのプロジェクト・全パス・未保存フラグを完全に復元する。
    """
    orig_project = ""
    try:
        orig_project = str(rt.pathConfig.getCurrentProjectFolder() or "")
    except Exception:
        pass

    orig_ats_silent = False
    try:
        orig_ats_silent = bool(rt.ATSOps.Silent)
    except Exception:
        pass

    restore_xref_scenes = []  # (idx, orig_raw_filename)
    restore_xref_objs = []    # (idx, orig_srcFileName)
    restore_bmps = []         # (bmp_node, orig_raw_filename)
    restore_ats_dirs = []     # (retargeted_abs_path, orig_dir_win)

    rt.disableSceneRedraw()
    try:
        try:
            rt.ATSOps.Silent = True
        except Exception:
            pass

        with pymxs.undo(False):
            # 1. プロジェクトフォルダを一時的に収集先へ切り替え（相対パス .\maps / .\scenes 解決用）
            if create_project and os.path.isdir(collect_root):
                try:
                    rt.pathConfig.setCurrentProjectFolder(to_win_path(collect_root))
                except Exception:
                    pass

            # 2. XRef Scene のパスを一時書き換え
            try:
                x_count = int(rt.xrefs.getXRefFileCount())
                for idx in range(1, x_count + 1):
                    x_item = rt.xrefs.getXRefFile(idx)
                    raw_x = str(x_item.filename or "")
                    if not raw_x:
                        continue
                    entry = _resolve_mapped_entry(raw_x, orig_max_dir, collect_root, xref_map, xref_bname_map)
                    if entry:
                        new_x = entry["rel"] if (create_project and use_subfolders) else entry["abs"]
                        restore_xref_scenes.append((idx, raw_x))
                        x_item.filename = to_win_path(new_x)
            except Exception:
                pass

            # 3. XRef Object のパスを一時書き換え
            try:
                rec_count = int(rt.objXRefMgr.recordCount)
                for idx in range(1, rec_count + 1):
                    rec = rt.objXRefMgr.GetRecord(idx)
                    raw_x = str(rec.srcFileName or "")
                    if not raw_x:
                        continue
                    entry = _resolve_mapped_entry(raw_x, orig_max_dir, collect_root, xref_map, xref_bname_map)
                    if entry:
                        new_x = entry["rel"] if (create_project and use_subfolders) else entry["abs"]
                        restore_xref_objs.append((idx, raw_x))
                        rec.srcFileName = to_win_path(new_x)
            except Exception:
                pass

            # 4. Bitmaptexture の filename を直接書き換え（テクスチャ・IFL・UDIMを確実にリリンク）
            handled_bmp_keys = set()
            try:
                for bmp in list(rt.getClassInstances(rt.Bitmaptexture)):
                    raw_bmp = str(bmp.filename or "")
                    if not raw_bmp:
                        continue
                    entry = _resolve_mapped_entry(raw_bmp, orig_max_dir, collect_root, asset_map, asset_bname_map)
                    if entry:
                        restore_bmps.append((bmp, raw_bmp))
                        handled_bmp_keys.add(norm_key(entry["abs"]))
                        abs_target = to_win_path(entry["abs"])
                        rel_target = to_win_path(entry["rel"])
                        if "<UDIM>" not in abs_target and os.path.isfile(abs_target):
                            bmp.filename = abs_target
                        if create_project and use_subfolders:
                            bmp.filename = rel_target
                        else:
                            bmp.filename = abs_target
            except Exception:
                pass

            # 5. Bitmaptexture 以外の外部アセット（IES・キャッシュ・プロキシ・オーディオ等）を ATSOps でリターゲット
            try:
                rt.ATSOps.Refresh()
                ats_files = rt.Array()
                rt.ATSOps.GetFiles(pymxs.byref(ats_files))

                for raw_ats in list(ats_files):
                    orig_ats_str = str(raw_ats or "")
                    if not orig_ats_str or not rt.ATSOps.IsInputFile(orig_ats_str):
                        continue

                    entry = _resolve_mapped_entry(orig_ats_str, orig_max_dir, collect_root, asset_map, asset_bname_map)
                    if not entry:
                        continue

                    if norm_key(entry["abs"]) in handled_bmp_keys:
                        continue

                    abs_target_win = to_win_path(entry["abs"])
                    target_dir = os.path.dirname(abs_target_win)

                    try:
                        resolved_orig = str(rt.pathConfig.resolvePathSymbols(orig_ats_str))
                    except Exception:
                        resolved_orig = orig_ats_str
                    orig_dir_win = to_win_path(os.path.dirname(resolved_orig))

                    if target_dir and orig_dir_win and norm_key(target_dir) != norm_key(orig_dir_win):
                        try:
                            rt.ATSOps.ClearSelection()
                            rt.ATSOps.SelectFiles(rt.Array(orig_ats_str))
                            rt.ATSOps.RetargetSelection(target_dir)
                            restore_ats_dirs.append((abs_target_win, orig_dir_win))
                        except Exception:
                            pass
            except Exception:
                pass

            # 6. コピー先へシーンを書き出し
            try:
                rt.ATSOps.Refresh()
            except Exception:
                pass
            rt.saveMaxFile(to_win_path(dest_scene_path), useNewFile=False, quiet=True)

    finally:
        # 作業中シーンのすべての状態・プロジェクト・パスを完全復元
        try:
            with pymxs.undo(False):
                # 先にプロジェクトフォルダを元に戻す（相対パス解決の基準を復元）
                if orig_project:
                    try:
                        rt.pathConfig.setCurrentProjectFolder(orig_project)
                    except Exception:
                        pass

                for idx, orig_raw in reversed(restore_xref_objs):
                    try:
                        rt.objXRefMgr.GetRecord(idx).srcFileName = orig_raw
                    except Exception:
                        pass

                for idx, orig_raw in reversed(restore_xref_scenes):
                    try:
                        rt.xrefs.getXRefFile(idx).filename = orig_raw
                    except Exception:
                        pass

                for bmp, orig_raw in reversed(restore_bmps):
                    try:
                        bmp.filename = orig_raw
                    except Exception:
                        pass

                for retargeted_abs, orig_dir_win in reversed(restore_ats_dirs):
                    try:
                        rt.ATSOps.ClearSelection()
                        rt.ATSOps.SelectFiles(rt.Array(retargeted_abs))
                        rt.ATSOps.RetargetSelection(orig_dir_win)
                    except Exception:
                        pass

                try:
                    rt.ATSOps.Refresh()
                except Exception:
                    pass

                try:
                    rt.setSaveRequired(was_modified)
                except Exception:
                    pass
        finally:
            try:
                rt.ATSOps.Silent = orig_ats_silent
            except Exception:
                pass
            rt.enableSceneRedraw()


def collect_scene_files(
    parent_dir,
    folder_name,
    collect_assets=True,
    collect_xrefs=True,
    create_project=True,
    use_subfolders=True,
    overwrite=False,
    progress_cb=None,
):
    """
    現在の3ds Maxシーンを完全非破壊かつ超高速に新しいフォルダへ収集する。
    """
    def report_progress(pct, msg_key):
        if progress_cb:
            progress_cb(pct, tr(msg_key))

    if not parent_dir or not os.path.isdir(parent_dir):
        raise RuntimeError(tr("有効な保存先フォルダを指定してください。"))

    safe_folder = re.sub(r'[<>:"/\\|?*]', "_", folder_name.strip())
    if not safe_folder:
        raise RuntimeError(tr("収集フォルダ名を入力してください。"))

    orig_max_dir = str(rt.maxFilePath or "").rstrip("\\/").replace("\\", "/")
    orig_max_name = str(rt.maxFileName or "")
    orig_scene_full = os.path.join(orig_max_dir, orig_max_name).replace("\\", "/") if orig_max_name else ""
    was_modified = bool(rt.getSaveRequired())

    collect_root = os.path.join(parent_dir, safe_folder).replace("\\", "/")
    if os.path.exists(collect_root) and os.listdir(collect_root):
        if not overwrite:
            raise RuntimeError(tr("既に空でない同名フォルダが存在します:\n{path}").format(path=collect_root))
        protected = _gather_current_protected_paths()
        if _is_unsafe_overwrite_target(collect_root, protected):
            raise RuntimeError(tr("元データを含むフォルダは上書きできません:\n{path}").format(path=collect_root))
        shutil.rmtree(collect_root)

    os.makedirs(collect_root, exist_ok=True)

    scenes_dir = os.path.join(collect_root, "scenes").replace("\\", "/") if use_subfolders else collect_root
    maps_dir = os.path.join(collect_root, "maps").replace("\\", "/") if use_subfolders else collect_root
    os.makedirs(scenes_dir, exist_ok=True)
    os.makedirs(maps_dir, exist_ok=True)

    scene_filename = orig_max_name if orig_max_name else "untitled.max"
    dest_scene_path = os.path.join(scenes_dir, scene_filename).replace("\\", "/")

    copied_files_map = {}     # norm_key(src) -> dst_abs_path
    asset_repath_map = {}     # norm_key(src) -> {"abs": ..., "rel": ...}
    asset_bname_map = {}      # lower(basename) -> {"abs": ..., "rel": ...}
    xref_repath_map = {}      # norm_key(src_xref) -> {"abs": ..., "rel": ...}
    xref_bname_map = {}       # lower(basename) -> {"abs": ..., "rel": ...}

    used_scene_names = {scene_filename.lower()}
    used_map_names = set()
    copied_count = 0
    missing_files = []
    missing_seen = set()

    def add_missing(p):
        k = p.lower()
        if k not in missing_seen:
            missing_seen.add(k)
            missing_files.append(p)

    def get_unique_dest_path(target_dir, src_path, used_set):
        base_name = os.path.basename(src_path)
        stem, ext = os.path.splitext(base_name)
        candidate = base_name
        counter = 1
        while candidate.lower() in used_set:
            candidate = f"{stem}_{counter}{ext}"
            counter += 1
        used_set.add(candidate.lower())
        return os.path.join(target_dir, candidate).replace("\\", "/")

    def make_path_entry(dst_abs_path, folder_kind):
        """3ds Max プロジェクトルート (.mxp) 基準の相対パス (.\maps\... / .\scenes\...) と絶対パスを返す"""
        bname = os.path.basename(dst_abs_path)
        abs_win = to_win_path(dst_abs_path)
        if use_subfolders:
            rel_win = f".\\maps\\{bname}" if folder_kind == "maps" else f".\\scenes\\{bname}"
        else:
            rel_win = f".\\{bname}"
        return {"abs": abs_win, "rel": rel_win}

    if create_project:
        write_minimal_mxp(collect_root, safe_folder)

    # ------------------------------------------------------------------
    # 1. XRef (外部参照シーン / オブジェクト) の収集
    # ------------------------------------------------------------------
    report_progress(20, "XRef (外部参照) をスキャン・収集中...")
    xref_orig_norm_set = set()
    raw_xref_paths = []

    xref_count = int(rt.xrefs.getXRefFileCount())
    for idx in range(1, xref_count + 1):
        raw_x = str(rt.xrefs.getXRefFile(idx).filename or "")
        if raw_x:
            raw_xref_paths.append(raw_x)

    try:
        rec_count = int(rt.objXRefMgr.recordCount)
        for idx in range(1, rec_count + 1):
            raw_x = str(rt.objXRefMgr.GetRecord(idx).srcFileName or "")
            if raw_x:
                raw_xref_paths.append(raw_x)
    except Exception:
        pass

    for raw_xref in raw_xref_paths:
        resolved_xref = str(rt.pathConfig.resolvePathSymbols(raw_xref)).replace("\\", "/")
        xk = norm_key(resolved_xref)
        xref_orig_norm_set.add(xk)

        if not collect_xrefs:
            continue

        if not os.path.isfile(resolved_xref):
            add_missing(resolved_xref)
            continue

        if xk not in copied_files_map:
            dst_xref = get_unique_dest_path(scenes_dir, resolved_xref, used_scene_names)
            shutil.copy2(resolved_xref, dst_xref)
            entry = make_path_entry(dst_xref, "scenes")
            copied_files_map[xk] = dst_xref
            xref_repath_map[xk] = entry
            xref_bname_map.setdefault(os.path.basename(resolved_xref).lower(), entry)
            copied_count += 1

    # ------------------------------------------------------------------
    # 2. ATSOps + Bitmaptexture 直接走査による外部アセット収集（二重保険）
    # ------------------------------------------------------------------
    report_progress(45, "テクスチャ・外部アセットを収集中...")
    if collect_assets:
        raw_asset_candidates = []
        seen_raw_candidates = set()

        # 2A. ATSOps から取得
        try:
            rt.ATSOps.Refresh()
            ats_files = rt.Array()
            rt.ATSOps.GetFiles(pymxs.byref(ats_files))
            for raw_item in list(ats_files):
                s = str(raw_item or "")
                if s and rt.ATSOps.IsInputFile(s) and s not in seen_raw_candidates:
                    seen_raw_candidates.add(s)
                    raw_asset_candidates.append(s)
        except Exception:
            pass

        # 2B. シーン内の全 Bitmaptexture から直接取得（ATSOps 漏れ対策）
        try:
            for bmp in list(rt.getClassInstances(rt.Bitmaptexture)):
                s = str(bmp.filename or "")
                if s and s not in seen_raw_candidates:
                    seen_raw_candidates.add(s)
                    raw_asset_candidates.append(s)
        except Exception:
            pass

        for orig_ats_str in raw_asset_candidates:
            resolved_str = str(rt.pathConfig.resolvePathSymbols(orig_ats_str)).replace("\\", "/")
            rk = norm_key(resolved_str)

            # シーン自身およびXRefシーンはスキップ
            if orig_scene_full and rk == norm_key(orig_scene_full):
                continue
            if rk in xref_orig_norm_set:
                continue

            matched_files = expand_wildcard_files(resolved_str)
            if not matched_files:
                add_missing(resolved_str)
                continue

            # ケースA: UDIM テクスチャ (<UDIM>)
            if "<UDIM>" in resolved_str:
                for mf in matched_files:
                    mk = norm_key(mf)
                    if mk not in copied_files_map:
                        dst_mf = os.path.join(maps_dir, os.path.basename(mf)).replace("\\", "/")
                        used_map_names.add(os.path.basename(dst_mf).lower())
                        shutil.copy2(mf, dst_mf)
                        entry_mf = make_path_entry(dst_mf, "maps")
                        copied_files_map[mk] = dst_mf
                        asset_repath_map[mk] = entry_mf
                        asset_bname_map.setdefault(os.path.basename(mf).lower(), entry_mf)
                        copied_count += 1

                base_pattern = os.path.basename(resolved_str)
                pattern_entry = {
                    "abs": to_win_path(os.path.join(maps_dir, base_pattern)),
                    "rel": f".\\maps\\{base_pattern}" if use_subfolders else f".\\{base_pattern}",
                }
                asset_repath_map[rk] = pattern_entry
                asset_bname_map.setdefault(base_pattern.lower(), pattern_entry)

            # ケースB: IFL (Image File List 連番テクスチャ)
            elif resolved_str.lower().endswith(".ifl"):
                ifl_src = matched_files[0]
                ik = norm_key(ifl_src)
                if ik not in copied_files_map:
                    ifl_dir = os.path.dirname(ifl_src)
                    dst_ifl = get_unique_dest_path(maps_dir, ifl_src, used_map_names)
                    lines = read_text_lines_fallback(ifl_src)
                    new_ifl_lines = []

                    for line in lines:
                        stripped = line.strip()
                        if not stripped or stripped.startswith(";"):
                            new_ifl_lines.append(line)
                            continue

                        parts = stripped.split()
                        frame_rel = parts[0].strip('"')
                        suffix_args = (" " + " ".join(parts[1:])) if len(parts) > 1 else ""

                        frame_full = (
                            frame_rel.replace("\\", "/")
                            if os.path.isabs(frame_rel)
                            else os.path.join(ifl_dir, frame_rel).replace("\\", "/")
                        )
                        if os.path.isfile(frame_full):
                            fk = norm_key(frame_full)
                            if fk not in copied_files_map:
                                dst_frame = get_unique_dest_path(maps_dir, frame_full, used_map_names)
                                shutil.copy2(frame_full, dst_frame)
                                copied_files_map[fk] = dst_frame
                                copied_count += 1
                            else:
                                dst_frame = copied_files_map[fk]
                            new_ifl_lines.append(f"{os.path.basename(dst_frame)}{suffix_args}\n")
                        else:
                            add_missing(frame_full)
                            new_ifl_lines.append(line)

                    with open(dst_ifl, "w", encoding="utf-8") as f_ifl:
                        f_ifl.writelines(new_ifl_lines)

                    entry_ifl = make_path_entry(dst_ifl, "maps")
                    copied_files_map[ik] = dst_ifl
                    asset_repath_map[ik] = entry_ifl
                    asset_bname_map.setdefault(os.path.basename(ifl_src).lower(), entry_ifl)
                    copied_count += 1

            # ケースC: 通常の単一ファイル
            else:
                single_src = matched_files[0]
                sk = norm_key(single_src)
                if sk not in copied_files_map:
                    dst_single = get_unique_dest_path(maps_dir, single_src, used_map_names)
                    shutil.copy2(single_src, dst_single)
                    entry_single = make_path_entry(dst_single, "maps")
                    copied_files_map[sk] = dst_single
                    asset_repath_map[sk] = entry_single
                    asset_bname_map.setdefault(os.path.basename(single_src).lower(), entry_single)
                    copied_count += 1

    # ------------------------------------------------------------------
    # 3. インプロセス高速リターゲット＆非破壊シーン書き出し
    # ------------------------------------------------------------------
    report_progress(75, "リンクを書き換えてシーンを保存中...")
    _save_relinked_scene_in_process(
        dest_scene_path=dest_scene_path,
        collect_root=collect_root,
        orig_max_dir=orig_max_dir,
        create_project=create_project,
        use_subfolders=use_subfolders,
        was_modified=was_modified,
        asset_map=asset_repath_map,
        asset_bname_map=asset_bname_map,
        xref_map=xref_repath_map,
        xref_bname_map=xref_bname_map,
    )

    report_progress(100, "待機中...")

    return collect_root, copied_count, missing_files


class CollectFilesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self._build_ui()
        self._set_defaults()
        self._retranslate_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # 言語切り替えバー (日本語 / English)
        lang_row = QtWidgets.QHBoxLayout()
        lang_row.setSpacing(2)
        lang_row.addStretch()

        self.btn_ja = QtWidgets.QPushButton("日本語")
        self.btn_en = QtWidgets.QPushButton("English")
        for btn in (self.btn_ja, self.btn_en):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedHeight(22)
            btn.setMinimumWidth(68)

        cur_lang = get_lang()
        self.btn_ja.setChecked(cur_lang == "JA")
        self.btn_en.setChecked(cur_lang == "EN")

        self.btn_ja.clicked.connect(lambda: self._on_change_language("JA"))
        self.btn_en.clicked.connect(lambda: self._on_change_language("EN"))

        lang_row.addWidget(self.btn_ja)
        lang_row.addWidget(self.btn_en)
        layout.addLayout(lang_row)

        # 1. 保存先親フォルダ
        self.dir_group = QtWidgets.QGroupBox()
        dir_form = QtWidgets.QFormLayout(self.dir_group)

        path_row = QtWidgets.QHBoxLayout()
        self.dir_edit = QtWidgets.QLineEdit()
        self.browse_btn = QtWidgets.QPushButton()
        self.browse_btn.setFixedWidth(78)
        self.browse_btn.clicked.connect(self._browse_dir)
        path_row.addWidget(self.dir_edit)
        path_row.addWidget(self.browse_btn)

        self.lbl_dest_dir = QtWidgets.QLabel()
        dir_form.addRow(self.lbl_dest_dir, path_row)

        self.lbl_folder_name = QtWidgets.QLabel()
        self.folder_name_edit = QtWidgets.QLineEdit()
        dir_form.addRow(self.lbl_folder_name, self.folder_name_edit)
        layout.addWidget(self.dir_group)

        # 2. 収集オプション
        self.opt_group = QtWidgets.QGroupBox()
        opt_layout = QtWidgets.QVBoxLayout(self.opt_group)

        self.chk_assets = QtWidgets.QCheckBox()
        self.chk_assets.setChecked(True)

        self.chk_xrefs = QtWidgets.QCheckBox()
        self.chk_xrefs.setChecked(True)

        self.chk_subfolders = QtWidgets.QCheckBox()
        self.chk_subfolders.setChecked(True)

        self.chk_project = QtWidgets.QCheckBox()
        self.chk_project.setChecked(True)

        self.chk_open_folder = QtWidgets.QCheckBox()
        self.chk_open_folder.setChecked(True)

        opt_layout.addWidget(self.chk_assets)
        opt_layout.addWidget(self.chk_xrefs)
        opt_layout.addWidget(self.chk_subfolders)
        opt_layout.addWidget(self.chk_project)
        opt_layout.addWidget(self.chk_open_folder)
        layout.addWidget(self.opt_group)

        # 進行状況バー
        self.status_label = QtWidgets.QLabel()
        self.status_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        # 3. 実行ボタン
        btn_row = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton()
        self.run_btn.setMinimumHeight(34)
        self.run_btn.setStyleSheet("font-weight: bold;")
        self.run_btn.clicked.connect(self._on_collect)

        self.close_btn = QtWidgets.QPushButton()
        self.close_btn.setMinimumHeight(34)
        self.close_btn.setFixedWidth(90)
        self.close_btn.clicked.connect(self.close)

        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def _on_change_language(self, lang):
        set_lang(lang)
        self._retranslate_ui()

    def _retranslate_ui(self):
        self.setWindowTitle(tr("CF3F - Collect Files for 3ds Max (ファイル収集)"))
        self.dir_group.setTitle(tr("1. 保存先とフォルダ名"))
        self.dir_edit.setPlaceholderText(tr("保存先の親フォルダを選択..."))
        self.browse_btn.setText(tr("参照..."))
        self.lbl_dest_dir.setText(tr("保存先フォルダ:"))
        self.lbl_folder_name.setText(tr("新規フォルダ名:"))

        self.opt_group.setTitle(tr("2. 収集オプション"))
        self.chk_assets.setText(tr("テクスチャ・キャッシュ等の外部ファイルを収集する"))
        self.chk_xrefs.setText(tr("XRef (外部参照シーン / オブジェクト) を収集する"))
        self.chk_subfolders.setText(tr("サブフォルダに分けて整理する (scenes / maps)"))
        self.chk_project.setText(tr("プロジェクト設定 (.mxp) を生成して相対パス化する（推奨）"))
        self.chk_open_folder.setText(tr("収集完了後にフォルダを開く"))

        self.status_label.setText(tr("待機中..."))
        self.run_btn.setText(tr("収集を実行 (Collect Files)"))
        self.close_btn.setText(tr("閉じる"))

    def _set_defaults(self):
        max_dir = str(rt.maxFilePath or "")
        max_name = str(rt.maxFileName or "")
        if max_dir and max_name:
            self.dir_edit.setText(max_dir.rstrip("\\/").replace("\\", "/"))
            stem = os.path.splitext(max_name)[0]
            self.folder_name_edit.setText(f"{stem}_Collected")
        else:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop").replace("\\", "/")
            self.dir_edit.setText(desktop)
            self.folder_name_edit.setText("MaxScene_Collected")

    def _browse_dir(self):
        start_dir = self.dir_edit.text() or os.path.expanduser("~")
        selected = QtWidgets.QFileDialog.getExistingDirectory(self, tr("保存先フォルダを選択"), start_dir)
        if selected:
            self.dir_edit.setText(selected.replace("\\", "/"))

    def _update_progress(self, pct, status_text):
        self.progress_bar.setValue(pct)
        self.status_label.setText(status_text)
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)

    def _on_collect(self):
        parent_dir = self.dir_edit.text()
        folder_name = self.folder_name_edit.text()
        allow_overwrite = False

        if not parent_dir or not os.path.isdir(parent_dir):
            QtWidgets.QMessageBox.critical(self, tr("エラー"), tr("有効な保存先フォルダを指定してください。"))
            return

        safe_folder = re.sub(r'[<>:"/\\|?*]', "_", folder_name.strip())
        if not safe_folder:
            QtWidgets.QMessageBox.critical(self, tr("エラー"), tr("収集フォルダ名を入力してください。"))
            return

        target_root = os.path.join(parent_dir, safe_folder).replace("\\", "/")
        if os.path.exists(target_root) and os.listdir(target_root):
            protected = _gather_current_protected_paths()
            if _is_unsafe_overwrite_target(target_root, protected):
                QtWidgets.QMessageBox.critical(
                    self,
                    tr("エラー"),
                    tr("元データを含むフォルダは上書きできません:\n{path}").format(path=target_root),
                )
                return

            ans = QtWidgets.QMessageBox.question(
                self,
                tr("上書き確認"),
                tr("既に同名のフォルダが存在します:\n{path}\n\n既存のフォルダを削除して上書きしますか？").format(path=target_root),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if ans != QtWidgets.QMessageBox.Yes:
                return
            allow_overwrite = True

        self.run_btn.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            collect_root, count, missing = collect_scene_files(
                parent_dir=parent_dir,
                folder_name=folder_name,
                collect_assets=self.chk_assets.isChecked(),
                collect_xrefs=self.chk_xrefs.isChecked(),
                create_project=self.chk_project.isChecked(),
                use_subfolders=self.chk_subfolders.isChecked(),
                overwrite=allow_overwrite,
                progress_cb=self._update_progress,
            )
        except Exception as e:
            self.progress_bar.setValue(0)
            self.status_label.setText(tr("待機中..."))
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, tr("エラー"), str(e))
            return
        finally:
            self.run_btn.setEnabled(True)
            while QtWidgets.QApplication.overrideCursor() is not None:
                QtWidgets.QApplication.restoreOverrideCursor()

        msg = tr("収集が完了しました！\n\n出力先:\n{root}\n\nコピーした外部ファイル数: {count} 件").format(
            root=collect_root, count=count
        )
        if missing:
            preview = "\n".join(missing[:5])
            extra = tr("\n...他 {count} 件").format(count=len(missing) - 5) if len(missing) > 5 else ""
            msg += tr("\n\n【注意】リンク切れのためスキップされたファイル ({count} 件):\n{preview}{extra}").format(
                count=len(missing), preview=preview, extra=extra
            )

        QtWidgets.QMessageBox.information(self, tr("CF3F 完了"), msg)
        self.progress_bar.setValue(0)

        if self.chk_open_folder.isChecked():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(collect_root))


def show():
    parent = get_max_main_window()
    if parent:
        existing = parent.findChild(QtWidgets.QDialog, WINDOW_OBJECT_NAME)
        if existing:
            existing.close()
            existing.deleteLater()

    dlg = CollectFilesDialog(parent=parent)
    dlg.show()
    return dlg


if __name__ == "__main__":
    show()
