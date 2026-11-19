# Collect Files for 3ds Max (CF3F) — Free Edition

An After Effects-style **Collect Files** tool for Autodesk 3ds Max.  
Gather your scene and its textures/external assets into a clean, portable project folder (`scenes/` and `maps/`) and auto-generate a `.mxp` project file so everything opens with relative paths on any PC.

* **Supported 3ds Max Versions:** Autodesk 3ds Max 2022 – 2027 (Windows)
* **Dependencies:** None (Pure Python 3 + `pymxs` + PySide2 / PySide6)
* **UI Languages:** English / Japanese (Switchable inside the tool window)

---

## Key Features (Free Edition)

* **Ultra-Fast In-Process Execution:** Rewrites and saves scenes directly in-process without launching external `3dsmaxbatch.exe` processes—completing typical single scenes in a fraction of a second with minimal CPU load.
* **100% Non-Destructive:** Keeps your active working scene, asset paths, current project folder, and unsaved status completely untouched.
* **Portable Relative Paths (`.mxp`):** Organizes files into `scenes/` and `maps/` and automatically generates a `.mxp` project file for hassle-free sharing across drives and machines.
* **Missing Link Detection:** Safely skips broken/missing file paths and lists them in the completion summary.
* **Bilingual UI & Easy Setup:** Switch between **English** and **Japanese** anytime, and install via drag-and-drop.

> **Scope Note:** The Free edition is designed as a lightweight baseline for standard single-scene collection. If you work with nested `.max` XRefs (XRef Scenes / XRef Objects), UDIMs, `.ifl` image sequences, or need collection reports and 1-click `.zip` packaging, check out **Collect Files for 3ds Max Pro (CF3P)** below.

---

## Free vs. Pro Comparison

| Feature | CF3F (Free) | CF3P (Pro) |
| :--- | :---: | :---: |
| Single-scene texture & external asset collection | ✅ | ✅ |
| Subfolder organization (`scenes/` & `maps/`) | ✅ | ✅ |
| Auto-generated `.mxp` project file & relative paths | ✅ | ✅ |
| 100% non-destructive & ultra-fast in-process engine | ✅ | ✅ |
| Bilingual UI (English / Japanese) + drag-and-drop installer | ✅ | ✅ |
| **Recursive nested XRef collection (`.max`, child & grandchild hierarchy)** | — | ✅ |
| **Internal path relinking inside nested XRef scenes & XRef Objects** | — | ✅ |
| **UDIM auto-expansion (`<UDIM>`, `<uvtile>`, `1001`+ tile sets)** | — | ✅ |
| **Image sequence & `.ifl` auto-expansion and internal relinking (`####`, `.ifl`)** | — | ✅ |
| **Collection audit report (`collection_report.txt`)** | — | ✅ |
| **1-click `.zip` delivery archive packaging** | — | ✅ |

### Get Collect Files for 3ds Max Pro (CF3P)
* **Gumroad (Global / English):** [https://mashitaya.gumroad.com/l/dhjmwl/6wl6aky](https://mashitaya.gumroad.com/l/dhjmwl)
* **BOOTH (Japan / 日本語):** https://yworks.booth.pm/items/9180013

---

## Repository Contents

* `collect_files_3dsmax_free.py` — Main tool script (Free Edition)
* `install_CF3F.ms` — Drag-and-drop MacroScript installer
* `README.md` — Documentation

---

## Installation

1. Download or clone this repository and extract the files into any folder. Make sure `install_CF3F.ms` and `collect_files_3dsmax_free.py` are in the **same folder**.
2. Open Autodesk 3ds Max (2022 or later) and **drag and drop `install_CF3F.ms` directly into the 3ds Max viewport**.
3. `collect_files_3dsmax_free.py` will be copied to your 3ds Max `userScripts` directory, and a MacroScript will be registered under the **`Collect Files`** category.
4. *(Optional — Add to Toolbar)* Go to **Customize > Customize User Interface > Toolbars**, select Category **`Collect Files`**, and drag **`Collect Files for 3ds Max (CF3F)`** onto any toolbar.

> **Alternative Method (if drag-and-drop is blocked by OS permissions):**  
> Go to **Scripting > Run Script...** in 3ds Max and select `install_CF3F.ms`.

---

## How to Use

1. Launch **CF3F** from your toolbar (or via **Scripting > Run Script...**).
2. *(Optional)* Use the **`日本語` / `English`** toggle at the top right to switch the UI language.
3. Choose the **Destination Folder** and **New Folder Name** (defaults to `<SceneName>_Collected`).
4. Select your options (collect external assets, organize into `scenes` / `maps`, generate `.mxp` project file, open folder after collection) and click **Collect Files**.

To verify the collected package on your own machine, go to **File > Project > Set Active Project** in 3ds Max, select the newly created output folder, open the scene inside `scenes/`, and check **Asset Tracking (`Shift + T`)**.

---

## License

MIT License — Free to use for both personal and commercial projects.

---
---

# Collect Files for 3ds Max (CF3F) — 日本語ガイド

Autodesk 3ds Max 向けの After Effects 風 **「ファイル収集（Collect Files）」** ツール（無料版）です。  
現在のシーンと使用しているテクスチャ等の外部アセットを1つのプロジェクトフォルダ（`scenes/`・`maps/`）へ一括収集し、`.mxp` プロジェクトファイルを自動生成して相対パス化することで、別のPCやドライブへ渡してもリンク切れなく開ける状態にまとめます。

* **対応バージョン:** Autodesk 3ds Max 2022 – 2027（Windows）
* **外部ライブラリ:** 不要（3ds Max 標準の Python 3 / `pymxs` / PySide2・PySide6 のみで動作）
* **UI言語:** 日本語 / English（ウィンドウ右上からいつでも切り替え可能）

---

## 主な機能（Free版）

* **超高速インプロセス処理:** 外部プロセス（`3dsmaxbatch.exe`）を起動せず現在の 3ds Max セッション内で高速に収集・リリンクを行うため、一般的な単一シーンであれば一瞬（0.1秒未満〜）で完了します。
* **100% 非破壊:** 作業中のシーンファイル、元のアセットパス、現在のプロジェクト設定、未保存状態を一切変更しません。
* **相対パス化（`.mxp` 自動生成）:** `scenes/` と `maps/` に整理したうえで `.mxp` プロジェクトファイルを自動生成します。
* **リンク切れの自動スキップ通知:** 見つからないファイルは安全にスキップし、完了ダイアログに一覧を表示します。
* **日英バイリンガルUI ＆ 簡単導入:** `install_CF3F.ms` をビューポートへドラッグ＆ドロップするだけでインストール完了します。

> **無料版の対応範囲について:**  
> Free版は日常的な単一シーンを手軽にまとめる用途に特化した軽量版です。子・孫階層までのネストされた XRef（XRef シーン・XRef オブジェクト）の再帰収集、UDIM・`.ifl` 連番の自動展開と内部リリンク、収集レポート出力、ワンクリック `.zip` 圧縮が必要な場合は、上位版の **Collect Files for 3ds Max Pro (CF3P)** をご利用ください。

---

## Free版 と Pro版 の機能比較

| 機能 | CF3F (Free版) | CF3P (Pro版) |
| :--- | :---: | :---: |
| 単一シーンのテクスチャ・外部アセット収集 | ✅ | ✅ |
| サブフォルダ整理（`scenes/`・`maps/`） | ✅ | ✅ |
| `.mxp` プロジェクト自動生成・相対パス化 | ✅ | ✅ |
| 100% 非破壊・超高速インプロセス処理 | ✅ | ✅ |
| 日英バイリンガルUI・ドラッグ＆ドロップ導入 | ✅ | ✅ |
| **ネストされた XRef の再帰収集（`.max` 子・孫階層対応）** | — | ✅ |
| **ネストされた XRef シーン・XRef オブジェクト内部パスの自動リリンク** | — | ✅ |
| **UDIM 自動展開・収集（`<UDIM>` / `<uvtile>` / `1001`番台タイル群）** | — | ✅ |
| **フレーム連番・`.ifl` の自動展開と内部リリンク（`####` / `.ifl`）** | — | ✅ |
| **収集レポート出力（`collection_report.txt`）** | — | ✅ |
| **納品用 `.zip` アーカイブ自動作成** | — | ✅ |

### Pro版（CF3P）の入手先
* **BOOTH（日本語 / 国内向け）:** https://yworks.booth.pm/items/9180013
* **Gumroad（英語 / 海外向け）:** https://mashitaya.gumroad.com/l/dhjmwl/6wl6aky

---

## インストール方法

1. リポジトリをダウンロード（または ZIP 展開）し、`install_CF3F.ms` と `collect_files_3dsmax_free.py` が**同じフォルダ内**にあることを確認します。
2. 3ds Max（2022以降）を起動し、**`install_CF3F.ms` をビューポートへドラッグ＆ドロップ**します。
3. 自動的に 3ds Max の `userScripts` フォルダへスクリプトがコピーされ、マクロが登録されます。
4. **（ツールバーへのボタン追加）** 上部メニュー **「カスタマイズ > ユーザー インタフェースをカスタマイズ > ツールバー」** を開き、カテゴリ **`Collect Files`** から **`Collect Files for 3ds Max (CF3F)`** を任意のツールバーへドラッグしてください。

> **ドラッグ＆ドロップで反応しない場合:**  
> 上部メニュー **「スクリプト > スクリプトを実行 (Scripting > Run Script...)」** から `install_CF3F.ms` を選択して実行してください。

---

## 使い方

1. ツールバーの **`CF3F`** ボタンをクリックしてウィンドウを開きます。
2. 保存先フォルダと新規フォルダ名（初期値：`<シーン名>_Collected`）を指定します。
3. 必要なオプションにチェックを入れ、**「収集を実行 (Collect Files)」** をクリックします。

※収集結果を手元で確認する場合は、3ds Max の **ファイル > プロジェクト > アクティブ プロジェクトを設定 (File > Project > Set Active Project)** から出力されたフォルダを指定し、`scenes/` 内のシーンを開いて **アセット トラッキング（`Shift + T`）** でパス解決状態をご確認ください。
