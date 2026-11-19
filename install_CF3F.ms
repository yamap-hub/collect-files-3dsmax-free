-- ===========================================================================
-- install_CF3F.ms  -  CF3F (Collect Files for 3ds Max Free) Installer
--
-- HOW TO USE
--   1. Put this file and collect_files_3dsmax_free.py in the same folder.
--   2. Drag and drop this file (install_CF3F.ms) into the 3ds Max viewport.
--   -> Copies collect_files_3dsmax_free.py to your user scripts folder,
--      registers the "CF3F" macroScript (Category: CF3F), and launches the UI.
--
-- Requires 3ds Max 2021 or later (Python 3).
-- ===========================================================================

(
    fn installCF3F =
    (
        local moduleName = "collect_files_3dsmax_free"
        local pyFileName = moduleName + ".py"
        local thisScript = getSourceFileName()
        local srcPy = ""

        if thisScript != "" and thisScript != undefined do
        (
            local candidate = (getFilenamePath thisScript) + pyFileName
            if doesFileExist candidate do
            (
                srcPy = candidate
            )
        )

        if srcPy == "" do
        (
            local picked = getOpenFileName \
                caption:"collect_files_3dsmax_free.py を選択してください / Select collect_files_3dsmax_free.py" \
                types:"Python (*.py)|*.py|All Files (*.*)|*.*"
            if picked == undefined or picked == "" do return false
            srcPy = picked
        )

        -- 1. Copy Python script to userScripts folder
        local userScriptsDir = getDir #userScripts
        makeDir userScriptsDir all:true
        local dstPy = pathConfig.appendPath userScriptsDir pyFileName

        if (toLower (pathConfig.normalizePath srcPy)) != (toLower (pathConfig.normalizePath dstPy)) do
        (
            if doesFileExist dstPy do deleteFile dstPy
            if not (copyFile srcPy dstPy) do
            (
                messageBox ("scripts フォルダへのコピーに失敗しました:\n" + dstPy + "\n\nFailed to copy script to userScripts folder.") title:"CF3F Installer"
                return false
            )
        )

        -- 2. Build Python loader snippet that guarantees userScriptsDir is in sys.path
        local safeScriptsDir = substituteString userScriptsDir "\\" "/"
        local pyRunCode = "import sys, importlib; "
        pyRunCode += "p = '" + safeScriptsDir + "'; "
        pyRunCode += "sys.path.insert(0, p) if p not in sys.path else None; "
        pyRunCode += "sys.modules.pop('collect_files_3dsmax_free', None); "
        pyRunCode += "importlib.invalidate_caches(); "
        pyRunCode += "import collect_files_3dsmax_free; "
        pyRunCode += "collect_files_3dsmax_free.show()"

        -- 3. Remove legacy CFM macro if present, then create & evaluate CF3F MacroScript
        local userMacrosDir = getDir #userMacros
        makeDir userMacrosDir all:true
        local oldMcrPath = pathConfig.appendPath userMacrosDir "CFM-CollectFiles3dsMax.mcr"
        if doesFileExist oldMcrPath do deleteFile oldMcrPath

        local mcrPath = pathConfig.appendPath userMacrosDir "CF3F-CollectFiles3dsMax.mcr"

        local f = createFile mcrPath
        if f != undefined then
        (
            format "macroScript CF3F_CollectFiles\n" to:f
            format "    category:\"CF3F\"\n" to:f
            format "    buttonText:\"CF3F\"\n" to:f
            format "    toolTip:\"CF3F - Collect Files for 3ds Max (Free)\"\n" to:f
            format "(\n" to:f
            format "    on execute do\n" to:f
            format "    (\n" to:f
            format "        python.Execute \"%\"\n" pyRunCode to:f
            format "    )\n" to:f
            format ")\n" to:f
            close f
            fileIn mcrPath
        )
        else
        (
            messageBox ("MacroScript の作成に失敗しました:\n" + mcrPath + "\n\nFailed to create MacroScript.") title:"CF3F Installer"
            return false
        )

        -- 4. Notify user & launch CF3F window
        local msg = "インストールが完了しました！\n"
        msg += "・scripts フォルダへコピーしました:\n  " + dstPy + "\n"
        msg += "・ツールバーへボタンを追加するには:\n  [カスタマイズ > ユーザー インタフェースをカスタマイズ > ツールバー > カテゴリ: CF3F]\n  から「CF3F」をツールバーへドラッグしてください。\n\n"
        msg += "Installation complete!\n"
        msg += "- Copied script to userScripts folder.\n"
        msg += "- To add a toolbar button: [Customize > Customize User Interface > Toolbars > Category: CF3F] and drag 'CF3F' onto any toolbar."

        messageBox msg title:"CF3F Installer"

        python.Execute pyRunCode
        return true
    )

    installCF3F()
)