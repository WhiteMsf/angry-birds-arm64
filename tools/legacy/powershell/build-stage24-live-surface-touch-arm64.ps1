param(
    [ValidateSet('wvga854','native')]
    [string]$DisplayMode = 'wvga854',

    [ValidateSet('Audit','Release')]
    [string]$BuildFlavor = 'Audit',

    [string]$ReleaseKeystore = '',
    [string]$ReleaseAlias = 'angry-birds-release',
    [string]$ReleasePasswordEnv = 'ANGRY_BIRDS_RELEASE_STOREPASS',

    [string]$OriginalRoot = '',
    [string]$AndroidSdk = '',

    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($AndroidSdk)) {
    if (![string]::IsNullOrWhiteSpace($env:ANDROID_SDK_ROOT)) {
        $AndroidSdk = $env:ANDROID_SDK_ROOT
    } elseif (![string]::IsNullOrWhiteSpace($env:ANDROID_HOME)) {
        $AndroidSdk = $env:ANDROID_HOME
    } else {
        $AndroidSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    }
}

$sdk = [IO.Path]::GetFullPath($AndroidSdk)
$ndkRoot = Join-Path $sdk 'ndk'
$vendor = Join-Path $root 'vendor'
$luaArchive = Join-Path $vendor 'lua-5.1.5.tar.gz'
$luaDir = Join-Path $vendor 'lua-5.1.5'
$boxArchive = Join-Path $vendor 'box2d-v2.1.2-pinned.tar.gz'
$boxDir = Join-Path $vendor 'box2d-v2.1.2'
$build = Join-Path $root 'b24'
$outputDir = Join-Path $root 'stage24-output'
$apkWork = Join-Path $root 'stage24-apk-work'
if ($BuildFlavor -eq 'Release') {
    $packageName = 'dev.angryarm64.angrybirds'
} else {
    $packageName = 'dev.angryarm64.stage24'
}
$component = "$packageName/android.app.NativeActivity"

if ([string]::IsNullOrWhiteSpace($OriginalRoot)) {
    if (![string]::IsNullOrWhiteSpace($env:ANGRY_BIRDS_ORIGINAL_ROOT)) {
        $OriginalRoot = $env:ANGRY_BIRDS_ORIGINAL_ROOT
    } else {
        $OriginalRoot = Join-Path $env:USERPROFILE 'Downloads\angry-re'
    }
}

$angryReRoot = [IO.Path]::GetFullPath($OriginalRoot)
$dataRoot = Join-Path $angryReRoot 'assets\data'
$scripts = Join-Path $dataRoot 'scripts'
$level1 = Join-Path $dataRoot 'levels\pack1\Level1.lua'
$level57 = Join-Path $dataRoot 'levels\pack1\Level57.lua'
$level53 = Join-Path $dataRoot 'levels\pack1\Level53.lua'
$level3 = Join-Path $dataRoot 'levels\pack1\Level3.lua'
$level6 = Join-Path $dataRoot 'levels\pack1\Level6.lua'
$level2 = Join-Path $dataRoot 'levels\pack1\Level2.lua'
$level4 = Join-Path $dataRoot 'levels\pack1\Level4.lua'
$level5 = Join-Path $dataRoot 'levels\pack1\Level5.lua'
$level7 = Join-Path $dataRoot 'levels\pack1\Level7.lua'
$level8 = Join-Path $dataRoot 'levels\pack1\Level8.lua'
$level9 = Join-Path $dataRoot 'levels\pack1\Level9.lua'
$level13 = Join-Path $dataRoot 'levels\pack1\Level13.lua'
$level10 = Join-Path $dataRoot 'levels\pack1\Level10.lua'
$level39 = Join-Path $dataRoot 'levels\pack1\Level39.lua'
$level12 = Join-Path $dataRoot 'levels\pack1\Level12.lua'
$level15 = Join-Path $dataRoot 'levels\pack1\Level15.lua'
$level17 = Join-Path $dataRoot 'levels\pack1\Level17.lua'
$level14 = Join-Path $dataRoot 'levels\pack1\Level14.lua'
$level16 = Join-Path $dataRoot 'levels\pack1\Level16.lua'
$level23 = Join-Path $dataRoot 'levels\pack1\Level23.lua'
$level44 = Join-Path $dataRoot 'levels\pack1\Level44.lua'
# Stage 24.35.0: untouched Poached Eggs theme 2 transport through 2-5.
$level52p2 = Join-Path $dataRoot 'levels\pack2\Level52.lua'
$level34p2 = Join-Path $dataRoot 'levels\pack2\Level34.lua'
$level42p2 = Join-Path $dataRoot 'levels\pack2\Level42.lua'
$level24p2 = Join-Path $dataRoot 'levels\pack2\Level24.lua'
$level88p2 = Join-Path $dataRoot 'levels\pack2\Level88.lua'
# Stage 24.36.0: continue untouched Poached Eggs theme2 through White debut at 2-14.
$level36p2 = Join-Path $dataRoot 'levels\pack2\Level36.lua'
$level31p2 = Join-Path $dataRoot 'levels\pack2\Level31.lua'
$level21p2 = Join-Path $dataRoot 'levels\pack2\Level21.lua'
$level41p2 = Join-Path $dataRoot 'levels\pack2\Level41.lua'
$level76p2 = Join-Path $dataRoot 'levels\pack2\Level76.lua'
$level38p2 = Join-Path $dataRoot 'levels\pack2\Level38.lua'
$level35p2 = Join-Path $dataRoot 'levels\pack2\Level35.lua'
$level20p2 = Join-Path $dataRoot 'levels\pack2\Level20.lua'
$level26p2 = Join-Path $dataRoot 'levels\pack2\Level26.lua'
# Stage 24.36.1: close the second 21-level Poached Eggs page using untouched Pack2 order.
$level66p2 = Join-Path $dataRoot 'levels\pack2\Level66.lua'
$level85p2 = Join-Path $dataRoot 'levels\pack2\Level85.lua'
$level27p2 = Join-Path $dataRoot 'levels\pack2\Level27.lua'
$level32p2 = Join-Path $dataRoot 'levels\pack2\Level32.lua'
$level72p2 = Join-Path $dataRoot 'levels\pack2\Level72.lua'
$level90p2 = Join-Path $dataRoot 'levels\pack2\Level90.lua'
$level96p2 = Join-Path $dataRoot 'levels\pack2\Level96.lua'
# Stage 24.38.0: enter Poached Eggs page/theme 3 through 3-5.
$level43p3 = Join-Path $dataRoot 'levels\pack3\Level43.lua'
$level77p3 = Join-Path $dataRoot 'levels\pack3\Level77.lua'
$level28p3 = Join-Path $dataRoot 'levels\pack3\Level28.lua'
$level29p3 = Join-Path $dataRoot 'levels\pack3\Level29.lua'
$level87p3 = Join-Path $dataRoot 'levels\pack3\Level87.lua'
# Stage 24.38.1: close Poached Eggs page/theme 3 through 3-21 using untouched Pack3 order.
$level18p3 = Join-Path $dataRoot 'levels\pack3\Level18.lua'
$level91p3 = Join-Path $dataRoot 'levels\pack3\Level91.lua'
$level49p3 = Join-Path $dataRoot 'levels\pack3\Level49.lua'
$level45p3 = Join-Path $dataRoot 'levels\pack3\Level45.lua'
$level75p3 = Join-Path $dataRoot 'levels\pack3\Level75.lua'
$level51p3 = Join-Path $dataRoot 'levels\pack3\Level51.lua'
$level30p3 = Join-Path $dataRoot 'levels\pack3\Level30.lua'
$level79p3 = Join-Path $dataRoot 'levels\pack3\Level79.lua'
$level40p3 = Join-Path $dataRoot 'levels\pack3\Level40.lua'
$level59p3 = Join-Path $dataRoot 'levels\pack3\Level59.lua'
$level58p3 = Join-Path $dataRoot 'levels\pack3\Level58.lua'
$level95p3 = Join-Path $dataRoot 'levels\pack3\Level95.lua'
$level82p3 = Join-Path $dataRoot 'levels\pack3\Level82.lua'
$level22p3 = Join-Path $dataRoot 'levels\pack3\Level22.lua'
$level89p3 = Join-Path $dataRoot 'levels\pack3\Level89.lua'
$level81p3 = Join-Path $dataRoot 'levels\pack3\Level81.lua'
# Stage 24.39.0: enter Mighty Hoax page/theme 4 through 4-5 using untouched Pack4 order.
$levelP2_103p4 = Join-Path $dataRoot 'levels\pack4\LevelP2_103.lua'
$levelP2_91p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_91.lua'
$levelP2_65p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_65.lua'
$levelP2_96p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_96.lua'
$levelP2_69p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_69.lua'
# Stage 24.40.1: continue untouched Mighty Hoax page 1 through 4-10.
$levelP2_88p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_88.lua'
$levelP2_64p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_64.lua'
$levelP2_80p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_80.lua'
$levelP2_108p4 = Join-Path $dataRoot 'levels\pack4\LevelP2_108.lua'
$levelP2_85p4  = Join-Path $dataRoot 'levels\pack4\LevelP2_85.lua'
# Stage 24.40.2: close untouched Mighty Hoax page 1 through 4-21.
$levelP2_82p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_82.lua'
$levelP2_66p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_66.lua'
$levelP2_104p4    = Join-Path $dataRoot 'levels\pack4\LevelP2_104.lua'
$levelP2_210p4    = Join-Path $dataRoot 'levels\pack4\LevelP2_210.lua'
$levelP2_83p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_83.lua'
$levelP2_79p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_79.lua'
$levelP2_77p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_77.lua'
$levelP2_114p4    = Join-Path $dataRoot 'levels\pack4\LevelP2_114.lua'
$levelP2_81p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_81.lua'
$levelP2_68p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_68.lua'
$levelP2_95p4     = Join-Path $dataRoot 'levels\pack4\LevelP2_95.lua'
# Stage 24.41.0: begin Mighty Hoax page/theme 5 through 5-10 using untouched Pack5 order.
$levelP2_78p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_78.lua'
$levelP2_100p5 = Join-Path $dataRoot 'levels\pack5\LevelP2_100.lua'
$levelP2_92p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_92.lua'
$levelP2_94p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_94.lua'
$levelP2_89p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_89.lua'
$levelP2_73p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_73.lua'
$levelP2_76p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_76.lua'
$levelP2_122p5 = Join-Path $dataRoot 'levels\pack5\LevelP2_122.lua'
$levelP2_99p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_99.lua'
$levelP2_84p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_84.lua'
# Stage 24.41.1: close untouched Mighty Hoax page/theme 5 through 5-21.
$levelP2_86p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_86.lua'
$levelP2_74p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_74.lua'
$levelP2_115p5 = Join-Path $dataRoot 'levels\pack5\LevelP2_115.lua'
$levelP2_98p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_98.lua'
$levelP2_71p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_71.lua'
$levelP2_72p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_72.lua'
$levelP2_87p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_87.lua'
$levelP2_93p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_93.lua'
$levelP2_67p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_67.lua'
$levelP2_97p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_97.lua'
$levelP2_90p5  = Join-Path $dataRoot 'levels\pack5\LevelP2_90.lua'
# Stage 24.42.0: begin Danger Above page/theme 6 as one natural 15-level QA boundary.
$levelP3_212p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_212.lua'
$levelP3_134p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_134.lua'
$levelP3_162p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_162.lua'
$levelP3_271p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_271.lua'
$levelP3_224p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_224.lua'
$levelP3_253p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_253.lua'
$levelP3_225p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_225.lua'
$levelP3_232p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_232.lua'
$levelP3_150p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_150.lua'
$levelP3_211p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_211.lua'
$levelP3_223p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_223.lua'
$levelP3_226p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_226.lua'
$levelP3_215p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_215.lua'
$levelP3_220p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_220.lua'
$levelP3_231p6 = Join-Path $dataRoot 'levels\pack6\LevelP3_231.lua'
# Stage 24.45.0: resume Danger Above with page/theme 7 as one natural 15-level QA boundary.
$levelP3_166p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_166.lua'
$levelP3_237p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_237.lua'
$levelP3_216p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_216.lua'
$levelP3_298p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_298.lua'
$levelP3_303p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_303.lua'
$levelP3_214p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_214.lua'
$levelP3_159p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_159.lua'
$levelP3_164p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_164.lua'
$levelP3_299p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_299.lua'
$levelP3_302p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_302.lua'
$levelP3_219p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_219.lua'
$levelP3_163p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_163.lua'
$levelP3_160p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_160.lua'
$levelP3_161p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_161.lua'
$levelP3_304p7 = Join-Path $dataRoot 'levels\pack7\LevelP3_304.lua'
# Stage 24.45.1: close Danger Above with page/theme 8, its third 15-level page.
$levelP3_297p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_297.lua'
$levelP3_221p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_221.lua'
$levelP3_306p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_306.lua'
$levelP3_301p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_301.lua'
$levelP3_312p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_312.lua'
$levelP3_309p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_309.lua'
$levelP3_168p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_168.lua'
$levelP3_311p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_311.lua'
$levelP3_308p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_308.lua'
$levelP3_310p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_310.lua'
$levelP3_217p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_217.lua'
$levelP3_307p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_307.lua'
$levelP3_296p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_296.lua'
$levelP3_149p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_149.lua'
$levelP3_313p8 = Join-Path $dataRoot 'levels\pack8\LevelP3_313.lua'
# Stage 24.46.0: enter The Big Setup with its first 15-level page/theme9.
$levelP4_421p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_421.lua'
$levelP4_423p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_423.lua'
$levelP4_424p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_424.lua'
$levelP4_425p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_425.lua'
$levelP4_426p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_426.lua'
$levelP4_427p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_427.lua'
$levelP4_428p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_428.lua'
$levelP4_429p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_429.lua'
$levelP4_431p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_431.lua'
$levelP4_432p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_432.lua'
$levelP4_433p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_433.lua'
$levelP4_436p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_436.lua'
$levelP4_439p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_439.lua'
$levelP4_440p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_440.lua'
$levelP4_441p9 = Join-Path $dataRoot 'levels\pack9\LevelP4_441.lua'
# Stage 24.46.2: continue The Big Setup with page2 / pack10.
$levelP4_442p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_442.lua'
$levelP4_443p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_443.lua'
$levelP4_444p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_444.lua'
$levelP4_445p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_445.lua'
$levelP4_448p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_448.lua'
$levelP4_449p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_449.lua'
$levelP4_451p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_451.lua'
$levelP4_452p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_452.lua'
$levelP4_453p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_453.lua'
$levelP4_454p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_454.lua'
$levelP4_455p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_455.lua'
$levelP4_457p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_457.lua'
$levelP4_458p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_458.lua'
$levelP4_459p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_459.lua'
$levelP4_462p10 = Join-Path $dataRoot 'levels\pack10\LevelP4_462.lua'
# Stage 24.46.3: final The Big Setup page / pack11.
$levelP4_463p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_463.lua'
$levelP4_464p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_464.lua'
$levelP4_465p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_465.lua'
$levelP4_466p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_466.lua'
$levelP4_467p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_467.lua'
$levelP4_468p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_468.lua'
$levelP4_469p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_469.lua'
$levelP4_470p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_470.lua'
$levelP4_471p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_471.lua'
$levelP4_472p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_472.lua'
$levelP4_473p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_473.lua'
$levelP4_474p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_474.lua'
$levelP4_475p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_475.lua'
$levelP4_477p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_477.lua'
$levelP4_478p11 = Join-Path $dataRoot 'levels\pack11\LevelP4_478.lua'
# Stage 24.47.0: Golden Eggs gameplay levels. The untouched menu has 19 slots:
# 15 LevelGE gameplay entries plus 4 Lua-owned soundboards. Transport gameplay only;
# unlock/selectability remains wholly owned by settings.openGoldenEggLevels.
$levelGE_1 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_1.lua'
$levelGE_2 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_2.lua'
$levelGE_3 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_3.lua'
$levelGE_4 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_4.lua'
$levelGE_5 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_5.lua'
$levelGE_6 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_6.lua'
$levelGE_7 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_7.lua'
$levelGE_8 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_8.lua'
$levelGE_9 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_9.lua'
$levelGE_10 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_10.lua'
$levelGE_11 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_11.lua'
$levelGE_12 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_12.lua'
$levelGE_13 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_13.lua'
$levelGE_14 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_14.lua'
$levelGE_15 = Join-Path $dataRoot 'levels\goldeneggs1\LevelGE_15.lua'
$imageRoot = Join-Path $dataRoot 'images\864x480'
$localizationRoot = Join-Path $dataRoot 'localization'
# Stage24.25.1a proved the untouched audio payload is rooted at
# assets/data/audio, with gameplay WAVs under audio/sfx and music/long cues
# alongside MP3 payloads. Stage24.25.2 packages that exact user-owned subtree
# into the locally built APK; the project ZIP itself contains no Rovio audio.
$audioRoot = Join-Path $dataRoot 'audio'
$sfxRoot = Join-Path $audioRoot 'sfx'
$wavAuditRoot = if (Test-Path $sfxRoot) { $sfxRoot } else { $dataRoot }
$textsBasic = Join-Path $localizationRoot 'TEXTS_BASIC.dat'
$fontProfileRoot = Join-Path $dataRoot 'fonts\864x480'
$fontDatNames = @(
    'FONT_BASIC.dat',
    'FONT_MENU.dat',
    'FONT_SCORE.dat',
    'FONT_BIG_NUMBERS.dat',
    'FONT_LS_SMALL.dat'
)
$fontDatFiles = @($fontDatNames | ForEach-Object { Join-Path $fontProfileRoot $_ })
$blocksDat = Join-Path $imageRoot 'INGAME_BLOCKS_1.dat'
$birdsDat = Join-Path $imageRoot 'INGAME_BIRDS_1.dat'
$blocksZip = Join-Path $imageRoot 'INGAME_BLOCKS_1.pvr.zip'
$birdsZip = Join-Path $imageRoot 'INGAME_BIRDS_1.pvr.zip'
# Stage 24.14.4: exact MaskedImage fill texture. Old Android asset dumps
# can contain either a direct PVR or the original one-file .pvr.zip wrapper.
$themeGroundDirect = Join-Path $imageRoot 'INGAME_THEME_GROUND_1.pvr'
$themeGroundZip = Join-Path $imageRoot 'INGAME_THEME_GROUND_1.pvr.zip'
# Stage 24.35.2: theme2 static terrain uses the same MaskedImage contract with
# a different original fill image. Keep transport keyed by the Lua-provided
# texture name instead of substituting theme1 pixels.
$themeGround2Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_2.pvr'
$themeGround2Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_2.pvr.zip'
# Stage 24.38.0: exact theme3 fill family, proven present by the Stage24.15.0
# scene inventory (INGAME_THEME_GROUND_3.dat -> INGAME_THEME_GROUND_3.pvr).
$themeGround3Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_3.pvr'
$themeGround3Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_3.pvr.zip'
# Stage 24.39.0: Mighty Hoax theme4 exact terrain fill, proven by the retained
# Stage24.15.0 original asset inventory.
$themeGround4Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_4.pvr'
$themeGround4Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_4.pvr.zip'
# Stage 24.41.0: Mighty Hoax theme5 exact terrain fill, proven by the retained
# Stage24.15.0 original asset inventory.
$themeGround5Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_5.pvr'
$themeGround5Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_5.pvr.zip'
# Stage 24.42.0: Danger Above theme6 exact terrain fill, proven by the retained
# Stage24.15.0 original asset inventory.
$themeGround6Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_6.pvr'
$themeGround6Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_6.pvr.zip'
# Stage 24.45.0: Danger Above theme7 exact terrain fill from retained Stage24.15.0 inventory.
$themeGround7Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_7.pvr'
$themeGround7Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_7.pvr.zip'
# Stage 24.45.1: Danger Above theme8 exact terrain fill from retained Stage24.15.0 inventory.
$themeGround8Direct = Join-Path $imageRoot 'INGAME_THEME_GROUND_8.pvr'
$themeGround8Zip = Join-Path $imageRoot 'INGAME_THEME_GROUND_8.pvr.zip'
$menuMetaNames = @(
    'BACKGROUNDS_GE_1.dat',
    'BACKGROUNDS_LS_1.dat',
    'BACKGROUNDS_MAIN_1.dat',
    'POPUPS_SHEET_1.dat',
    'BUTTONS_SHEET_1.dat',
    'GOLDEN_EGGS_SHEET_1.dat',
    'LEVELSELECTION_SHEET_1.dat',
    'MENU_ELEMENTS_1.dat',
    'MENU_BACKGROUNDS_1.dat',
    'TUTORIALS_SHEET_1.dat',
    # Stage 24.29.0: core startup branding metadata. These remain references
    # to the user's original asset tree; the project ZIP carries no Rovio pixels.
    'SPLASHES_SHEET_1.dat',
    'SPLASHES_SHEET_2.dat'
)
# Stage 24.30.3: the untouched pre-loader replays loadImages(OTHER/MENU)
# before the GLES renderer exists.  v0.26.93 proved that this replay reaches
# original MENU sheets beyond the older minimal bootstrap set (first concrete
# miss: GOLDEN_EGGS_SHEET_2).  Any concrete, edition-local supplemental sheet
# from the original loadlist must therefore be resident before that replay so
# force=false createSpriteSheet keeps stock reuse semantics without requiring
# a GPU bridge.  Missing edition-specific files remain skipped; no asset is
# invented and CUTSCENES stay dynamic/owned by loadCutScenes.
$preGpuSupplementalMenuMetaCandidates = @(
    'ACHIEVEMENTS_SHEET_1.dat',
    'GOLDEN_EGGS_SHEET_2.dat',
    'GOLDEN_EGGS_SHEET_4.dat',
    'LEVELSELECTION_SHEET_2.dat',
    'MENU_ELEMENTS_2.dat',
    'MENU_ELEMENTS_3.dat',
    'SPLASHES_SHEET_3.dat'
)
$preGpuSupplementalMenuMetaNames = @($preGpuSupplementalMenuMetaCandidates | Where-Object { Test-Path (Join-Path $imageRoot $_) })
$menuMetaNames = @($menuMetaNames + $preGpuSupplementalMenuMetaNames | Select-Object -Unique)
Write-Host "[stage24.30.3-pre-gpu-menu-closure] supplemental resident sheets=$($preGpuSupplementalMenuMetaNames -join ', ')"
if ($preGpuSupplementalMenuMetaNames -notcontains 'GOLDEN_EGGS_SHEET_2.dat') {
    throw 'Stage 24.30.3 requires the concrete GOLDEN_EGGS_SHEET_2.dat proven by the v0.26.93 runtime frontier.'
}
$menuMetaFiles = @($menuMetaNames | ForEach-Object { Join-Path $imageRoot $_ })
$tutorialCompoDat = Join-Path $imageRoot 'TUTORIALS_composprites.dat'

# Stage 24.30.1: dynamic first-entry story sheets. These remain outside the
# bootstrap SpriteDB until untouched Lua calls res.createSpriteSheet(path).
$cutsceneMetaNames = @(
    'CUTSCENES_BACKGROUNDS_1.dat',
    'CUTSCENES_BACKGROUNDS_2.dat',
    'CUTSCENES_BACKGROUNDS_3.dat',
    'CUTSCENES_BACKGROUNDS_4.dat',
    'CUTSCENES_ELEMENTS_1.dat',
    'CUTSCENES_ELEMENTS_2.dat'
)
$cutsceneMetaFiles = @($cutsceneMetaNames | ForEach-Object { Join-Path $imageRoot $_ })
$cutsceneTextureNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($meta in $cutsceneMetaFiles) {
    if (!(Test-Path $meta)) { throw "Required original cutscene metadata not found: $meta" }
    $ascii = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($meta))
    foreach ($m in [regex]::Matches($ascii, '[A-Za-z0-9_.-]+\.(?:png|pvr)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
        [void]$cutsceneTextureNames.Add([IO.Path]::GetFileName($m.Value))
    }
}
$cutsceneTextureNames = @($cutsceneTextureNames | Sort-Object)
if ($cutsceneTextureNames.Count -eq 0) { throw 'No cutscene texture references discovered from original CUTSCENES DATs.' }
Write-Host "[stage24.30.1-cutscene] Dynamic sheet contract discovered meta=$($cutsceneMetaNames.Count) textures=$($cutsceneTextureNames -join ', ')"


# Stage 24.15.3 + 24.35.0: original scene families. Theme1 uses the proven
# SKIES_1 / PARALLAX_1 / GROUNDS_1 set; theme2 reuses the sky/ground families
# and adds the recovered INGAME_PARALLAX_2 layer family. No filename is guessed.
$themeSceneMetaNames = @('INGAME_SKIES_1.dat','INGAME_SKIES_2.dat','INGAME_PARALLAX_1.dat','INGAME_PARALLAX_2.dat','INGAME_PARALLAX_3.dat','INGAME_PARALLAX_4.dat','INGAME_PARALLAX_5.dat','INGAME_PARALLAX_6.dat','INGAME_PARALLAX_7.dat','INGAME_PARALLAX_8.dat','INGAME_PARALLAX_CRANES.dat','INGAME_GROUNDS_1.dat')
$themeSceneTextureNames = @('INGAME_SKIES_1.pvr','INGAME_SKIES_2.pvr','INGAME_PARALLAX_1.pvr','INGAME_PARALLAX_2.pvr','INGAME_PARALLAX_3.pvr','INGAME_PARALLAX_4.pvr','INGAME_PARALLAX_5.pvr','INGAME_PARALLAX_6.pvr','INGAME_PARALLAX_7.pvr','INGAME_PARALLAX_8.pvr','INGAME_PARALLAX_CRANES.pvr','INGAME_GROUNDS_1.pvr')
$themeSceneMetaFiles = @($themeSceneMetaNames | ForEach-Object { Join-Path $imageRoot $_ })
$themeSceneTextureFiles = @($themeSceneTextureNames | ForEach-Object { Join-Path $imageRoot $_ })

# Stage 24.13.2: discover the exact texture files referenced by the original
# menu SPRT metadata. Android 1.4.x mixes PNG and PVR assets, so do not assume
# an extension from the DAT filename. The regex only reads the length-prefixed
# ASCII texture names already embedded in each untouched KA3D SPRT chunk.
$menuTextureNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($meta in $menuMetaFiles) {
    $metaAscii = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($meta))
    foreach ($m in [regex]::Matches($metaAscii, '[A-Za-z0-9_.-]+\.(?:png|pvr)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
        [void]$menuTextureNames.Add([IO.Path]::GetFileName($m.Value))
    }
}
$menuTextureNames = @($menuTextureNames | Sort-Object)
if ($menuTextureNames.Count -eq 0) { throw 'No menu texture references (.png/.pvr) found in original SPRT metadata.' }
Write-Host "[stage24.13.2] Menu texture contract discovered from DAT: $($menuTextureNames -join ', ')"

foreach ($required in @($scripts,$level1,$level57,$level53,$level3,$level6,$level2,$level4,$level5,$level7,$level8,$level9,$level13,$level10,$level39,$level12,$level15,$level17,$level14,$level16,$level23,$level44,$level52p2,$level34p2,$level42p2,$level24p2,$level88p2,$level36p2,$level31p2,$level21p2,$level41p2,$level76p2,$level38p2,$level35p2,$level20p2,$level26p2,$level66p2,$level85p2,$level27p2,$level32p2,$level72p2,$level90p2,$level96p2,$level43p3,$level77p3,$level28p3,$level29p3,$level87p3,$level18p3,$level91p3,$level49p3,$level45p3,$level75p3,$level51p3,$level30p3,$level79p3,$level40p3,$level59p3,$level58p3,$level95p3,$level82p3,$level22p3,$level89p3,$level81p3,$levelP2_103p4,$levelP2_91p4,$levelP2_65p4,$levelP2_96p4,$levelP2_69p4,$levelP2_88p4,$levelP2_64p4,$levelP2_80p4,$levelP2_108p4,$levelP2_85p4,$levelP2_82p4,$levelP2_66p4,$levelP2_104p4,$levelP2_210p4,$levelP2_83p4,$levelP2_79p4,$levelP2_77p4,$levelP2_114p4,$levelP2_81p4,$levelP2_68p4,$levelP2_95p4,$levelP2_78p5,$levelP2_100p5,$levelP2_92p5,$levelP2_94p5,$levelP2_89p5,$levelP2_73p5,$levelP2_76p5,$levelP2_122p5,$levelP2_99p5,$levelP2_84p5,$levelP2_86p5,$levelP2_74p5,$levelP2_115p5,$levelP2_98p5,$levelP2_71p5,$levelP2_72p5,$levelP2_87p5,$levelP2_93p5,$levelP2_67p5,$levelP2_97p5,$levelP2_90p5,$levelP3_212p6,$levelP3_134p6,$levelP3_162p6,$levelP3_271p6,$levelP3_224p6,$levelP3_253p6,$levelP3_225p6,$levelP3_232p6,$levelP3_150p6,$levelP3_211p6,$levelP3_223p6,$levelP3_226p6,$levelP3_215p6,$levelP3_220p6,$levelP3_231p6,$levelP3_166p7,$levelP3_237p7,$levelP3_216p7,$levelP3_298p7,$levelP3_303p7,$levelP3_214p7,$levelP3_159p7,$levelP3_164p7,$levelP3_299p7,$levelP3_302p7,$levelP3_219p7,$levelP3_163p7,$levelP3_160p7,$levelP3_161p7,$levelP3_304p7,$levelP3_297p8,$levelP3_221p8,$levelP3_306p8,$levelP3_301p8,$levelP3_312p8,$levelP3_309p8,$levelP3_168p8,$levelP3_311p8,$levelP3_308p8,$levelP3_310p8,$levelP3_217p8,$levelP3_307p8,$levelP3_296p8,$levelP3_149p8,$levelP3_313p8,$levelP4_421p9,$levelP4_423p9,$levelP4_424p9,$levelP4_425p9,$levelP4_426p9,$levelP4_427p9,$levelP4_428p9,$levelP4_429p9,$levelP4_431p9,$levelP4_432p9,$levelP4_433p9,$levelP4_436p9,$levelP4_439p9,$levelP4_440p9,$levelP4_441p9,$levelP4_442p10,$levelP4_443p10,$levelP4_444p10,$levelP4_445p10,$levelP4_448p10,$levelP4_449p10,$levelP4_451p10,$levelP4_452p10,$levelP4_453p10,$levelP4_454p10,$levelP4_455p10,$levelP4_457p10,$levelP4_458p10,$levelP4_459p10,$levelP4_462p10,$levelP4_463p11,$levelP4_464p11,$levelP4_465p11,$levelP4_466p11,$levelP4_467p11,$levelP4_468p11,$levelP4_469p11,$levelP4_470p11,$levelP4_471p11,$levelP4_472p11,$levelP4_473p11,$levelP4_474p11,$levelP4_475p11,$levelP4_477p11,$levelP4_478p11,$levelGE_1,$levelGE_2,$levelGE_3,$levelGE_4,$levelGE_5,$levelGE_6,$levelGE_7,$levelGE_8,$levelGE_9,$levelGE_10,$levelGE_11,$levelGE_12,$levelGE_13,$levelGE_14,$levelGE_15,$blocksDat,$birdsDat,$blocksZip,$birdsZip,$textsBasic,$tutorialCompoDat) + $menuMetaFiles + $cutsceneMetaFiles + $fontDatFiles + $themeSceneMetaFiles + $themeSceneTextureFiles) {
    if (!(Test-Path $required)) { throw "Required original Angry Birds asset not found: $required" }
}
if (!(Test-Path $themeGroundDirect) -and !(Test-Path $themeGroundZip)) {
    throw "Required original MaskedImage fill texture not found: $themeGroundDirect or $themeGroundZip"
}
if (!(Test-Path $themeGround2Direct) -and !(Test-Path $themeGround2Zip)) {
    throw "Required original theme2 MaskedImage fill texture not found: $themeGround2Direct or $themeGround2Zip"
}
if (!(Test-Path $themeGround3Direct) -and !(Test-Path $themeGround3Zip)) {
    throw "Required original theme3 MaskedImage fill texture not found: $themeGround3Direct or $themeGround3Zip"
}
if (!(Test-Path $themeGround4Direct) -and !(Test-Path $themeGround4Zip)) {
    throw "Required original theme4 MaskedImage fill texture not found: $themeGround4Direct or $themeGround4Zip"
}
if (!(Test-Path $themeGround5Direct) -and !(Test-Path $themeGround5Zip)) {
    throw "Required original theme5 MaskedImage fill texture not found: $themeGround5Direct or $themeGround5Zip"
}
if (!(Test-Path $themeGround6Direct) -and !(Test-Path $themeGround6Zip)) {
    throw "Required original theme6 MaskedImage fill texture not found: $themeGround6Direct or $themeGround6Zip"
}
if (!(Test-Path $themeGround7Direct) -and !(Test-Path $themeGround7Zip)) {
    throw "Required original theme7 MaskedImage fill texture not found: $themeGround7Direct or $themeGround7Zip"
}
if (!(Test-Path $themeGround8Direct) -and !(Test-Path $themeGround8Zip)) {
    throw "Required original theme8 MaskedImage fill texture not found: $themeGround8Direct or $themeGround8Zip"
}
Write-Host '[stage24.45.1-mask] Original terrain fill assets found: INGAME_THEME_GROUND_1 + _2 + _3 + _4 + _5 + _6 + _7 + _8'

# Stage24.25.2 is the first audible build. Unlike the prior diagnostic-only
# audit, the runtime now needs the original payload itself. Require only the
# proven data/audio root and at least one PCM WAV. Stage24.25.7 also consumes
# the untouched MP3 payload through the documented ARM64 compatibility decoder.
if (!(Test-Path $audioRoot)) {
    throw "Stage24.25.2 requires the proven original audio root: $audioRoot"
}
$audioPayloadFiles = @(Get-ChildItem -LiteralPath $audioRoot -Recurse -File)
$audioWavFiles = @($audioPayloadFiles | Where-Object { $_.Extension -ieq '.wav' })
$audioMp3Files = @($audioPayloadFiles | Where-Object { $_.Extension -ieq '.mp3' })
if ($audioWavFiles.Count -eq 0) {
    throw "Stage24.25.2 found no original WAV payloads under: $audioRoot"
}
Write-Host "[stage24.25.2-audio] Original payload preflight PASS root=$audioRoot wav=$($audioWavFiles.Count) mp3=$($audioMp3Files.Count) total=$($audioPayloadFiles.Count)"

# The v0.26.7 trace identifies this exact first missing menu sprite. Verify that
# the locally extracted LEVELSELECTION metadata really owns it before building.
$levelSelectionMeta = Join-Path $imageRoot 'LEVELSELECTION_SHEET_1.dat'
$levelSelectionAscii = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($levelSelectionMeta))
if (!$levelSelectionAscii.Contains('LS_LEVEL_BG_NORMAL_OPEN_1')) {
    throw "LEVELSELECTION_SHEET_1.dat does not contain LS_LEVEL_BG_NORMAL_OPEN_1: $levelSelectionMeta"
}
Write-Host '[stage24] Menu metadata ownership check PASS: LS_LEVEL_BG_NORMAL_OPEN_1 -> LEVELSELECTION_SHEET_1.dat'

# Stage 24.12.7: the original tutorial branch calls res.getCompoSpriteBounds.
# Verify the exact 1.4.2 COMP asset before packaging it.
$tutorialCompoBytes = [System.IO.File]::ReadAllBytes($tutorialCompoDat)
$tutorialCompoAscii = [System.Text.Encoding]::ASCII.GetString($tutorialCompoBytes)
if ($tutorialCompoBytes.Length -lt 20 -or !$tutorialCompoAscii.StartsWith('KA3D') -or !$tutorialCompoAscii.Contains('COMP')) {
    throw "TUTORIALS_composprites.dat is not the expected KA3D/COMP asset: $tutorialCompoDat"
}
Write-Host "[stage24] Tutorial composprite preflight PASS: TUTORIALS_composprites.dat bytes=$($tutorialCompoBytes.Length) format=KA3D/COMP"

# Stage 24.7: SETTINGS_BG is intentionally *not* required to have an asset
# owner. A full local asset-tree probe found that the literal exists only in
# gamelogic.lua, and the original ARMv7 Resources::getSpriteWidth/Height path
# returns 0 when a requested sprite/sheet is absent. The runtime binding below
# now mirrors that behavior instead of turning an optional/missing sprite into
# a fatal Lua error.
Write-Host '[stage24] SETTINGS_BG asset-owner preflight skipped: ARMv7 missing-sprite bounds semantics are zero/zero, not an exception.'

# Stage 24.8: createMenuPages PC 2635 is exactly
#     res.getString("TEXTS_BASIC", "TEXT_SCORE_SPRITE")
# and the original createStartUpAssets() creates its TextGroupSet from this
# untouched localization asset. Verify that the user's 1.4.2 file contains the
# two IDs required by createMenuPages before packaging it.
$textsBasicAscii = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($textsBasic))
foreach ($id in @('TEXT_SCORE_SPRITE','TEXT_PLAY_SPRITE','FONT_BASIC','FONT_MENU')) {
    if (!$textsBasicAscii.Contains($id)) {
        throw "TEXTS_BASIC.dat does not contain required localization ID ${id}: $textsBasic"
    }
}
Write-Host "[stage24] TEXTS_BASIC localization preflight PASS: $((Get-Item $textsBasic).Length) bytes; result labels + FONT_BASIC/FONT_MENU IDs present."
Write-Host "[stage24] Font asset preflight PASS profile=864x480 files=$($fontDatNames -join ', ')"


if (!(Test-Path $sdk)) { throw 'Android SDK not found.' }
if (!(Test-Path $ndkRoot)) { throw 'Android NDK not found.' }
$ndk = Get-ChildItem $ndkRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1
if (!$ndk) { throw 'No Android NDK version found.' }
$toolchain = Join-Path $ndk.FullName 'build\cmake\android.toolchain.cmake'

$cmakeCmd = Get-Command cmake -ErrorAction SilentlyContinue
if (!$cmakeCmd) { throw 'cmake.exe not found.' }
$cmake = $cmakeCmd.Source
$ninjaCmd = Get-Command ninja -ErrorAction SilentlyContinue
$ninja = if ($ninjaCmd) { $ninjaCmd.Source } else { $null }
if (!$ninja) {
    $candidates = @(
        'C:\Program Files\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe',
        'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe',
        'C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe',
        'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
    )
    foreach ($n in $candidates) { if (Test-Path $n) { $ninja = $n; break } }
}
if (!$ninja) { throw 'ninja.exe not found.' }

$adb = Join-Path $sdk 'platform-tools\adb.exe'
if (!(Test-Path $adb)) { throw 'adb.exe not found.' }
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (!$python) { throw 'python not found.' }

$buildToolsRoot = Join-Path $sdk 'build-tools'
$buildTools = Get-ChildItem $buildToolsRoot -Directory |
    Sort-Object @{ Expression = {
        try { [version]$_.Name } catch { [version]'0.0.0' }
    }} -Descending | Select-Object -First 1
if (!$buildTools) { throw 'Android SDK build-tools not found.' }
$aapt = Join-Path $buildTools.FullName 'aapt.exe'
$zipalign = Join-Path $buildTools.FullName 'zipalign.exe'
$apksigner = Join-Path $buildTools.FullName 'apksigner.bat'
foreach ($tool in @($aapt,$zipalign,$apksigner)) { if (!(Test-Path $tool)) { throw "Android build tool missing: $tool" } }

$platformsRoot = Join-Path $sdk 'platforms'
$platform = Get-ChildItem $platformsRoot -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'android.jar') } |
    Sort-Object @{ Expression = {
        if ($_.Name -match '^android-(\d+)$') { [int]$Matches[1] } else { 0 }
    }} -Descending | Select-Object -First 1
if (!$platform) { throw 'No Android SDK platform/android.jar found.' }
$androidJar = Join-Path $platform.FullName 'android.jar'

function Expand-SinglePvr([string]$zip,[string]$dir) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Expand-Archive -LiteralPath $zip -DestinationPath $dir -Force
    $pvrs = @(Get-ChildItem $dir -Recurse -File | Where-Object { $_.Extension -ieq '.pvr' })
    if ($pvrs.Count -ne 1) { throw "Expected exactly one PVR in $zip; found $($pvrs.Count)." }
    return $pvrs[0].FullName
}

New-Item -ItemType Directory -Force -Path $vendor,$outputDir | Out-Null

# Stage 24.15.0: before implementing any gameplay background/foreground layer,
# inventory the exact 1.4.2 scene families from the user's own extracted tree.
# Public later builds establish the family names, but this audit decides what
# this exact Android asset set actually contains and records raw PVR contracts.
$sceneAudit = Join-Path $outputDir 'stage24.15.0-gameplay-scene-contract.txt'
& $python (Join-Path $root 'tools\stage24150_scene_asset_audit.py') $imageRoot $level1 $level57 | Set-Content -Encoding UTF8 $sceneAudit
if ($LASTEXITCODE -ne 0) { throw 'Stage 24.15.0 gameplay-scene asset contract audit failed.' }
$sceneFileCount = (Select-String -Path $sceneAudit -Pattern '^FILE\t' -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "[stage24.15.0-scene] Exact gameplay-scene asset audit PASS files=$sceneFileCount report=$sceneAudit"

# Stage 24.15.4: the first live scene-renderer attempt proved that these three
# exact Android DATs are not the SPRT container used by normal sprite sheets.
# Capture their binary container contract before writing any alternative parser.
$sceneDatContainerAudit = Join-Path $outputDir 'stage24.15.4-scene-dat-container.txt'
& $python (Join-Path $root 'tools\stage24154_scene_dat_container_audit.py') $themeSceneMetaFiles[0] $themeSceneMetaFiles[1] $themeSceneMetaFiles[2] | Set-Content -Encoding UTF8 $sceneDatContainerAudit
if ($LASTEXITCODE -ne 0) { throw 'Stage 24.15.4 scene DAT container audit failed.' }
Write-Host "[stage24.15.4-scene] Exact non-SPRT scene DAT container audit PASS report=$sceneDatContainerAudit"

# Stage 24.14.1: recover the original ARMv7 MaskedImage::render body when the
# original library is available.  v0.26.20 retains the v0.26.19 demangled-symbol discovery of
# candidates and disassembles by address range: llvm-objdump cannot reliably
# use --disassemble-symbols for local/Thumb symbols in this old ARMv7 .so.
$maskedArmv7Audit = Join-Path $outputDir 'stage24.14.1-armv7-maskedimage-render.txt'
# $angryReRoot is resolved near the start of the script from -OriginalRoot,
# ANGRY_BIRDS_ORIGINAL_ROOT, or the legacy Downloads\angry-re fallback.
$llvmBin = Join-Path $ndk.FullName 'toolchains\llvm\prebuilt\windows-x86_64\bin'
$llvmNm = Join-Path $llvmBin 'llvm-nm.exe'
$llvmObjdump = Join-Path $llvmBin 'llvm-objdump.exe'
"ANGRY_STAGE24_14_1_MASKEDIMAGE_ARMV7_AUDIT 2" | Set-Content -Encoding UTF8 $maskedArmv7Audit

function Invoke-Stage24141NativeText {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [Parameter(Mandatory=$true)][string[]]$ArgList
    )
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $Exe @ArgList 2>&1 | ForEach-Object { "$_" })
        $exitCode = $LASTEXITCODE
    } catch {
        $lines = @("exception=$($_.Exception.Message)")
        $exitCode = -1
    } finally {
        $ErrorActionPreference = $oldEap
    }
    [pscustomobject]@{ Lines = $lines; ExitCode = $exitCode }
}

$armv7Lib = $null
if (Test-Path $angryReRoot) {
    $armv7Lib = Get-ChildItem -LiteralPath $angryReRoot -Recurse -File -Filter 'libangrybirds.so' -ErrorAction SilentlyContinue |
        Sort-Object @{ Expression = { if ($_.FullName -match 'armeabi|armv7') { 0 } else { 1 } } }, FullName |
        Select-Object -First 1
}
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    "lib=$($armv7Lib.FullName)" | Add-Content -Encoding UTF8 $maskedArmv7Audit

    $nmResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-S','-C',$armv7Lib.FullName)
    $nmLines = @($nmResult.Lines)
    $candidates = @($nmLines | Where-Object { $_ -match 'MaskedImage::render' })
    if ($candidates.Count -eq 0) {
        $nmDynResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-D','-S','-C',$armv7Lib.FullName)
        $nmLines = @($nmDynResult.Lines)
        $candidates = @($nmLines | Where-Object { $_ -match 'MaskedImage::render' })
    }

    "nmCandidates=$($candidates.Count)" | Add-Content -Encoding UTF8 $maskedArmv7Audit
    $captured = 0
    foreach ($candidate in $candidates) {
        "nm=$candidate" | Add-Content -Encoding UTF8 $maskedArmv7Audit
        # llvm-nm -S -C format: ADDRESS SIZE TYPE DEMANGLED-NAME
        if ($candidate -match '^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+\S+\s+(.+)$') {
            [UInt64]$startAddress = [Convert]::ToUInt64($matches[1], 16)
            [UInt64]$symbolSize = [Convert]::ToUInt64($matches[2], 16)
            $demangledName = $matches[3]
            # Thumb function symbols can carry bit0.  objdump address ranges must not.
            if (($startAddress % 2) -ne 0) { $startAddress = $startAddress - 1 }
            if ($symbolSize -eq 0) { $symbolSize = 0x400 }
            [UInt64]$stopAddress = $startAddress + $symbolSize
            $startHex = ('0x{0:x}' -f $startAddress)
            $stopHex = ('0x{0:x}' -f $stopAddress)
            "candidate=$demangledName start=$startHex size=0x$('{0:x}' -f $symbolSize) stop=$stopHex" | Add-Content -Encoding UTF8 $maskedArmv7Audit

            $dumpResult = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-d','--demangle',"--start-address=$startHex","--stop-address=$stopHex",$armv7Lib.FullName)
            $dump = @($dumpResult.Lines)
            "objdumpExit=$($dumpResult.ExitCode) lines=$($dump.Count)" | Add-Content -Encoding UTF8 $maskedArmv7Audit
            if ($dump.Count -gt 0) {
                $dump | Add-Content -Encoding UTF8 $maskedArmv7Audit
                $captured++
            }
        } else {
            'parse=FAILED' | Add-Content -Encoding UTF8 $maskedArmv7Audit
        }
    }

    if ($captured -gt 0) {
        Write-Host "[stage24.14.1-mask] ARMv7 MaskedImage render address-range disassembly captured candidates=$captured"
    } elseif ($candidates.Count -gt 0) {
        Write-Host '[stage24.14.1-mask] MaskedImage render symbol(s) found, but address-range disassembly was empty; build continues with live contract audit.'
    } else {
        'symbol=NOT_FOUND' | Add-Content -Encoding UTF8 $maskedArmv7Audit
        Write-Host '[stage24.14.1-mask] ARMv7 lib found, but no MaskedImage::render symbol was exported/retained; build continues with live contract audit.'
    }
} else {
    if (!$armv7Lib) { 'lib=NOT_FOUND' | Add-Content -Encoding UTF8 $maskedArmv7Audit }
    if (!(Test-Path $llvmNm)) { "llvmNm=NOT_FOUND $llvmNm" | Add-Content -Encoding UTF8 $maskedArmv7Audit }
    if (!(Test-Path $llvmObjdump)) { "llvmObjdump=NOT_FOUND $llvmObjdump" | Add-Content -Encoding UTF8 $maskedArmv7Audit }
    Write-Host '[stage24.14.1-mask] ARMv7 MaskedImage static audit unavailable; live setTexture contract audit remains enabled.'
}
Write-Host "[stage24.14.1-mask] Static audit report: $maskedArmv7Audit"

# Stage 24.14.2: the render() body proved that MaskedImage is a transient
# triangle batch with position + two UV sets.  Recover the producer-side
# methods and the nearby shader parameter strings before implementing it.
# This is static/audit-only: the strict live renderer gate remains unchanged.
$maskedFullAudit = Join-Path $outputDir 'stage24.14.2-armv7-maskedimage-full.txt'
"ANGRY_STAGE24_14_2_MASKEDIMAGE_FULL_ARMV7_AUDIT 1" | Set-Content -Encoding UTF8 $maskedFullAudit

if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    "lib=$($armv7Lib.FullName)" | Add-Content -Encoding UTF8 $maskedFullAudit

    $nmAllResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-S','-C',$armv7Lib.FullName)
    $nmAllLines = @($nmAllResult.Lines)
    $maskedCandidates = @($nmAllLines | Where-Object { $_ -match 'MaskedImage' })
    if ($maskedCandidates.Count -eq 0) {
        $nmAllDynResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-D','-S','-C',$armv7Lib.FullName)
        $nmAllLines = @($nmAllDynResult.Lines)
        $maskedCandidates = @($nmAllLines | Where-Object { $_ -match 'MaskedImage' })
    }

    "nmExit=$($nmAllResult.ExitCode)" | Add-Content -Encoding UTF8 $maskedFullAudit
    "maskedSymbolCandidates=$($maskedCandidates.Count)" | Add-Content -Encoding UTF8 $maskedFullAudit
    '--- MASKEDIMAGE SYMBOL TABLE ---' | Add-Content -Encoding UTF8 $maskedFullAudit
    $maskedCandidates | Add-Content -Encoding UTF8 $maskedFullAudit

    $codeCaptured = 0
    foreach ($candidate in $maskedCandidates) {
        # llvm-nm -S -C: ADDRESS SIZE TYPE DEMANGLED-NAME
        if ($candidate -match '^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+)$') {
            [UInt64]$startAddress = [Convert]::ToUInt64($matches[1], 16)
            [UInt64]$symbolSize = [Convert]::ToUInt64($matches[2], 16)
            $symbolType = $matches[3]
            $demangledName = $matches[4]

            # Only text/weak-text symbols are executable. Keep all data/vtable
            # candidates in the symbol table above, but do not disassemble them.
            if ($symbolType -notmatch '^[TtWw]$') { continue }
            if (($startAddress % 2) -ne 0) { $startAddress = $startAddress - 1 }
            if ($symbolSize -eq 0) { $symbolSize = 0x400 }
            [UInt64]$stopAddress = $startAddress + $symbolSize
            $startHex = ('0x{0:x}' -f $startAddress)
            $stopHex = ('0x{0:x}' -f $stopAddress)

            '' | Add-Content -Encoding UTF8 $maskedFullAudit
            "--- SYMBOL $demangledName type=$symbolType start=$startHex size=0x$('{0:x}' -f $symbolSize) stop=$stopHex ---" | Add-Content -Encoding UTF8 $maskedFullAudit
            $dumpResult = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-d','--demangle',"--start-address=$startHex","--stop-address=$stopHex",$armv7Lib.FullName)
            "objdumpExit=$($dumpResult.ExitCode) lines=$(@($dumpResult.Lines).Count)" | Add-Content -Encoding UTF8 $maskedFullAudit
            if (@($dumpResult.Lines).Count -gt 0) {
                @($dumpResult.Lines) | Add-Content -Encoding UTF8 $maskedFullAudit
                $codeCaptured++
            }
        }
    }

    # render() references four PC-relative string literals clustered here.
    # Dump a slightly wider, evidence-derived window so the exact shader
    # parameter names can be recovered rather than guessed.
    [UInt64]$roStart = 0x145180
    [UInt64]$roStop = 0x145280
    $roStartHex = ('0x{0:x}' -f $roStart)
    $roStopHex = ('0x{0:x}' -f $roStop)
    '' | Add-Content -Encoding UTF8 $maskedFullAudit
    "--- RODATA SHADER-STRING WINDOW $roStartHex..$roStopHex ---" | Add-Content -Encoding UTF8 $maskedFullAudit

    $roResult = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-s','--section=.rodata',"--start-address=$roStartHex","--stop-address=$roStopHex",$armv7Lib.FullName)
    if ($roResult.ExitCode -ne 0 -or @($roResult.Lines).Count -eq 0) {
        # Old ELF/linker layouts can make section-qualified range selection
        # unhappy.  Fall back to an address-only contents dump, still nonfatal.
        $roResult = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-s',"--start-address=$roStartHex","--stop-address=$roStopHex",$armv7Lib.FullName)
    }
    "rodataExit=$($roResult.ExitCode) lines=$(@($roResult.Lines).Count)" | Add-Content -Encoding UTF8 $maskedFullAudit
    @($roResult.Lines) | Add-Content -Encoding UTF8 $maskedFullAudit

    Write-Host "[stage24.14.2-mask] ARMv7 full MaskedImage audit PASS symbols=$($maskedCandidates.Count) codeBodies=$codeCaptured rodataLines=$(@($roResult.Lines).Count)"
} else {
    if (!$armv7Lib) { 'lib=NOT_FOUND' | Add-Content -Encoding UTF8 $maskedFullAudit }
    if (!(Test-Path $llvmNm)) { "llvmNm=NOT_FOUND $llvmNm" | Add-Content -Encoding UTF8 $maskedFullAudit }
    if (!(Test-Path $llvmObjdump)) { "llvmObjdump=NOT_FOUND $llvmObjdump" | Add-Content -Encoding UTF8 $maskedFullAudit }
    Write-Host '[stage24.14.2-mask] ARMv7 full MaskedImage audit unavailable; build continues unchanged.'
}
Write-Host "[stage24.14.2-mask] Full static audit report: $maskedFullAudit"

# Stage 24.14.5: fidelity audit for the first visible terrain result.
# No renderer geometry/UV constants are changed here.  The live semantic change
# is limited to the alpha-mask combine proven by Rovio shader sources; this
# audit searches the user's original tree and the original ARMv7 call sites so
# any remaining seam/placement difference can be recovered instead of tuned.
$maskedFidelityAudit = Join-Path $outputDir 'stage24.14.5-original-mask-fidelity.txt'
"ANGRY_STAGE24_14_5_ORIGINAL_MASK_FIDELITY_AUDIT 1" | Set-Content -Encoding UTF8 $maskedFidelityAudit
'contract=BASEMAP_RGB_UNCHANGED; outputAlpha=BASEMAP_ALPHA*BASEMAP1_ALPHA' | Add-Content -Encoding UTF8 $maskedFidelityAudit
'policy=NO_MAGIC_NUMBERS_NO_HALF_TEXEL_GUESS_NO_VISUAL_FUDGE' | Add-Content -Encoding UTF8 $maskedFidelityAudit

# First prefer exact shader/source evidence from the user's own extracted 1.4.2
# tree.  Some Android packages do not ship text shaders, so absence is evidence
# only and must never fail the build.
'--- LOCAL ORIGINAL SHADER SEARCH ---' | Add-Content -Encoding UTF8 $maskedFidelityAudit
$shaderCandidates = @()
if (Test-Path $angryReRoot) {
    $shaderCandidates = @(Get-ChildItem -LiteralPath $angryReRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $_.FullName -match '(?i)[\\/]shaders?[\\/]' -or $_.Name -match '(?i)\.(fx|ps|vs|glsl|shader|sh)$'
    })
}
"candidateFiles=$($shaderCandidates.Count)" | Add-Content -Encoding UTF8 $maskedFidelityAudit
$shaderHitCount = 0
foreach ($shaderFile in $shaderCandidates) {
    try {
        $hits = @(Select-String -LiteralPath $shaderFile.FullName -Pattern @('ENABLE_ALPHA_MASK','BASEMAP1','2d-sprite-alpha-masked') -SimpleMatch -ErrorAction Stop)
        if ($hits.Count -eq 0) { continue }
        "file=$($shaderFile.FullName) sha256=$((Get-FileHash -Algorithm SHA256 $shaderFile.FullName).Hash.ToLowerInvariant())" | Add-Content -Encoding UTF8 $maskedFidelityAudit
        foreach ($hit in $hits) {
            $line = ($hit.Line -replace '\s+$','').Trim()
            "  line=$($hit.LineNumber) text=$line" | Add-Content -Encoding UTF8 $maskedFidelityAudit
            $shaderHitCount++
        }
    } catch {
        "read-skip=$($shaderFile.FullName) reason=$($_.Exception.Message)" | Add-Content -Encoding UTF8 $maskedFidelityAudit
    }
}
if ($shaderHitCount -eq 0) {
    'localShaderContract=NOT_FOUND (nonfatal; original Android package may not ship text shader sources)' | Add-Content -Encoding UTF8 $maskedFidelityAudit
} else {
    "localShaderContractHits=$shaderHitCount" | Add-Content -Encoding UTF8 $maskedFidelityAudit
}

# The old llvm-objdump build ignores section address ranges on this ELF.  Dump
# .rodata once and filter by the actual addresses referenced by render().
# These bounds come directly from render()'s PC-relative literal targets, not
# from a visual adjustment.
'--- ARMV7 RODATA EXACT REFERENCED WINDOW ---' | Add-Content -Encoding UTF8 $maskedFidelityAudit
if ($armv7Lib -and (Test-Path $llvmObjdump)) {
    [UInt64]$roExactStart = 0x1451c0
    [UInt64]$roExactStop = 0x145220
    $roAll = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-s','--section=.rodata',$armv7Lib.FullName)
    $roExactLines = @()
    foreach ($line in @($roAll.Lines)) {
        if ($line -match '^\s*([0-9A-Fa-f]{6,})\s+') {
            try { [UInt64]$addr = [Convert]::ToUInt64($matches[1],16) } catch { continue }
            if ($addr -ge $roExactStart -and $addr -lt $roExactStop) { $roExactLines += $line }
        }
    }
    "objdumpExit=$($roAll.ExitCode) filteredLines=$($roExactLines.Count) start=0x$('{0:x}' -f $roExactStart) stop=0x$('{0:x}' -f $roExactStop)" | Add-Content -Encoding UTF8 $maskedFidelityAudit
    $roExactLines | Add-Content -Encoding UTF8 $maskedFidelityAudit
} else {
    'rodata=UNAVAILABLE' | Add-Content -Encoding UTF8 $maskedFidelityAudit
}

# Find every original ARMv7 call to MaskedImage::add(), then capture the exact
# containing function from one symbol header to the next.  This gives the next
# stage the original x/y/model-transform setup without inventing offsets.
'--- ARMV7 MASKEDIMAGE::ADD CALLERS ---' | Add-Content -Encoding UTF8 $maskedFidelityAudit
$callerCount = 0
if ($armv7Lib -and (Test-Path $llvmObjdump)) {
    $fullDis = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-d','--demangle',$armv7Lib.FullName)
    $fullLines = @($fullDis.Lines)
    $capturedCallerHeaders = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    for ($i = 0; $i -lt $fullLines.Count; $i++) {
        if ($fullLines[$i] -notmatch '\bblx?\b.*<MaskedImage::add\(float, float, gr::Image\*, game::Sprite\*\)>') { continue }
        $headerIndex = $i
        while ($headerIndex -ge 0 -and $fullLines[$headerIndex] -notmatch '^\s*[0-9A-Fa-f]+\s+<.+>:\s*$') { $headerIndex-- }
        if ($headerIndex -lt 0) { continue }
        $header = $fullLines[$headerIndex]
        if (!$capturedCallerHeaders.Add($header)) { continue }
        $endIndex = $headerIndex + 1
        while ($endIndex -lt $fullLines.Count -and $fullLines[$endIndex] -notmatch '^\s*[0-9A-Fa-f]+\s+<.+>:\s*$') { $endIndex++ }
        '' | Add-Content -Encoding UTF8 $maskedFidelityAudit
        "caller=$header callLine=$($fullLines[$i])" | Add-Content -Encoding UTF8 $maskedFidelityAudit
        for ($j = $headerIndex; $j -lt $endIndex; $j++) { $fullLines[$j] | Add-Content -Encoding UTF8 $maskedFidelityAudit }
        $callerCount++
    }
    "fullObjdumpExit=$($fullDis.ExitCode) callerBodies=$callerCount" | Add-Content -Encoding UTF8 $maskedFidelityAudit
} else {
    'callers=UNAVAILABLE' | Add-Content -Encoding UTF8 $maskedFidelityAudit
}
Write-Host "[stage24.14.5-mask] Fidelity audit PASS localShaderHits=$shaderHitCount armv7CallerBodies=$callerCount"
Write-Host "[stage24.14.5-mask] Fidelity audit report: $maskedFidelityAudit"

# Stage 24.15.1: the live scene audit proved both Level1 and Level57 are theme1
# with no per-level themeSprites, while the current ARM64 binding still mapped
# setTheme/drawBackgroundNative/drawForegroundNative to historical stubs.
# Recover the original native theme boundary before drawing a single pixel.
$themeNativeAudit = Join-Path $outputDir 'stage24.15.1-armv7-theme-native-contract.txt'
"ANGRY_STAGE24_15_1_ARMV7_THEME_NATIVE_CONTRACT_AUDIT 1" | Set-Content -Encoding UTF8 $themeNativeAudit
'policy=NO_MAGIC_NUMBERS; recover setTheme/background/foreground before implementation' | Add-Content -Encoding UTF8 $themeNativeAudit
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    "lib=$($armv7Lib.FullName)" | Add-Content -Encoding UTF8 $themeNativeAudit
    $themeNmResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-S','-C',$armv7Lib.FullName)
    $themeNmLines = @($themeNmResult.Lines)
    if ($themeNmLines.Count -eq 0) {
        $themeNmResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-D','-S','-C',$armv7Lib.FullName)
        $themeNmLines = @($themeNmResult.Lines)
    }

    # Keep a compact symbol index for anything plausibly owning the global
    # theme scene.  These names come from the original symbol table, not from
    # assumptions in the ARM64 implementation.
    $themeSymbolLines = @($themeNmLines | Where-Object {
        $_ -match '(?i)(GameLua::.*(setTheme|Background|Foreground|Theme)|::setTheme\(|Parallax|Background|Foreground)'
    })
    "nmExit=$($themeNmResult.ExitCode) themeSymbolCandidates=$($themeSymbolLines.Count)" | Add-Content -Encoding UTF8 $themeNativeAudit
    '--- THEME-RELATED SYMBOL TABLE ---' | Add-Content -Encoding UTF8 $themeNativeAudit
    $themeSymbolLines | Add-Content -Encoding UTF8 $themeNativeAudit

    # Exact target methods: capture bodies if symbols exist.  If names differ,
    # the table above remains enough evidence for the next iteration.
    $exactThemeCandidates = @($themeNmLines | Where-Object {
        $_ -match '(?i)(GameLua::setTheme\(|GameLua::drawBackground\(|GameLua::drawForeground\(|GameLua::drawBackgroundNative\(|GameLua::drawForegroundNative\()'
    })
    "exactThemeCandidates=$($exactThemeCandidates.Count)" | Add-Content -Encoding UTF8 $themeNativeAudit
    $themeBodies = 0
    foreach ($candidate in $exactThemeCandidates) {
        if ($candidate -match '^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+)$') {
            [UInt64]$startAddress = [Convert]::ToUInt64($matches[1],16)
            [UInt64]$symbolSize = [Convert]::ToUInt64($matches[2],16)
            $symbolType = $matches[3]
            $demangledName = $matches[4]
            if ($symbolType -notmatch '^[TtWw]$') { continue }
            if (($startAddress % 2) -ne 0) { $startAddress = $startAddress - 1 }
            if ($symbolSize -eq 0) { $symbolSize = 0x800 }
            [UInt64]$stopAddress = $startAddress + $symbolSize
            $startHex=('0x{0:x}' -f $startAddress); $stopHex=('0x{0:x}' -f $stopAddress)
            '' | Add-Content -Encoding UTF8 $themeNativeAudit
            "--- SYMBOL $demangledName type=$symbolType start=$startHex size=0x$('{0:x}' -f $symbolSize) stop=$stopHex ---" | Add-Content -Encoding UTF8 $themeNativeAudit
            $d=Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-d','--demangle',"--start-address=$startHex","--stop-address=$stopHex",$armv7Lib.FullName)
            "objdumpExit=$($d.ExitCode) lines=$(@($d.Lines).Count)" | Add-Content -Encoding UTF8 $themeNativeAudit
            @($d.Lines) | Add-Content -Encoding UTF8 $themeNativeAudit
            if (@($d.Lines).Count -gt 0) { $themeBodies++ }
        }
    }

    # Extract exact printable strings from the original binary with offsets.
    # Python reads the bytes directly so this does not depend on llvm-strings
    # availability in a particular NDK release.
    '' | Add-Content -Encoding UTF8 $themeNativeAudit
    '--- ORIGINAL BINARY SCENE STRINGS ---' | Add-Content -Encoding UTF8 $themeNativeAudit
    $stringReport = @(& $python (Join-Path $root 'tools\stage24151_theme_binary_strings.py') $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $stringExit = $LASTEXITCODE
    "stringAuditExit=$stringExit lines=$($stringReport.Count)" | Add-Content -Encoding UTF8 $themeNativeAudit
    $stringReport | Add-Content -Encoding UTF8 $themeNativeAudit
    Write-Host "[stage24.15.1-theme] ARMv7 native theme audit PASS symbols=$($themeSymbolLines.Count) exact=$($exactThemeCandidates.Count) bodies=$themeBodies report=$themeNativeAudit"
} else {
    if (!$armv7Lib) { 'lib=NOT_FOUND' | Add-Content -Encoding UTF8 $themeNativeAudit }
    if (!(Test-Path $llvmNm)) { "llvmNm=NOT_FOUND $llvmNm" | Add-Content -Encoding UTF8 $themeNativeAudit }
    if (!(Test-Path $llvmObjdump)) { "llvmObjdump=NOT_FOUND $llvmObjdump" | Add-Content -Encoding UTF8 $themeNativeAudit }
    Write-Host '[stage24.15.1-theme] ARMv7 native theme audit unavailable; build continues.'
}


# Stage 24.16.0: presentation/resolution contract audit.  The previous stage
# made the old 480x320 gameplay pillarbox assumption visible; do not replace it
# with another guessed widescreen formula.  Inventory the exact user's 1.4.2
# asset/profile tree and disassemble only original ARMv7 display-facing methods.
$presentationAssetAudit = Join-Path $outputDir 'stage24.16.0-asset-profile-contract.txt'
& $python (Join-Path $root 'tools\stage24160_presentation_tree_audit.py') $dataRoot | Set-Content -Encoding UTF8 $presentationAssetAudit
if ($LASTEXITCODE -ne 0) { throw 'Stage 24.16.0 asset/profile tree audit failed.' }
Write-Host "[stage24.16.0-presentation] Original asset/profile tree audit PASS report=$presentationAssetAudit"

$presentationArmv7Audit = Join-Path $outputDir 'stage24.16.0-armv7-presentation-contract.txt'
"ANGRY_STAGE24_16_0_ARMV7_PRESENTATION_CONTRACT 1" | Set-Content -Encoding UTF8 $presentationArmv7Audit
'policy=DIAGNOSTIC_ONLY; no viewport/aspect implementation in this stage' | Add-Content -Encoding UTF8 $presentationArmv7Audit
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    "lib=$($armv7Lib.FullName)" | Add-Content -Encoding UTF8 $presentationArmv7Audit
    $presNmResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-S','-C',$armv7Lib.FullName)
    $presNmLines = @($presNmResult.Lines)
    if ($presNmLines.Count -eq 0) {
        $presNmResult = Invoke-Stage24141NativeText -Exe $llvmNm -ArgList @('-D','-S','-C',$armv7Lib.FullName)
        $presNmLines = @($presNmResult.Lines)
    }

    $presRelated = @($presNmLines | Where-Object {
        $_ -match '(?i)(GameLua::.*(RenderState|TopLeft|WorldScale|Screen|Width|Height|Viewport)|gr::Context::.*(width|height|viewport|clear|projection|transform)|Viewport|Resolution|Display|Screen)'
    } | Select-Object -First 300)
    "nmExit=$($presNmResult.ExitCode) relatedSymbols=$($presRelated.Count)" | Add-Content -Encoding UTF8 $presentationArmv7Audit
    '--- PRESENTATION-RELATED SYMBOL TABLE (capped 300) ---' | Add-Content -Encoding UTF8 $presentationArmv7Audit
    $presRelated | Add-Content -Encoding UTF8 $presentationArmv7Audit

    # Exact targets are names observed in the original symbol table or native
    # boundaries already called by untouched gamelogic.lua. Unknown/missing
    # methods stay missing rather than receiving guessed semantics.
    $presExact = @($presNmLines | Where-Object {
        $_ -match '(?i)(GameLua::setRenderState\(|GameLua::setTopLeft\(|GameLua::setWorldScale\(|GameLua::GameLua\(|gr::Context::width\(|gr::Context::height\(|gr::Context::viewport\(|gr::Context::setViewport\(|gr::Context::clear\()'
    })
    "exactCandidates=$($presExact.Count)" | Add-Content -Encoding UTF8 $presentationArmv7Audit
    $presBodies = 0
    foreach ($candidate in $presExact) {
        if ($candidate -match '^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+)$') {
            [UInt64]$startAddress = [Convert]::ToUInt64($matches[1],16)
            [UInt64]$symbolSize = [Convert]::ToUInt64($matches[2],16)
            $symbolType = $matches[3]
            $demangledName = $matches[4]
            if ($symbolType -notmatch '^[TtWw]$') { continue }
            if (($startAddress % 2) -ne 0) { $startAddress = $startAddress - 1 }
            if ($symbolSize -eq 0) { $symbolSize = 0x800 }
            [UInt64]$stopAddress = $startAddress + $symbolSize
            $startHex=('0x{0:x}' -f $startAddress); $stopHex=('0x{0:x}' -f $stopAddress)
            '' | Add-Content -Encoding UTF8 $presentationArmv7Audit
            "--- SYMBOL $demangledName type=$symbolType start=$startHex size=0x$('{0:x}' -f $symbolSize) stop=$stopHex ---" | Add-Content -Encoding UTF8 $presentationArmv7Audit
            $pd = Invoke-Stage24141NativeText -Exe $llvmObjdump -ArgList @('-d','--demangle',"--start-address=$startHex","--stop-address=$stopHex",$armv7Lib.FullName)
            "objdumpExit=$($pd.ExitCode) lines=$(@($pd.Lines).Count)" | Add-Content -Encoding UTF8 $presentationArmv7Audit
            @($pd.Lines) | Add-Content -Encoding UTF8 $presentationArmv7Audit
            if (@($pd.Lines).Count -gt 0) { $presBodies++ }
        }
    }

    '' | Add-Content -Encoding UTF8 $presentationArmv7Audit
    '--- ORIGINAL BINARY PRESENTATION / RESOLUTION STRINGS ---' | Add-Content -Encoding UTF8 $presentationArmv7Audit
    $presStrings = @(& $python (Join-Path $root 'tools\stage24160_binary_presentation_strings.py') $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $presStringExit = $LASTEXITCODE
    "stringAuditExit=$presStringExit lines=$($presStrings.Count)" | Add-Content -Encoding UTF8 $presentationArmv7Audit
    $presStrings | Add-Content -Encoding UTF8 $presentationArmv7Audit
    Write-Host "[stage24.16.0-presentation] ARMv7 presentation audit PASS exact=$($presExact.Count) bodies=$presBodies report=$presentationArmv7Audit"
} else {
    if (!$armv7Lib) { 'lib=NOT_FOUND' | Add-Content -Encoding UTF8 $presentationArmv7Audit }
    if (!(Test-Path $llvmNm)) { "llvmNm=NOT_FOUND $llvmNm" | Add-Content -Encoding UTF8 $presentationArmv7Audit }
    if (!(Test-Path $llvmObjdump)) { "llvmObjdump=NOT_FOUND $llvmObjdump" | Add-Content -Encoding UTF8 $presentationArmv7Audit }
    Write-Host '[stage24.16.0-presentation] ARMv7 presentation audit unavailable; runtime Lua audit remains enabled.'
}


# Stage 24.16.1: the 24.16.0 symbol inventory proved that the original ARMv7
# binary exports concrete EGL/native resolution methods, but the old exact
# regex accidentally skipped the EGL_Context namespace and several ownership
# boundaries. Recover those exact bodies and their direct callers before any
# gameplay viewport/camera formula is changed.
$nativeResolutionOwnershipAudit = Join-Path $outputDir 'stage24.16.1-native-resolution-ownership.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $ownershipLines = @(& $python (Join-Path $root 'tools\stage24161_native_resolution_ownership.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $ownershipExit = $LASTEXITCODE
    $ownershipLines | Set-Content -Encoding UTF8 $nativeResolutionOwnershipAudit
    if ($ownershipExit -ne 0) { throw "Stage 24.16.1 native resolution ownership audit failed exit=$ownershipExit report=$nativeResolutionOwnershipAudit" }
    Write-Host "[stage24.16.1-presentation] Native resolution ownership audit PASS report=$nativeResolutionOwnershipAudit"
} else {
    'ANGRY_STAGE24_16_1_NATIVE_RESOLUTION_OWNERSHIP 1' | Set-Content -Encoding UTF8 $nativeResolutionOwnershipAudit
    'policy=DIAGNOSTIC_ONLY; native audit unavailable' | Add-Content -Encoding UTF8 $nativeResolutionOwnershipAudit
    if (!$armv7Lib) { 'lib=NOT_FOUND' | Add-Content -Encoding UTF8 $nativeResolutionOwnershipAudit }
    if (!(Test-Path $llvmNm)) { "llvmNm=NOT_FOUND $llvmNm" | Add-Content -Encoding UTF8 $nativeResolutionOwnershipAudit }
    if (!(Test-Path $llvmObjdump)) { "llvmObjdump=NOT_FOUND $llvmObjdump" | Add-Content -Encoding UTF8 $nativeResolutionOwnershipAudit }
    Write-Host '[stage24.16.1-presentation] Native resolution ownership audit unavailable; build continues.'
}



# Stage 24.16.2: close the exact ownership chain for screenWidth/screenHeight.
# 24.16.1 established that AndroidOSInterface::setResolution is a no-op and
# exposed the EGL context constructor.  This pass maps the Context vtable slots
# used by GameLua, resolves the literal screenWidth/screenHeight writes, and
# finds direct constructor/reset/setNativeSize callers by numeric address.
$screenGlobalSourceAudit = Join-Path $outputDir 'stage24.16.2-screen-global-source.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $sgLines = @(& $python (Join-Path $root 'tools\stage24162_screen_global_source.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $sgExit = $LASTEXITCODE
    $sgLines | Set-Content -Encoding UTF8 $screenGlobalSourceAudit
    if ($sgExit -ne 0) { throw "Stage 24.16.2 screen-global source audit failed exit=$sgExit report=$screenGlobalSourceAudit" }
    Write-Host "[stage24.16.2-presentation] Screen-global source/EGL construction audit PASS report=$screenGlobalSourceAudit"
} else {
    'ANGRY_STAGE24_16_2_SCREEN_GLOBAL_SOURCE 1' | Set-Content -Encoding UTF8 $screenGlobalSourceAudit
    'policy=DIAGNOSTIC_ONLY; native audit unavailable' | Add-Content -Encoding UTF8 $screenGlobalSourceAudit
    Write-Host '[stage24.16.2-presentation] Screen-global source audit unavailable; build continues.'
}

# Stage 24.16.3: one hop above EGL_createContext.  24.16.2 proved that
# GameLua screenWidth/screenHeight are Context::width/height and that the EGL
# factory forwards w/h unchanged.  Walk the reverse direct-call graph so the
# producer of those dimensions is recovered before presentation is changed.
$eglFactoryCallgraphAudit = Join-Path $outputDir 'stage24.16.3-egl-factory-callgraph.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $efLines = @(& $python (Join-Path $root 'tools\stage24163_egl_factory_callgraph.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $efExit = $LASTEXITCODE
    $efLines | Set-Content -Encoding UTF8 $eglFactoryCallgraphAudit
    if ($efExit -ne 0) { throw "Stage 24.16.3 EGL factory callgraph audit failed exit=$efExit report=$eglFactoryCallgraphAudit" }
    Write-Host "[stage24.16.3-presentation] EGL factory upstream callgraph audit PASS report=$eglFactoryCallgraphAudit"
} else {
    'ANGRY_STAGE24_16_3_EGL_FACTORY_CALLGRAPH 1' | Set-Content -Encoding UTF8 $eglFactoryCallgraphAudit
    'policy=DIAGNOSTIC_ONLY; native audit unavailable' | Add-Content -Encoding UTF8 $eglFactoryCallgraphAudit
    Write-Host '[stage24.16.3-presentation] EGL factory callgraph audit unavailable; build continues.'
}

# Stage 24.16.4: JNI boundary provenance. 24.16.3 proved that
# Java_com_rovio_ka3d_MyRenderer_nativeInit is the sole direct caller of
# EGL_createContext and forwards two values as width/height. Dump the full
# nativeInit body and map ARM32 entry arguments/stack slots so the Java
# parameters owning those values are identified before presentation changes.
$jniDimensionProvenanceAudit = Join-Path $outputDir 'stage24.16.4-jni-dimension-provenance.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $jpLines = @(& $python (Join-Path $root 'tools\stage24164_jni_dimension_provenance.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $jpExit = $LASTEXITCODE
    $jpLines | Set-Content -Encoding UTF8 $jniDimensionProvenanceAudit
    if ($jpExit -ne 0) { throw "Stage 24.16.4 JNI dimension provenance audit failed exit=$jpExit report=$jniDimensionProvenanceAudit" }
    Write-Host "[stage24.16.4-presentation] JNI dimension provenance audit PASS report=$jniDimensionProvenanceAudit"
} else {
    'ANGRY_STAGE24_16_4_JNI_DIMENSION_PROVENANCE 1' | Set-Content -Encoding UTF8 $jniDimensionProvenanceAudit
    'policy=DIAGNOSTIC_ONLY; native audit unavailable' | Add-Content -Encoding UTF8 $jniDimensionProvenanceAudit
    Write-Host '[stage24.16.4-presentation] JNI dimension provenance audit unavailable; build continues.'
}

# Stage 24.18.0: now that the Context presentation contract is closed, recover
# the next structurally missing drawGame boundary: original slingshot/resources.
# Diagnostic only: inventory exact asset owners and dump the untouched ARMv7
# drawGame call sequence before emitting any sling wood/rubber pixels.
$slingshotRenderAudit = Join-Path $outputDir 'stage24.18.0-slingshot-render-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $srLines = @(& $python (Join-Path $root 'tools\stage24180_slingshot_render_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $dataRoot 2>&1 | ForEach-Object { "$_" })
    $srExit = $LASTEXITCODE
    $srLines | Set-Content -Encoding UTF8 $slingshotRenderAudit
    if ($srExit -ne 0) { throw "Stage 24.18.0 slingshot render contract audit failed exit=$srExit report=$slingshotRenderAudit" }
    Write-Host "[stage24.18.0-sling] Original slingshot/resource render audit PASS report=$slingshotRenderAudit"
} else {
    'ANGRY_STAGE24_18_0_SLINGSHOT_RENDER_CONTRACT 1' | Set-Content -Encoding UTF8 $slingshotRenderAudit
    'policy=DIAGNOSTIC_ONLY; native audit unavailable' | Add-Content -Encoding UTF8 $slingshotRenderAudit
    Write-Host '[stage24.18.0-sling] Original slingshot render audit unavailable; build continues.'
}

# Stage 24.19.0: score simulation is live but the gameplay score HUD is not.
# Inventory untouched 864x480 score/font assets now; runtime Lua closure audit
# (before binding replacement) recovers exact drawString/font/anchor/position.
$scoreHudAudit = Join-Path $outputDir 'stage24.19.0-gameplay-score-hud-contract.txt'
if (Test-Path $dataRoot) {
    $shLines = @(& $python (Join-Path $root 'tools\stage24190_gameplay_score_hud_contract.py') $dataRoot 2>&1 | ForEach-Object { "$_" })
    $shExit = $LASTEXITCODE
    $shLines | Set-Content -Encoding UTF8 $scoreHudAudit
    if ($shExit -ne 0) { throw "Stage 24.19.0 gameplay score HUD asset audit failed exit=$shExit report=$scoreHudAudit" }
    Write-Host "[stage24.19.0-score-hud] Original gameplay score HUD asset audit PASS report=$scoreHudAudit"
} else {
    'ANGRY_STAGE24_19_0_GAMEPLAY_SCORE_HUD_CONTRACT 1' | Set-Content -Encoding UTF8 $scoreHudAudit
    'policy=DIAGNOSTIC_ONLY; data root unavailable' | Add-Content -Encoding UTF8 $scoreHudAudit
    Write-Host '[stage24.19.0-score-hud] Score HUD asset audit unavailable; build continues.'
}

# Stage 24.19.2: Stage 10 already recovered an ordinary/non-controllable
# BeginContact score-like update equal to floor(totalActualDamage) * 10, but
# intentionally left its target table unresolved. Stage 24.19.1 now proves the
# Lua scoreTable ownership model and runtime ledger exposes a 2-3k deficit.
# Dump the untouched ARMv7 BeginContact body before applying that native score.
$blockScoreOwnershipAudit = Join-Path $outputDir 'stage24.19.2-armv7-block-score-ownership.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $bsLines = @(& $python (Join-Path $root 'tools\stage24192_block_score_ownership.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $bsExit = $LASTEXITCODE
    $bsLines | Set-Content -Encoding UTF8 $blockScoreOwnershipAudit
    if ($bsExit -ne 0) { throw "Stage 24.19.2 ARMv7 block-score ownership audit failed exit=$bsExit report=$blockScoreOwnershipAudit" }
    Write-Host "[stage24.19.2-score] ARMv7 ordinary-contact score ownership audit PASS report=$blockScoreOwnershipAudit"
} else {
    'ANGRY_STAGE24_19_2_BLOCK_SCORE_OWNERSHIP 1' | Set-Content -Encoding UTF8 $blockScoreOwnershipAudit
    'policy=DIAGNOSTIC_ONLY; native audit unavailable' | Add-Content -Encoding UTF8 $blockScoreOwnershipAudit
    Write-Host '[stage24.19.2-score] ARMv7 ordinary-contact score ownership audit unavailable; build continues.'
}

# Exact patched Lua 5.1.5 ABI used by all prior closed stages.
$luaExpected = '2640fc56a795f29d28ef15e13c34a47e223960b0240e8cb0a82d9b0738695333'
$needLua = $true
if (Test-Path $luaArchive) {
    $h = (Get-FileHash -Algorithm SHA256 $luaArchive).Hash.ToLowerInvariant()
    if ($h -eq $luaExpected) { $needLua = $false }
}
if ($needLua) {
    Write-Host '[stage24] Downloading official Lua 5.1.5...'
    Invoke-WebRequest -Uri 'https://www.lua.org/ftp/lua-5.1.5.tar.gz' -OutFile $luaArchive
}
$luaActual = (Get-FileHash -Algorithm SHA256 $luaArchive).Hash.ToLowerInvariant()
if ($luaActual -ne $luaExpected) { throw "Lua SHA256 mismatch: $luaActual" }
Write-Host "[stage24] Lua SHA256 OK: $luaActual"
if (Test-Path $luaDir) { Remove-Item $luaDir -Recurse -Force }
tar -xzf $luaArchive -C $vendor
if ($LASTEXITCODE -ne 0) { throw 'Lua extraction failed.' }
& $python (Join-Path $root 'tools\patch_lua51_angry.py') $luaDir
if ($LASTEXITCODE -ne 0) { throw 'Lua ABI patch failed.' }

# Pinned period-correct Box2D candidate, unchanged from the closed physics stages.
$boxCommit = '20100c5e81ed18619b0fbd5d78bd60e7b13c7fe9'
$boxExpected = '14ddf9af0d5ed006bfcc20d410ac2575d16a852dc1b6ba1cf62f9ab298a7180c'
$boxUrl = "https://codeload.github.com/Necrys/Box2D_v2.1.2/tar.gz/$boxCommit"
$needBox = $true
if (Test-Path $boxArchive) {
    $h = (Get-FileHash -Algorithm SHA256 $boxArchive).Hash.ToLowerInvariant()
    if ($h -eq $boxExpected) { $needBox = $false }
}
if ($needBox) {
    Write-Host "[stage24] Downloading Box2D v2.1.2 pinned commit $boxCommit..."
    Invoke-WebRequest -Uri $boxUrl -OutFile $boxArchive
}
$boxActual = (Get-FileHash -Algorithm SHA256 $boxArchive).Hash.ToLowerInvariant()
if ($boxActual -ne $boxExpected) { throw "Box2D SHA256 mismatch: $boxActual" }
Write-Host "[stage24] Box2D SHA256 OK: $boxActual"
if (Test-Path $boxDir) { Remove-Item $boxDir -Recurse -Force }
$boxTmp = Join-Path $vendor '_box2d_extract'
if (Test-Path $boxTmp) { Remove-Item $boxTmp -Recurse -Force }
New-Item -ItemType Directory -Force -Path $boxTmp | Out-Null
tar -xzf $boxArchive -C $boxTmp
if ($LASTEXITCODE -ne 0) { throw 'Box2D extraction failed.' }
$boxExtracted = Get-ChildItem $boxTmp -Directory | Select-Object -First 1
if (!$boxExtracted) { throw 'Box2D extracted directory missing.' }
Move-Item $boxExtracted.FullName $boxDir
Remove-Item $boxTmp -Recurse -Force

# Stage 24.22.3: the failure deadlock is now narrowed to stale shot birds that
# never satisfy the original Lua speed<0.05 removal gate because they can enter
# a low-amplitude ground-contact limit cycle. Before changing restitution,
# sleep, or the Lua threshold, compare the untouched Rovio Box2D solver/island
# implementation against the pinned 2.1.2 candidate source used by this port.
$box2dSettleAudit = Join-Path $outputDir 'stage24.22.3-box2d-settle-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $settleLines = @(& $python (Join-Path $root 'tools\stage24223_box2d_settle_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
    $settleExit = $LASTEXITCODE
    $settleLines | Set-Content -Encoding UTF8 $box2dSettleAudit
    if ($settleExit -ne 0) { throw "Stage 24.22.3 Box2D settle contract audit failed exit=$settleExit report=$box2dSettleAudit" }
    Write-Host "[stage24.22.3-settle] Original Box2D settle/contact audit PASS report=$box2dSettleAudit"
} else {
    'ANGRY_STAGE24_22_3_BOX2D_SETTLE_CONTRACT 1' | Set-Content -Encoding UTF8 $box2dSettleAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $box2dSettleAudit
    Write-Host '[stage24.22.3-settle] Original Box2D settle/contact audit unavailable; build continues.'
}

# Stage 24.22.4: Stage 24.22.3 proved that the Rovio island sleep constants
# differ from stock Box2D 2.1.2, but the observed ~1.198 ground-contact loop
# specifically points at the restitution velocity-bias gate. Resolve the
# constructor/InitVelocityConstraints threshold directly from untouched ARMv7
# before changing any candidate Box2D setting.
$box2dContactBiasAudit = Join-Path $outputDir 'stage24.22.4-box2d-contact-bias-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $biasLines = @(& $python (Join-Path $root 'tools\stage24224_box2d_contact_bias_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
    $biasExit = $LASTEXITCODE
    $biasLines | Set-Content -Encoding UTF8 $box2dContactBiasAudit
    if ($biasExit -ne 0) { throw "Stage 24.22.4 Box2D contact-bias audit failed exit=$biasExit report=$box2dContactBiasAudit" }
    Write-Host "[stage24.22.4-contact-bias] Original Box2D restitution threshold audit PASS report=$box2dContactBiasAudit"
} else {
    'ANGRY_STAGE24_22_4_BOX2D_CONTACT_BIAS_CONTRACT 1' | Set-Content -Encoding UTF8 $box2dContactBiasAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $box2dContactBiasAudit
    Write-Host '[stage24.22.4-contact-bias] Original Box2D restitution threshold audit unavailable; build continues.'
}

# Stage 24.22.5: Stage 24.22.4 closes the restitution-threshold hypothesis:
# untouched ARMv7 compares vRel against immediate -1.0f, exactly stock
# b2_velocityThreshold=1.0f.  The next ownership boundary is object construction
# itself.  Audit original createCircle/createBox callers around CreateBody and
# CreateFixture before changing restitution, damping, sleep, or the Lua removal
# gate.  This is diagnostic-only and does not mutate gameplay.
$bodyFixtureAudit = Join-Path $outputDir 'stage24.22.5-body-fixture-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $bfLines = @(& $python (Join-Path $root 'tools\stage24225_body_fixture_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
    $bfExit = $LASTEXITCODE
    $bfLines | Set-Content -Encoding UTF8 $bodyFixtureAudit
    if ($bfExit -ne 0) { throw "Stage 24.22.5 body/fixture contract audit failed exit=$bfExit report=$bodyFixtureAudit" }
    Write-Host "[stage24.22.5-body-fixture] Original body/fixture construction audit PASS report=$bodyFixtureAudit"
} else {
    'ANGRY_STAGE24_22_5_BODY_FIXTURE_CONTRACT 1' | Set-Content -Encoding UTF8 $bodyFixtureAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $bodyFixtureAudit
    Write-Host '[stage24.22.5-body-fixture] Original body/fixture construction audit unavailable; build continues.'
}

# Stage 24.22.6: Stage 24.22.5 closes the object-construction hypothesis for
# physics-affecting fields. Untouched createCircle/createBox use angularDamping=1,
# inertiaScale=1, stock body flags, and direct friction/restitution/density. The
# only observed bridge mismatch is fixture userData, which cannot alter solver
# impulses. Audit the next lower ownership boundary: b2Contact material mixing.
$contactMaterialMixAudit = Join-Path $outputDir 'stage24.22.6-contact-material-mix-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $mixLines = @(& $python (Join-Path $root 'tools\stage24226_contact_material_mix_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
    $mixExit = $LASTEXITCODE
    $mixLines | Set-Content -Encoding UTF8 $contactMaterialMixAudit
    if ($mixExit -ne 0) { throw "Stage 24.22.6 contact material-mix audit failed exit=$mixExit report=$contactMaterialMixAudit" }
    Write-Host "[stage24.22.6-contact-mix] Original Box2D contact material-mixing audit PASS report=$contactMaterialMixAudit"
} else {
    'ANGRY_STAGE24_22_6_CONTACT_MATERIAL_MIX_CONTRACT 1' | Set-Content -Encoding UTF8 $contactMaterialMixAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $contactMaterialMixAudit
    Write-Host '[stage24.22.6-contact-mix] Original Box2D contact material-mixing audit unavailable; build continues.'
}

# Stage 24.22.7: Stage 24.22.6 itself looked at b2Contact ownership, but the
# Box2D 2.1.2 material mix actually lives in b2ContactSolver construction.
# Stage 24.22.4 already captured that exact ARMv7 code and proves stock
# sqrt(fA*fB) friction + max(rA,rB) restitution. The stronger remaining clue
# is that original polygon m_radius=0.1 while this bridge otherwise compiles
# stock b2_linearSlop=0.005. Audit the original position-correction constants
# before changing physics or the Lua failure/removal gate.
$linearSlopPositionAudit = Join-Path $outputDir 'stage24.22.7-linear-slop-position-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $slopLines = @(& $python (Join-Path $root 'tools\stage24227_linear_slop_position_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
    $slopExit = $LASTEXITCODE
    $slopLines | Set-Content -Encoding UTF8 $linearSlopPositionAudit
    if ($slopExit -ne 0) { throw "Stage 24.22.7 linear-slop/position audit failed exit=$slopExit report=$linearSlopPositionAudit" }
    Write-Host "[stage24.22.7-linear-slop] Original Box2D linear-slop/position-correction audit PASS report=$linearSlopPositionAudit"
} else {
    'ANGRY_STAGE24_22_7_LINEAR_SLOP_POSITION_CONTRACT 1' | Set-Content -Encoding UTF8 $linearSlopPositionAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $linearSlopPositionAudit
    Write-Host '[stage24.22.7-linear-slop] Original Box2D linear-slop/position-correction audit unavailable; build continues.'
}

# Stage 24.23.4: the pause page now renders and input reaches original actions.
# Runtime testing exposed two remaining ownership boundaries: BUTTON_RESUME
# selects hidePauseMenu but immediately returns to updateMenu, and BUTTON_SFX
# reaches res.getTrackVolume(), not yet bridged. Dump the original native
# LuaResources volume methods before implementing audio-control state.
$pauseAudioNativeAudit = Join-Path $outputDir 'stage24.23.4-pause-audio-native-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $paLines = @(& $python (Join-Path $root 'tools\stage24234_pause_audio_native_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $paExit = $LASTEXITCODE
    $paLines | Set-Content -Encoding UTF8 $pauseAudioNativeAudit
    if ($paExit -ne 0) { throw "Stage 24.23.4 pause/audio native audit failed exit=$paExit report=$pauseAudioNativeAudit" }
    Write-Host "[stage24.23.4-pause-audio] Original pause/audio native contract audit PASS report=$pauseAudioNativeAudit"
} else {
    'ANGRY_STAGE24_23_4_PAUSE_AUDIO_NATIVE_CONTRACT 1' | Set-Content -Encoding UTF8 $pauseAudioNativeAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $pauseAudioNativeAudit
    Write-Host '[stage24.23.4-pause-audio] Original pause/audio native audit unavailable; build continues.'
}

# Stage 24.24.0: particles have intentionally remained headless since Stage16.
# Before replacing particles.addParticles, inventory the original ARMv7 Particles
# wrapper / KA3D particle symbols and strings alongside the untouched Lua
# particle definitions dumped by the live runtime.
$particleNativeAudit = Join-Path $outputDir 'stage24.24.0-particle-native-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $pnLines = @(& $python (Join-Path $root 'tools\stage24240_particle_native_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $pnExit = $LASTEXITCODE
    $pnLines | Set-Content -Encoding UTF8 $particleNativeAudit
    if ($pnExit -ne 0) { throw "Stage 24.24.0 particle native audit failed exit=$pnExit report=$particleNativeAudit" }
    Write-Host "[stage24.24.0-particles] Original particle native contract audit PASS report=$particleNativeAudit"
} else {
    'ANGRY_STAGE24_24_0_PARTICLE_NATIVE_CONTRACT 1' | Set-Content -Encoding UTF8 $particleNativeAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $particleNativeAudit
    Write-Host '[stage24.24.0-particles] Original particle native audit unavailable; live Lua definition audit remains enabled.'
}

# Stage 24.24.1: Stage24.24.0 recovered the full custom Particles wrapper.
# Tighten the final pre-implementation ownership questions: exact soft/hard
# limit policy, random birth-position transform, per-particle random fields,
# 108-byte ParticleData update contract and lifetime animation semantics.
$particleEmitterLimitAudit = Join-Path $outputDir 'stage24.24.1-particle-emitter-limit-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $pelLines = @(& $python (Join-Path $root 'tools\stage24241_particle_emitter_limit_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $pelExit = $LASTEXITCODE
    $pelLines | Set-Content -Encoding UTF8 $particleEmitterLimitAudit
    if ($pelExit -ne 0) { throw "Stage 24.24.1 particle emitter/limit audit failed exit=$pelExit report=$particleEmitterLimitAudit" }
    Write-Host "[stage24.24.1-particles] Exact particle emitter/limit/update contract PASS report=$particleEmitterLimitAudit"
} else {
    'ANGRY_STAGE24_24_1_PARTICLE_EMITTER_LIMIT_CONTRACT 1' | Set-Content -Encoding UTF8 $particleEmitterLimitAudit
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $particleEmitterLimitAudit
    Write-Host '[stage24.24.1-particles] Exact particle emitter/limit audit unavailable; runtime spawn telemetry remains enabled.'
}


# Stage 24.25.0: particles are now visible and validated, so the next missing
# original subsystem is audio.  Inventory the exact ARMv7 LuaResources /
# Resources / AudioOutput call chain before replacing the historical headless
# playAudio/stopAudio surfaces or inventing handle/track semantics.
$audioNative250 = Join-Path $outputDir 'stage24.25.0-audio-native-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $audLines = @(& $python (Join-Path $root 'tools\stage24250_audio_system_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $audExit = $LASTEXITCODE
    $audLines | Set-Content -Encoding UTF8 $audioNative250
    if ($audExit -ne 0) { throw "Stage 24.25.0 audio native audit failed exit=$audExit report=$audioNative250" }
    Write-Host "[stage24.25.0-audio] Original ARMv7 audio-system contract audit PASS report=$audioNative250"
} else {
    'ANGRY_STAGE24_25_0_AUDIO_NATIVE_CONTRACT 1' | Set-Content -Encoding UTF8 $audioNative250
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $audioNative250
    Write-Host '[stage24.25.0-audio] Original audio native audit unavailable; Lua ownership audit remains enabled.'
}

# Stage 24.25.1a: Stage24.25.0 proved the LuaResources -> Resources ->
# AudioOutput ownership and playAudio defaults, but intentionally stopped
# before choosing a replacement backend. Audit the lower AudioMixer/AudioClip
# handle path plus any untouched 1.4.2 WAV headers available in the user's
# local data tree. Some historical angry-re extractions omit assets/data/sfx;
# that absence is diagnostic evidence, not a fatal build prerequisite.
$audioMixerWav251 = Join-Path $outputDir 'stage24.25.1-audio-mixer-wav-contract.txt'
if (!(Test-Path $sfxRoot)) {
    Write-Host "[stage24.25.1a-audio] Direct SFX directory absent: $sfxRoot"
    Write-Host "[stage24.25.1a-audio] Falling back to recursive WAV inventory under: $wavAuditRoot"
}
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $amwLines = @(& $python (Join-Path $root 'tools\stage24251_audio_mixer_wav_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $wavAuditRoot 2>&1 | ForEach-Object { "$_" })
    $amwExit = $LASTEXITCODE
    $amwLines | Set-Content -Encoding UTF8 $audioMixerWav251
    if ($amwExit -ne 0) { throw "Stage 24.25.1 audio mixer/WAV audit failed exit=$amwExit report=$audioMixerWav251" }
    Write-Host "[stage24.25.1-audio] Original mixer + WAV payload contract audit PASS report=$audioMixerWav251"
} else {
    'ANGRY_STAGE24_25_1_AUDIO_MIXER_WAV_CONTRACT 1' | Set-Content -Encoding UTF8 $audioMixerWav251
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable' | Add-Content -Encoding UTF8 $audioMixerWav251
    Write-Host '[stage24.25.1-audio] Mixer/WAV native audit unavailable; runtime audio probe remains enabled.'
}

# Stage 24.25.4: complete audio fidelity audit before adding MP3 playback or
# changing the pause SFX button.  The prior ARMv7 mixer dump already exposes a
# crucial native invariant: AudioMixer::setTrackVolume clamps requested volume
# into [0,1] before storing it.  Audit that body together with createAudio /
# AudioReader ownership and untouched MP3 headers so raw Lua overshoot is not
# confused with observable vanilla mixer state.
$audioFidelity254 = Join-Path $outputDir 'stage24.25.4-audio-fidelity-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $afLines = @(& $python (Join-Path $root 'tools\stage24254_audio_fidelity_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $audioRoot 2>&1 | ForEach-Object { "$_" })
    $afExit = $LASTEXITCODE
    $afLines | Set-Content -Encoding UTF8 $audioFidelity254
    if ($afExit -ne 0) { throw "Stage 24.25.4 complete audio fidelity audit failed exit=$afExit report=$audioFidelity254" }
    Write-Host "[stage24.25.4-audio] Complete ARMv7 + MP3 payload fidelity audit PASS report=$audioFidelity254"
} else {
    'ANGRY_STAGE24_25_4_AUDIO_FIDELITY_CONTRACT 1' | Set-Content -Encoding UTF8 $audioFidelity254
    'policy=AUDIT_FIRST; original ARMv7 native audit unavailable; runtime raw-vs-clamped track-volume telemetry remains enabled' | Add-Content -Encoding UTF8 $audioFidelity254
    Write-Host '[stage24.25.4-audio] Native audio fidelity audit unavailable; runtime Lua/track telemetry remains enabled.'
}

# Stage 24.25.5: Stage24.25.4 proved two separate facts: untouched Lua can
# request track volume above 1.0, while the original AudioMixer clamps the
# stored value to [0,1]. Before adding MP3 playback, close the two remaining
# ownership gaps: who initializes/clears audioRampVolume/audioRampLength and
# how AudioReader MP3 EOF/reset/looping feeds AudioMixer.
$mp3DecodeLoop255 = Join-Path $outputDir 'stage24.25.5-mp3-decode-loop-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $mdlLines = @(& $python (Join-Path $root 'tools\stage24255_mp3_decode_loop_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $mdlExit = $LASTEXITCODE
    $mdlLines | Set-Content -Encoding UTF8 $mp3DecodeLoop255
    if ($mdlExit -ne 0) { throw "Stage 24.25.5 MP3 decode/loop audit failed exit=$mdlExit report=$mp3DecodeLoop255" }
    Write-Host "[stage24.25.5-audio] Original MP3 decode/reset/loop ownership audit PASS report=$mp3DecodeLoop255"
} else {
    'ANGRY_STAGE24_25_5_MP3_DECODE_LOOP_CONTRACT 1' | Set-Content -Encoding UTF8 $mp3DecodeLoop255
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable; runtime audio-ramp ownership telemetry remains enabled' | Add-Content -Encoding UTF8 $mp3DecodeLoop255
    Write-Host '[stage24.25.5-audio] MP3 decode/loop native audit unavailable; runtime audio-ramp ownership telemetry remains enabled.'
}

# Stage 24.25.6: Stage24.25.5 closes the Lua audio-ramp question but exposes
# the one native function the prior MP3 audit did not dump: every mixer path
# calls AudioClipInstance::fetchData(), and AudioClip::getData() then delegates
# to AudioReader::readData(). Therefore fetchData + queue cleanup own the EOF /
# rewind / loop boundary. Audit those exact untouched ARMv7 bodies before
# choosing any ARM64 MP3 decoder or playback implementation.
$audioClipLoop256 = Join-Path $outputDir 'stage24.25.6-audioclipinstance-eof-loop-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $aclLines = @(& $python (Join-Path $root 'tools\stage24256_audioclipinstance_eof_loop_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
    $aclExit = $LASTEXITCODE
    $aclLines | Set-Content -Encoding UTF8 $audioClipLoop256
    if ($aclExit -ne 0) { throw "Stage 24.25.6 AudioClipInstance EOF/loop audit failed exit=$aclExit report=$audioClipLoop256" }
    Write-Host "[stage24.25.6-audio] Original AudioClipInstance EOF/loop ownership audit PASS report=$audioClipLoop256"
} else {
    'ANGRY_STAGE24_25_6_AUDIOCLIPINSTANCE_EOF_LOOP_CONTRACT 1' | Set-Content -Encoding UTF8 $audioClipLoop256
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable; Stage24.25.7 compatibility MP3 playback still builds from the previously recovered contract' | Add-Content -Encoding UTF8 $audioClipLoop256
    Write-Host '[stage24.25.6-audio] AudioClipInstance native audit unavailable; Stage24.25.7 compatibility playback remains enabled but this local run lacks fresh ARMv7 re-audit evidence.'
}

# Stage 24.25.8: now that WAV + MP3 playback are live, close the remaining
# lifecycle boundaries before declaring audio complete. This is diagnostic-only:
# dump original ARMv7 start/stop output, master volume, clip query/stop/cleanup
# bodies and scan untouched scripts/audio payload for the runtime ground_collision
# request. No behavior is patched from this report.
$audioClosure258 = Join-Path $outputDir 'stage24.25.8-audio-closure-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $acl258Lines = @(& $python (Join-Path $root 'tools\stage24258_audio_closure_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $scripts $audioRoot 2>&1 | ForEach-Object { "$_" })
    $acl258Exit = $LASTEXITCODE
    $acl258Lines | Set-Content -Encoding UTF8 $audioClosure258
    if ($acl258Exit -ne 0) { throw "Stage 24.25.8 audio closure audit failed exit=$acl258Exit report=$audioClosure258" }
    Write-Host "[stage24.25.8-audio] Original lifecycle/ground-collision closure audit PASS report=$audioClosure258"
} else {
    'ANGRY_STAGE24_25_8_AUDIO_CLOSURE_CONTRACT 1' | Set-Content -Encoding UTF8 $audioClosure258
    'policy=DIAGNOSTIC_ONLY; original ARMv7 native audit unavailable; runtime lifecycle telemetry remains enabled' | Add-Content -Encoding UTF8 $audioClosure258
    Write-Host '[stage24.25.8-audio] Native closure audit unavailable; runtime lifecycle telemetry remains enabled.'
}

# Stage 24.26.0: Stage24.25.8 closes observable audio lifecycle behavior.
# The next actively exercised headless GameLua boundary was trajectory.  This
# retained 24.26.0 report exposes the exact original ARMv7 producer/storage
# bodies plus untouched script/image-metadata provenance; Stage24.26.2 below
# now implements only the contract subsequently closed by 24.26.0/24.26.1.
$trajectoryNative260 = Join-Path $outputDir 'stage24.26.0-trajectory-native-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $tr260Lines = @(& $python (Join-Path $root 'tools\stage24260_trajectory_system_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $scripts $imageRoot 2>&1 | ForEach-Object { "$_" })
    $tr260Exit = $LASTEXITCODE
    $tr260Lines | Set-Content -Encoding UTF8 $trajectoryNative260
    if ($tr260Exit -ne 0) { throw "Stage 24.26.0 trajectory native contract audit failed exit=$tr260Exit report=$trajectoryNative260" }
    Write-Host "[stage24.26.0-trajectory] Original GameLua trajectory contract audit PASS report=$trajectoryNative260"
} else {
    'ANGRY_STAGE24_26_0_TRAJECTORY_NATIVE_CONTRACT 1' | Set-Content -Encoding UTF8 $trajectoryNative260
    'policy=RETAINED_AUDIT_UNAVAILABLE; runtime Lua/argument telemetry remains enabled; Stage24.26.2 implementation requires its separate fail-closed resource preflight below' | Add-Content -Encoding UTF8 $trajectoryNative260
    Write-Host '[stage24.26.0-trajectory] Native trajectory audit unavailable; runtime Lua/argument telemetry remains enabled.'
}

# Stage 24.26.1: Stage24.26.0 recovered the producer/storage contract (three
# slots, two banks, normal vs puff arrays).  Before drawing anything, audit the
# untouched ARMv7 consumers of those exact fields, the complete drawGame body,
# retained TRAIL_* resources, and puff-specialty provenance.
$trajectoryRenderer261 = Join-Path $outputDir 'stage24.26.1-trajectory-renderer-puff-contract.txt'
if ($armv7Lib -and (Test-Path $llvmNm) -and (Test-Path $llvmObjdump)) {
    $tr261Lines = @(& $python (Join-Path $root 'tools\stage24261_trajectory_renderer_puff_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $scripts $imageRoot 2>&1 | ForEach-Object { "$_" })
    $tr261Exit = $LASTEXITCODE
    $tr261Lines | Set-Content -Encoding UTF8 $trajectoryRenderer261
    if ($tr261Exit -ne 0) { throw "Stage 24.26.1 trajectory renderer/puff audit failed exit=$tr261Exit report=$trajectoryRenderer261" }
    Write-Host "[stage24.26.1-trajectory] Original renderer/puff contract audit PASS report=$trajectoryRenderer261"
} else {
    'ANGRY_STAGE24_26_1_TRAJECTORY_RENDERER_PUFF_CONTRACT 1' | Set-Content -Encoding UTF8 $trajectoryRenderer261
    'policy=RETAINED_AUDIT_UNAVAILABLE; Lua puff-producer telemetry remains enabled; Stage24.26.2 implementation requires its separate fail-closed resource preflight below' | Add-Content -Encoding UTF8 $trajectoryRenderer261
    Write-Host '[stage24.26.1-trajectory] Native renderer/puff audit unavailable; Lua producer telemetry remains enabled.'
}

# Stage 24.26.2: implement only the renderer/storage behavior already recovered
# by 24.26.0/24.26.1.  Fail closed on the one resource literal that was still
# unresolved in the previous report: untouched drawGame builds a 12-byte
# string immediately after TRAIL_WHITE_3.  Verify that exact PIC cluster is
# INGAME_BIRDS_1 / TRAIL_WHITE_1..3 / BIRD_SPECIAL and that the retained
# sprite metadata contains every referenced sprite before compiling ARM64.
$trajectoryImpl262 = Join-Path $outputDir 'stage24.26.2-trajectory-renderer-implementation-contract.txt'
if (!$armv7Lib) {
    throw 'Stage 24.26.2 requires the original ARMv7 libangrybirds.so for fail-closed trajectory resource verification.'
}
$tr262Lines = @(& $python (Join-Path $root 'tools\stage24262_trajectory_renderer_implementation_contract.py') $armv7Lib.FullName $birdsDat 2>&1 | ForEach-Object { "$_" })
$tr262Exit = $LASTEXITCODE
$tr262Lines | Set-Content -Encoding UTF8 $trajectoryImpl262
if ($tr262Exit -ne 0) { throw "Stage 24.26.2 trajectory renderer implementation preflight failed exit=$tr262Exit report=$trajectoryImpl262" }
Write-Host "[stage24.26.2-trajectory] Original renderer implementation preflight PASS report=$trajectoryImpl262"

# Stage 24.22.8: Stage24.22.7 closes the tolerance-scale ownership question.
# Untouched ARMv7 proves linearSlop=0.05f, timeToSleep=0.25f and
# linearSleepTolerance=0.1f while velocityThreshold, maxLinearCorrection,
# contactBaumgarte and angularSleepTolerance retain the 2.1.2 stock values.
# Patch the freshly extracted pinned source coherently BEFORE compiling it.
# Do not touch the original Lua speed<0.05 bird-removal gate.
$rovioToleranceReport = Join-Path $outputDir 'stage24.22.8-rovio-box2d-tolerances.txt'
$rovioToleranceLines = @(& $python (Join-Path $root 'tools\patch_box2d212_rovio_tolerances.py') $boxDir 2>&1 | ForEach-Object { "$_" })
$rovioToleranceExit = $LASTEXITCODE
$rovioToleranceLines | Set-Content -Encoding UTF8 $rovioToleranceReport
if ($rovioToleranceExit -ne 0) { throw "Stage 24.22.8 Rovio Box2D tolerance patch failed exit=$rovioToleranceExit report=$rovioToleranceReport" }
Write-Host "[stage24.22.8-rovio-physics] Proven Rovio Box2D tolerance patch PASS report=$rovioToleranceReport"


# Stage 24.27.0: after the proven Rovio tolerance patch is applied, capture the
# exact effective ARM64 sleep source side-by-side with untouched ARMv7 solver/
# awake bodies. Runtime Lua + body/contact telemetry is emitted by the native
# executable; this static report changes no physics state.
$birdRestNative270 = Join-Path $outputDir 'stage24.27.0-bird-rest-native-contract.txt'
$br270Lines = @(& $python (Join-Path $root 'tools\stage24270_bird_rest_level_end_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
$br270Exit = $LASTEXITCODE
$br270Lines | Set-Content -Encoding UTF8 $birdRestNative270
if ($br270Exit -ne 0) { throw "Stage 24.27.0 bird-rest native contract audit failed exit=$br270Exit report=$birdRestNative270" }
Write-Host "[stage24.27.0-bird-rest] Native/effective-Box2D contract audit PASS report=$birdRestNative270"

# Stage 24.28.0: giant read-only inventory of the untouched menu/UI/navigation
# surface before implementing any remaining screens. This deliberately spans
# native GameLua/platform boundaries, original scripts/levels, menu metadata,
# localization and the Level1 first-entry film/cutscene provenance.
$menuUiNative280 = Join-Path $outputDir 'stage24.28.0-menu-ui-native-corpus-contract.txt'
$mu280Lines = @(& $python (Join-Path $root 'tools\stage24280_menu_ui_surface_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $dataRoot $scripts $imageRoot $localizationRoot 2>&1 | ForEach-Object { "$_" })
$mu280Exit = $LASTEXITCODE
$mu280Lines | Set-Content -Encoding UTF8 $menuUiNative280
if ($mu280Exit -ne 0) { throw "Stage 24.28.0 giant menu/UI native+corpus audit failed exit=$mu280Exit report=$menuUiNative280" }
Write-Host "[stage24.28.0-menu-ui] Giant original native/script/asset/localization inventory PASS report=$menuUiNative280"

# Stage 24.28.1: startup branding is part of the vanilla boot contract and must
# be understood before replacing the direct-Level1 harness boot. This audit is
# read-only and resolves the exact splash symbols to untouched image metadata.
$startupBranding281 = Join-Path $outputDir 'stage24.28.1-startup-branding-asset-contract.txt'
$sb281Lines = @(& $python (Join-Path $root 'tools\stage24281_startup_branding_contract.py') $scripts $imageRoot $localizationRoot 2>&1 | ForEach-Object { "$_" })
$sb281Exit = $LASTEXITCODE
$sb281Lines | Set-Content -Encoding UTF8 $startupBranding281
if ($sb281Exit -ne 0) { throw "Stage 24.28.1 startup branding asset contract audit failed exit=$sb281Exit report=$startupBranding281" }
Write-Host "[stage24.28.1-boot] Startup branding asset provenance PASS report=$startupBranding281"


# Stage 24.28.2: the first visible Level Selection frame proved two separate
# resource-frontier facts: FONT_LS_SMALL metadata is loaded but its exact PVR
# was not transported, and Lua requests LS_THEME_1_LEFT through
# BUTTONS_SHEET_1 even though the original corpus owns it uniquely in
# LEVELSELECTION_SHEET_1.dat.  The font transport is a proven fix.  The sprite
# mismatch is NOT guessed: recover the untouched ARMv7 two-string drawSprite
# lookup path and expose the result to the ARM64 renderer as a compile-time
# contract.
$levelSelectionResource282 = Join-Path $outputDir 'stage24.28.2-level-selection-resource-contract.txt'
$ls282Lines = @(& $python (Join-Path $root 'tools\stage24282_level_selection_resource_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $imageRoot 2>&1 | ForEach-Object { "$_" })
$ls282Exit = $LASTEXITCODE
$ls282Lines | Set-Content -Encoding UTF8 $levelSelectionResource282
if ($ls282Exit -ne 0) { throw "Stage 24.28.2 Level Selection resource contract audit failed exit=$ls282Exit report=$levelSelectionResource282" }
$ls282Text = $ls282Lines -join "`n"
$stage24282GlobalLookup = $ls282Text -match 'nativeLookupMode=GLOBAL_SPRITE_REGISTRY'
$stage24282GlobalLookupCmake = if ($stage24282GlobalLookup) { 'ON' } else { 'OFF' }
Write-Host "[stage24.28.2-level-selection] Resource contract PASS globalRegistry=$stage24282GlobalLookup report=$levelSelectionResource282"

# Stage 24.28.3: the now-visible full menu tree proved a renderer ownership
# leak: updateMenu was still preceded by the reconstructed gameplay world/HUD,
# while untouched drawMenu() called drawBackgroundNative/drawForegroundNative
# into historical blanket stubs. Recover the exact ARMv7 native ownership calls
# and inventory the remaining menu sprite-name misses before enabling the bridge.
$menuRenderOwnership283 = Join-Path $outputDir 'stage24.28.3-menu-render-ownership-contract.txt'
$mr283Lines = @(& $python (Join-Path $root 'tools\stage24283_menu_render_ownership_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $imageRoot $scripts 2>&1 | ForEach-Object { "$_" })
$mr283Exit = $LASTEXITCODE
$mr283Lines | Set-Content -Encoding UTF8 $menuRenderOwnership283
if ($mr283Exit -ne 0) { throw "Stage 24.28.3 menu render ownership contract audit failed exit=$mr283Exit report=$menuRenderOwnership283" }
Write-Host "[stage24.28.3-render-ownership] ARMv7 menu background/foreground ownership + remaining miss inventory PASS report=$menuRenderOwnership283"

# Stage 24.28.4: v0.26.86 proved that updateMenu contains two ownership classes.
# Pause/terminal pages overlay the final gameplay frame, while the root menu tree
# owns a fresh theme frame.  The same run also proved openURL is a real missing
# platform boundary reachable from the trailer button.  Audit both without
# launching any external application in this version.
$overlayPlatform284 = Join-Path $outputDir 'stage24.28.4-overlay-platform-boundary-contract.txt'
$op284Lines = @(& $python (Join-Path $root 'tools\stage24284_overlay_platform_boundary_contract.py') $llvmNm $armv7Lib.FullName $scripts (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$op284Exit = $LASTEXITCODE
$op284Lines | Set-Content -Encoding UTF8 $overlayPlatform284
if ($op284Exit -ne 0) { throw "Stage 24.28.4 overlay/platform boundary audit failed exit=$op284Exit report=$overlayPlatform284" }
Write-Host "[stage24.28.4-overlay-platform] Contract audit PASS report=$overlayPlatform284"

# Stage 24.28.5: close the exact v0.26.87 findings. Untouched updateMenu
# calls setBGColor(currentMenuPage.bgColor.*), and external callbacks use
# _G.res.openURL rather than a global openURL. Audit the original corpus plus
# the staged ARM64 bindings before packaging user assets.
$menuBgOpenUrl285 = Join-Path $outputDir 'stage24.28.5-menu-bg-openurl-contract.txt'
$mb285Lines = @(& $python (Join-Path $root 'tools\stage24285_menu_bg_openurl_contract.py') $scripts (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$mb285Exit = $LASTEXITCODE
$mb285Lines | Set-Content -Encoding UTF8 $menuBgOpenUrl285
if ($mb285Exit -ne 0) { throw "Stage 24.28.5 menu-bg/openURL contract audit failed exit=$mb285Exit report=$menuBgOpenUrl285" }
Write-Host "[stage24.28.5-menu-bg-openurl] Contract audit PASS report=$menuBgOpenUrl285"

# Stage 24.29.0: close the startup core-splash contract before enabling the
# visible boot gate. The audit is fail-closed for Rovio/Angry Birds ownership
# and deliberately reports Clickgamer/Loading as edition-dependent when this
# concrete 864x480 corpus has no owning sprite metadata.
$startupBoot290 = Join-Path $outputDir 'stage24.29.0-startup-boot-contract.txt'
$sb290Lines = @(& $python (Join-Path $root 'tools\stage24290_startup_boot_contract.py') $scripts $imageRoot (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$sb290Exit = $LASTEXITCODE
$sb290Lines | Set-Content -Encoding UTF8 $startupBoot290
if ($sb290Exit -ne 0) { throw "Stage 24.29.0 startup boot contract failed exit=$sb290Exit report=$startupBoot290" }
Write-Host "[stage24.29.0-boot] Startup core splash contract PASS report=$startupBoot290"

# Stage 24.29.1: the first real splash frame proved that both original
# SPLASHES_SHEET PVRs use legacy OpenGL PVR v2 GL_RGB_565 (type 0x13), a
# concrete format that the runtime previously classified but did not upload.
# Audit the user's exact payloads and the staged generic decoder before APK
# materialization. No conversion is performed: the original 16-bit texels are
# packaged byte-identically and uploaded with GL_RGB/GL_UNSIGNED_SHORT_5_6_5.
$rgb565Splash291 = Join-Path $outputDir 'stage24.29.1-rgb565-splash-contract.txt'
$rs291Lines = @(& $python (Join-Path $root 'tools\stage24291_rgb565_splash_contract.py') $imageRoot (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$rs291Exit = $LASTEXITCODE
$rs291Lines | Set-Content -Encoding UTF8 $rgb565Splash291
if ($rs291Exit -ne 0) { throw "Stage 24.29.1 RGB565 splash contract failed exit=$rs291Exit report=$rgb565Splash291" }
Write-Host "[stage24.29.1-rgb565] Exact PVR v2 RGB565 splash contract PASS report=$rgb565Splash291"

# Stage 24.30.0: first-entry story/cutscene contract. v0.26.90 reached
# loadCutScenes -> loadImages -> _G.res.createSpriteSheet from the real menu path.
# Inventory the untouched Lua/corpus and native ARMv7 create/release surfaces
# before allowing the audit-only runtime probe to reveal the next dependency.
if (!$armv7Lib) { throw 'Stage 24.30.0 requires the original ARMv7 libangrybirds.so for cutscene native contract audit.' }
$cutsceneStory300 = Join-Path $outputDir 'stage24.30.0-cutscene-story-native-contract.txt'
$cs300Lines = @(& $python (Join-Path $root 'tools\stage24300_cutscene_story_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $scripts $imageRoot (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$cs300Exit = $LASTEXITCODE
$cs300Lines | Set-Content -Encoding UTF8 $cutsceneStory300
if ($cs300Exit -ne 0) { throw "Stage 24.30.0 cutscene/story contract audit failed exit=$cs300Exit report=$cutsceneStory300" }
Write-Host "[stage24.30.0-cutscene] Original cutscene/story contract PASS report=$cutsceneStory300"

# Stage 24.30.1: fail closed before implementation. Verify that the six
# original dynamic sheets have concrete texture payloads and that the staged
# ARM64 source contains dynamic registry release + progressive setRenderState.
$cutsceneDynamic301 = Join-Path $outputDir 'stage24.30.1-cutscene-dynamic-renderstate-contract.txt'
$cd301Lines = @(& $python (Join-Path $root 'tools\stage24301_cutscene_dynamic_contract.py') $imageRoot (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$cd301Exit = $LASTEXITCODE
$cd301Lines | Set-Content -Encoding UTF8 $cutsceneDynamic301
if ($cd301Exit -ne 0) { throw "Stage 24.30.1 dynamic cutscene/render-state preflight failed exit=$cd301Exit report=$cutsceneDynamic301" }
Write-Host "[stage24.30.1-cutscene] Dynamic sheet + render-state preflight PASS report=$cutsceneDynamic301"

# Stage 24.30.4: v0.26.94 proved that build-time staging and runtime
# bootstrap ownership had diverged. Verify that the C++ runtime consumes the
# generated bootstrap-menu-meta.txt for both APK extraction and SpriteDB load,
# rather than maintaining a second hardcoded sheet list.
$bootstrapMeta304 = Join-Path $outputDir 'stage24.30.4-bootstrap-meta-manifest-contract.txt'
$bm304Lines = @(& $python (Join-Path $root 'tools\stage24304_bootstrap_meta_manifest_contract.py') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$bm304Exit = $LASTEXITCODE
$bm304Lines | Set-Content -Encoding UTF8 $bootstrapMeta304
if ($bm304Exit -ne 0) { throw "Stage 24.30.4 bootstrap meta manifest preflight failed exit=$bm304Exit report=$bootstrapMeta304" }
Write-Host "[stage24.30.4-bootstrap-meta] Runtime manifest ownership preflight PASS report=$bootstrapMeta304"

# Stage 24.31.0: persistence/save contract audit.  The menu/cutscene tree is
# now closed enough to observe real settings/highscore writes.  Audit the
# untouched Lua producers plus ARMv7 GameLua file methods before implementing
# any Android-local profile storage.  Runtime save/check/create bindings remain
# no-write probes in this revision.
$savePersistence310 = Join-Path $outputDir 'stage24.31.0-save-persistence-native-contract.txt'
$sp310Lines = @(& $python (Join-Path $root 'tools\stage24310_persistence_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $scripts (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$sp310Exit = $LASTEXITCODE
$sp310Lines | Set-Content -Encoding UTF8 $savePersistence310
if ($sp310Exit -ne 0) { throw "Stage 24.31.0 save/persistence contract audit failed exit=$sp310Exit report=$savePersistence310" }
Write-Host "[stage24.31.0-persistence] Original save/progress contract audit PASS report=$savePersistence310"

# Stage 24.31.1: real restart persistence wiring.  Keep the Stage 24.31.0
# ARMv7/Lua audit as provenance, then fail closed unless the live runtime binds
# real AppData save, loads settings/highscores before menu/audio initialization,
# and uses an atomic private-file commit.
$savePersistence311Contract = Join-Path $outputDir 'stage24.31.1-real-save-restart-contract.txt'
$sp311Lines = @(& $python (Join-Path $root 'tools\stage24311_real_persistence_contract.py') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$sp311Exit = $LASTEXITCODE
$sp311Lines | Set-Content -Encoding UTF8 $savePersistence311Contract
if ($sp311Exit -ne 0) { throw "Stage 24.31.1 real persistence preflight failed exit=$sp311Exit report=$savePersistence311Contract" }
Write-Host "[stage24.31.1-persistence] Real AppData/restart wiring preflight PASS report=$savePersistence311Contract"

# Stage 24.31.2: restore the original first-run Red tutorial boundary now that
# live gameplay/menu rendering and persistence exist. Fail closed unless the
# ancient Stage8 queue clear is gone and the exact COMP/TUTORIAL_OK surfaces
# are wired while the ARMv7 symbol/corpus evidence is still present.
$tutorial312Contract = Join-Path $outputDir 'stage24.31.2-first-run-tutorial-restoration-contract.txt'
$tu312Lines = @(& $python (Join-Path $root 'tools\stage24312_tutorial_restoration_contract.py') $llvmNm $armv7Lib.FullName $scripts (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$tu312Exit = $LASTEXITCODE
$tu312Lines | Set-Content -Encoding UTF8 $tutorial312Contract
if ($tu312Exit -ne 0) { throw "Stage 24.31.2 tutorial restoration preflight failed exit=$tu312Exit report=$tutorial312Contract" }
Write-Host "[stage24.31.2-tutorial] First-run tutorial restoration preflight PASS report=$tutorial312Contract"

# Stage 24.31.3: UI micro-fidelity is intentionally audit-first.  Recover the
# untouched ARMv7 SpriteSheet/CompoSprite/render-state contract and instrument
# the live settings-gear / Golden-Egg / seam paths before selecting any global
# UV/pivot/visibility correction.
$ui313Contract = Join-Path $outputDir 'stage24.31.3-ui-microfidelity-contract.txt'
$ui313Lines = @(& $python (Join-Path $root 'tools\stage24313_ui_microfidelity_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $scripts (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui313Exit = $LASTEXITCODE
$ui313Lines | Set-Content -Encoding UTF8 $ui313Contract
if ($ui313Exit -ne 0) { throw "Stage 24.31.3 UI micro-fidelity contract audit failed exit=$ui313Exit report=$ui313Contract" }
Write-Host "[stage24.31.3-ui] UI micro-fidelity audit preflight PASS report=$ui313Contract"

# Stage 24.31.4: apply only the evidence-backed seam fix: target-sized UI
# sprites sample texel centers under the already-recovered GL_LINEAR filter.
# Natural-size sprite UVs and all geometry/render-state semantics stay unchanged.
$ui314Contract = Join-Path $outputDir 'stage24.31.4-ui-seam-fidelity-contract.txt'
$ui314Lines = @(& $python (Join-Path $root 'tools\stage24314_ui_seam_fidelity_contract.py') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui314Exit = $LASTEXITCODE
$ui314Lines | Set-Content -Encoding UTF8 $ui314Contract
if ($ui314Exit -ne 0) { throw "Stage 24.31.4 UI seam fidelity preflight failed exit=$ui314Exit report=$ui314Contract" }
Write-Host "[stage24.31.4-seam] Target-sized UI center-sampling preflight PASS report=$ui314Contract"

# Stage 24.31.4a: stop treating the Stage24.31.4 half-texel experiment as the
# canonical architecture. Recover the untouched ARMv7 backend that receives
# integer source rectangles from SpriteSheet::drawSprite. The report captures
# EGL_Image::draw plus RenderBatcher candidates/call targets before any 24.31.4b
# renderer rewrite is selected.
$ui314aContract = Join-Path $outputDir 'stage24.31.4a-original-egl-image-draw-contract.txt'
$ui314aLines = @(& $python (Join-Path $root 'tools\stage24314a_egl_image_draw_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui314aExit = $LASTEXITCODE
$ui314aLines | Set-Content -Encoding UTF8 $ui314aContract
if ($ui314aExit -ne 0) { throw "Stage 24.31.4a original EGL_Image draw audit failed exit=$ui314aExit report=$ui314aContract" }
Write-Host "[stage24.31.4a-egl-image] Original EGL_Image/subrect backend audit PASS report=$ui314aContract"


# Stage 24.31.4b: Stage24.31.4a proved that the original integer-subrect
# overload uses edge-to-edge UVs, so +0.5/-0.5 cannot be the canonical fix.
# Recover the texture sampler state and the EGL_Texture backing dimensions that
# Image::draw actually uses as the normalization denominator before rewriting
# any ARM64 renderer behavior.
$ui314bContract = Join-Path $outputDir 'stage24.31.4b-original-texture-sampling-backing-contract.txt'
$ui314bLines = @(& $python (Join-Path $root 'tools\stage24314b_texture_sampling_backing_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui314bExit = $LASTEXITCODE
$ui314bLines | Set-Content -Encoding UTF8 $ui314bContract
if ($ui314bExit -ne 0) { throw "Stage 24.31.4b original texture sampling/backing audit failed exit=$ui314bExit report=$ui314bContract" }
Write-Host "[stage24.31.4b-texture] Original sampler/backing audit PASS report=$ui314bContract"

# Stage 24.31.4c: implement the recovered EGL_Image/EGL_Texture architecture,
# not the earlier half-texel A/B workaround. Logical image dimensions stay
# separate from the physical next-POT texture backing; integer source rectangles
# use edge-to-edge UVs normalized by that backing.
$ui314cContract = Join-Path $outputDir 'stage24.31.4c-original-egl-image-pot-backing-contract.txt'
$ui314cLines = @(& $python (Join-Path $root 'tools\stage24314c_original_pot_backing_contract.py') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui314cExit = $LASTEXITCODE
$ui314cLines | Set-Content -Encoding UTF8 $ui314cContract
if ($ui314cExit -ne 0) { throw "Stage 24.31.4c original EGL_Image POT-backing reconstruction preflight failed exit=$ui314cExit report=$ui314cContract" }
Write-Host "[stage24.31.4c-texture] Original EGL_Image POT-backing reconstruction preflight PASS report=$ui314cContract"

# Stage 24.31.4f: the 1:1 A/B test proved raster ownership. Preserve the
# original 854x480 renderer as an internal 1:1 raster and scale only the fully
# composited frame in an outer presentation layer. Touch maps from that visible
# output viewport back to the untouched logical Context.
$ui314fContract = Join-Path $outputDir 'stage24.31.4f-composited-presentation-contract.txt'
$ui314fLines = @(& $python (Join-Path $root 'tools\stage24314f_composited_presentation_contract.py') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui314fExit = $LASTEXITCODE
$ui314fLines | Set-Content -Encoding UTF8 $ui314fContract
if ($ui314fExit -ne 0) { throw "Stage 24.31.4f composited presentation preflight failed exit=$ui314fExit report=$ui314fContract" }
Write-Host "[stage24.31.4f-presentation] Composited modern presentation preflight PASS report=$ui314fContract"

# Stage 24.31.5: menu micro-fidelity returns to the transform frontier now that
# raster/presentation ownership is closed.  Audit the exact untouched ARMv7
# RenderState2D producer/consumer chain before changing the current ARM64 model.
$ui315Contract = Join-Path $outputDir 'stage24.31.5-original-renderstate2d-contract.txt'
$ui315Lines = @(& $python (Join-Path $root 'tools\stage24315_renderstate2d_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui315Exit = $LASTEXITCODE
$ui315Lines | Set-Content -Encoding UTF8 $ui315Contract
if ($ui315Exit -ne 0) { throw "Stage 24.31.5 original RenderState2D contract audit failed exit=$ui315Exit report=$ui315Contract" }
Write-Host "[stage24.31.5-ui] Original RenderState2D transform audit PASS report=$ui315Contract"

# Stage 24.31.5b: consume the recovered EGL_Image::draw affine contract.  The
# original backend applies RenderState2D per image-local quad while preserving
# each draw destination origin.  Reconstruct that once globally; never branch
# on BUTTON_OPTIONS / GOLDEN_EGG_STAR_EFFECT names.
$ui315bContract = Join-Path $outputDir 'stage24.31.5b-renderstate2d-reconstruction-contract.txt'
$ui315bLines = @(& $python (Join-Path $root 'tools\stage24315b_renderstate2d_reconstruction_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ui315bExit = $LASTEXITCODE
$ui315bLines | Set-Content -Encoding UTF8 $ui315bContract
if ($ui315bExit -ne 0) { throw "Stage 24.31.5b RenderState2D reconstruction preflight failed exit=$ui315bExit report=$ui315bContract" }
Write-Host "[stage24.31.5b-ui] Original per-image RenderState2D reconstruction preflight PASS report=$ui315bContract"

# Stage 24.31.5 passive score audit runs alongside the UI work. It observes the
# untouched scoring pipeline only; no constants, thresholds or score buckets are
# changed. The runtime capture becomes useful whenever the user plays a level.
$score315Contract = Join-Path $outputDir 'stage24.31.5-score-passive-contract.txt'
$score315Lines = @(& $python (Join-Path $root 'tools\stage24315_score_passive_contract.py') $scripts (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$score315Exit = $LASTEXITCODE
$score315Lines | Set-Content -Encoding UTF8 $score315Contract
if ($score315Exit -ne 0) { throw "Stage 24.31.5 passive score audit preflight failed exit=$score315Exit report=$score315Contract" }
Write-Host "[stage24.31.5-score] Passive score-fidelity observer preflight PASS report=$score315Contract"

# Stage 24.32.0: progression expansion starts from already-working 1-2.
# The untouched levelSelectionPagesBasic runtime inventory recovered 1-3 as
# Level53 (levelIndex=3, pageLevelIndex=3, theme=1, world=1).  Transport only
# that original level and keep getNextLevel/unlock/save ownership in stock Lua.
$progress320Contract = Join-Path $outputDir 'stage24.32.0-progression-expansion-contract.txt'
$progress320Lines = @(& $python (Join-Path $root 'tools\stage24320_progression_expansion_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$progress320Exit = $LASTEXITCODE
$progress320Lines | Set-Content -Encoding UTF8 $progress320Contract
if ($progress320Exit -ne 0) { throw "Stage 24.32.0 progression expansion preflight failed exit=$progress320Exit report=$progress320Contract" }
Write-Host "[stage24.32.0-progression] Level53 transport + untouched progression ownership preflight PASS report=$progress320Contract"

# Stage 24.32.1: widen the same original Pack 1 transport through human 1-10,
# restore an evidence-derived two-pointer input bridge into the already-original
# zoomLevel/doItAllCamera consumer, and audit the untouched CLUSTER_BOMB branch.
# This pass must not hardcode a Blue split or mutate worldScale directly.
$pack321Contract = Join-Path $outputDir 'stage24.32.1-pack1-multitouch-specialty-contract.txt'
$pack321Lines = @(& $python (Join-Path $root 'tools\stage24321_pack1_multitouch_specialty_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') $scripts 2>&1 | ForEach-Object { "$_" })
$pack321Exit = $LASTEXITCODE
$pack321Lines | Set-Content -Encoding UTF8 $pack321Contract
if ($pack321Exit -ne 0) { throw "Stage 24.32.1 Pack1/multitouch/specialty preflight failed exit=$pack321Exit report=$pack321Contract" }
Write-Host "[stage24.32.1] Pack1 1-10 + multitouch + original specialty audit preflight PASS report=$pack321Contract"

# Stage 24.33.0: the 1-10 live run proved untouched CLUSTER_BOMB dispatch and
# failed only because the reconstructed createCircle Lua object omitted the
# physical/render arguments that updateGame re-reads from flyingBird. Restore
# that generic object-materialization contract; do not implement Blue natively.
$circle330Contract = Join-Path $outputDir 'stage24.33.0-createcircle-lua-metadata-contract.txt'
$circle330Lines = @(& $python (Join-Path $root 'tools\stage24330_createcircle_lua_metadata_contract.py') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$circle330Exit = $LASTEXITCODE
$circle330Lines | Set-Content -Encoding UTF8 $circle330Contract
if ($circle330Exit -ne 0) { throw "Stage 24.33.0 createCircle Lua metadata preflight failed exit=$circle330Exit report=$circle330Contract" }
Write-Host "[stage24.33.0] Generic createCircle Lua metadata reconstruction preflight PASS report=$circle330Contract"

# Stage 24.34.0: extend untouched Pack 1 transport through human 1-16 and
# use the first Yellow/BOOST level as an audit of the original specialty branch.
# No Yellow boost is synthesized natively; updateGame remains authoritative.
$yellow340Contract = Join-Path $outputDir 'stage24.34.0-pack1-yellow-boost-contract.txt'
$yellow340Lines = @(& $python (Join-Path $root 'tools\stage24340_pack1_yellow_boost_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') $scripts 2>&1 | ForEach-Object { "$_" })
$yellow340Exit = $LASTEXITCODE
$yellow340Lines | Set-Content -Encoding UTF8 $yellow340Contract
if ($yellow340Exit -ne 0) { throw "Stage 24.34.0 Pack1/Yellow BOOST preflight failed exit=$yellow340Exit report=$yellow340Contract" }
Write-Host "[stage24.34.0] Pack1 1-16 + untouched Yellow BOOST audit preflight PASS report=$yellow340Contract"


# Stage 24.34.1: close the first 21-level Pack 1 chapter using the untouched
# levelOrder.pack1 mapping already captured from initializeMenu. This is a pure
# transport/progression expansion: no bird behavior, score, save or Next logic
# is replaced natively.
$chapter341Contract = Join-Path $outputDir 'stage24.34.1-pack1-chapter1-closure-contract.txt'
$chapter341Lines = @(& $python (Join-Path $root 'tools\stage24341_pack1_chapter1_closure_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$chapter341Exit = $LASTEXITCODE
$chapter341Lines | Set-Content -Encoding UTF8 $chapter341Contract
if ($chapter341Exit -ne 0) { throw "Stage 24.34.1 Pack1 chapter-1 closure preflight failed exit=$chapter341Exit report=$chapter341Contract" }
Write-Host "[stage24.34.1] Pack1 1-21 original progression closure preflight PASS report=$chapter341Contract"

# Stage 24.35.0: enter untouched Poached Eggs theme 2 and stop at 2-5, the
# first Bomb/BOMB specialty level.  This stage transports original level files
# and the exact theme2 parallax sheet only; updateGame/makeExplosion/removeBird
# remain the sole owners of Bomb behavior.
$bomb350Contract = Join-Path $outputDir 'stage24.35.0-pack2-bomb-contract.txt'
$bomb350Lines = @(& $python (Join-Path $root 'tools\stage24350_pack2_bomb_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') $scripts 2>&1 | ForEach-Object { "$_" })
$bomb350Exit = $LASTEXITCODE
$bomb350Lines | Set-Content -Encoding UTF8 $bomb350Contract
if ($bomb350Exit -ne 0) { throw "Stage 24.35.0 Pack2/Bomb preflight failed exit=$bomb350Exit report=$bomb350Contract" }
Write-Host "[stage24.35.0] Pack2 2-1..2-5 + untouched Bomb/BOMB audit preflight PASS report=$bomb350Contract"


# Stage 24.35.1: close the theme2 scene-metadata bootstrap gap exposed by the
# first real Level52 load. v0.26.115 staged/uploaded INGAME_PARALLAX_2.pvr and
# packaged its DAT, but the native APK extraction + SpriteDB metadata bootstrap
# lists still named only the historical theme1 families.
$theme351Contract = Join-Path $outputDir 'stage24.35.1-theme2-scene-metadata-contract.txt'
$theme351Lines = @(& $python (Join-Path $root 'tools\stage24351_theme2_scene_metadata_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$theme351Exit = $LASTEXITCODE
$theme351Lines | Set-Content -Encoding UTF8 $theme351Contract
if ($theme351Exit -ne 0) { throw "Stage 24.35.1 theme2 scene metadata preflight failed exit=$theme351Exit report=$theme351Contract" }
Write-Host "[stage24.35.1] Theme2 scene metadata bootstrap/extraction preflight PASS report=$theme351Contract"


# Stage 24.35.2: Level34 is the first transported level to request static
# MaskedImage terrain filled from INGAME_THEME_GROUND_2. The original producer
# already records that textureName per object; ensure the ARM64 consumer follows
# that metadata instead of freezing all fills to theme1.
$ground352Contract = Join-Path $outputDir 'stage24.35.2-theme-ground-fill-contract.txt'
$ground352Lines = @(& $python (Join-Path $root 'tools\stage24352_theme_ground_fill_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$ground352Exit = $LASTEXITCODE
$ground352Lines | Set-Content -Encoding UTF8 $ground352Contract
if ($ground352Exit -ne 0) { throw "Stage 24.35.2 theme-ground fill preflight failed exit=$ground352Exit report=$ground352Contract" }
Write-Host "[stage24.35.2] Generic theme-ground MaskedImage fill preflight PASS report=$ground352Contract"

# Stage 24.36.0: continue Pack2 through 2-14, the first White/DROPPABLE_EGG
# specialty level. Transport only original level payloads; untouched updateGame
# remains the sole owner of egg creation/launch behavior.
$white360Contract = Join-Path $outputDir 'stage24.36.0-pack2-white-contract.txt'
$white360Lines = @(& $python (Join-Path $root 'tools\stage24360_pack2_white_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') $scripts 2>&1 | ForEach-Object { "$_" })
$white360Exit = $LASTEXITCODE
$white360Lines | Set-Content -Encoding UTF8 $white360Contract
if ($white360Exit -ne 0) { throw "Stage 24.36.0 Pack2/White preflight failed exit=$white360Exit report=$white360Contract" }
Write-Host "[stage24.36.0] Pack2 2-6..2-14 + untouched White/DROPPABLE_EGG audit preflight PASS report=$white360Contract"

# Stage 24.36.1: pure Pack2 page-2 closure through 2-21. No new gameplay
# behavior is introduced; stock Next/theme2Complete/save ownership remains Lua.
$chapter361Contract = Join-Path $outputDir 'stage24.36.1-pack2-chapter2-closure-contract.txt'
$chapter361Lines = @(& $python (Join-Path $root 'tools\stage24361_pack2_chapter2_closure_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$chapter361Exit = $LASTEXITCODE
$chapter361Lines | Set-Content -Encoding UTF8 $chapter361Contract
if ($chapter361Exit -ne 0) { throw "Stage 24.36.1 Pack2 chapter2 closure preflight failed exit=$chapter361Exit report=$chapter361Contract" }
Write-Host "[stage24.36.1] Pack2 2-15..2-21 + stock theme2Complete closure preflight PASS report=$chapter361Contract"

# Stage 24.37.0: re-audit the original EGL_Image RenderState2D consumer after
# live menu evidence exposed a negative-scale ordering mismatch.  The generic
# consumer must apply scale after local rotation/pivot + draw-origin translation;
# no LS_BACKGROUND geometry branch is allowed.
$render370Contract = Join-Path $outputDir 'stage24.37.0-renderstate-negative-scale-contract.txt'
$render370Lines = @(& $python (Join-Path $root 'tools\stage24370_renderstate_negative_scale_contract.py') $ui314aContract (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$render370Exit = $LASTEXITCODE
$render370Lines | Set-Content -Encoding UTF8 $render370Contract
if ($render370Exit -ne 0) { throw "Stage 24.37.0 RenderState2D negative-scale preflight failed exit=$render370Exit report=$render370Contract" }
Write-Host "[stage24.37.0] Generic post-affine RenderState2D scale preflight PASS report=$render370Contract"

# Stage 24.38.0: first five levels of Poached Eggs page/theme 3. The exact
# map is read from untouched levelOrder.pack3; this pass additionally requires
# the concrete theme3 parallax/fill families already inventoried from the
# user's original 864x480 asset tree. No gameplay or transition override.
$theme380Contract = Join-Path $outputDir 'stage24.38.0-pack3-theme3-contract.txt'
$theme380Lines = @(& $python (Join-Path $root 'tools\stage24380_pack3_theme3_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$theme380Exit = $LASTEXITCODE
$theme380Lines | Set-Content -Encoding UTF8 $theme380Contract
if ($theme380Exit -ne 0) { throw "Stage 24.38.0 Pack3/theme3 preflight failed exit=$theme380Exit report=$theme380Contract" }
Write-Host "[stage24.38.0] Pack3 3-1..3-5 + exact theme3 render-family preflight PASS report=$theme380Contract"


# Stage 24.38.1: close the third 21-level Poached Eggs page. Runtime Lua
# levelOrder.pack3/getNextLevel/theme3Complete/save remain authoritative.
$chapter381Contract = Join-Path $outputDir 'stage24.38.1-pack3-chapter3-closure-contract.txt'
$chapter381Lines = @(& $python (Join-Path $root 'tools\stage24381_pack3_chapter3_closure_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$chapter381Exit = $LASTEXITCODE
$chapter381Lines | Set-Content -Encoding UTF8 $chapter381Contract
if ($chapter381Exit -ne 0) { throw "Stage 24.38.1 Pack3 chapter3 closure preflight failed exit=$chapter381Exit report=$chapter381Contract" }
Write-Host "[stage24.38.1] Pack3 3-6..3-21 + stock theme3Complete closure preflight PASS report=$chapter381Contract"

# Stage 24.38.2: the long Pack3 stress run exposed a Stage24.29.0 boot-handoff
# regression that overwrote the original levelFailed menu table with boolean
# false.  Preserve initializeMenu's table; untouched levelFailedTimer remains
# the failure-state owner.
$failure382Contract = Join-Path $outputDir 'stage24.38.2-level-failed-menu-boot-regression-contract.txt'
$failure382Lines = @(& $python (Join-Path $root 'tools\stage24382_level_failed_menu_boot_regression_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$failure382Exit = $LASTEXITCODE
$failure382Lines | Set-Content -Encoding UTF8 $failure382Contract
if ($failure382Exit -ne 0) { throw "Stage 24.38.2 levelFailed menu boot regression preflight failed exit=$failure382Exit report=$failure382Contract" }
Write-Host "[stage24.38.2] levelFailed menu-table startup ownership regression preflight PASS report=$failure382Contract"

# Stage 24.39.0: first Mighty Hoax frontier.  The direct-load context bridge now
# resolves both the basic Poached Eggs selection table and the untouched
# levelSelectionPagesExtra table, then transports the exact Theme4 families
# already proven by Stage24.15.0.  No Mighty Hoax gameplay/progression override.
$mighty390Contract = Join-Path $outputDir 'stage24.39.0-mighty-hoax-theme4-contract.txt'
$mighty390Lines = @(& $python (Join-Path $root 'tools\stage24390_mighty_hoax_theme4_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$mighty390Exit = $LASTEXITCODE
$mighty390Lines | Set-Content -Encoding UTF8 $mighty390Contract
if ($mighty390Exit -ne 0) { throw "Stage 24.39.0 Mighty Hoax/theme4 preflight failed exit=$mighty390Exit report=$mighty390Contract" }
Write-Host "[stage24.39.0] Mighty Hoax 4-1..4-5 + exact theme4/context preflight PASS report=$mighty390Contract"

# Stage 24.40.0: Mighty Hoax 4-1 exposed the first polygon object ever reached
# by the live progression.  Reconstruct the original native vertex accumulator
# + createPolygon body/fixture surface generically from the user's ARMv7 binary.
$polygon400Contract = Join-Path $outputDir 'stage24.40.0-polygon-native-contract.txt'
$polygon400Lines = @(& $python (Join-Path $root 'tools\stage24400_polygon_native_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$polygon400Exit = $LASTEXITCODE
$polygon400Lines | Set-Content -Encoding UTF8 $polygon400Contract
if ($polygon400Exit -ne 0) { throw "Stage 24.40.0 createPolygon native preflight failed exit=$polygon400Exit report=$polygon400Contract" }
Write-Host "[stage24.40.0-polygon] ARMv7 clearVertices/addVertex/createPolygon reconstruction preflight PASS report=$polygon400Contract"

# Stage 24.40.1: polygon reconstruction is now runtime-proven through Mighty Hoax
# 4-1..4-5. Continue the untouched Pack4 order through 4-10; transport only.
$mighty401Contract = Join-Path $outputDir 'stage24.40.1-mighty-hoax-4-10-contract.txt'
$mighty401Lines = @(& $python (Join-Path $root 'tools\stage24401_mighty_hoax_4_10_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$mighty401Exit = $LASTEXITCODE
$mighty401Lines | Set-Content -Encoding UTF8 $mighty401Contract
if ($mighty401Exit -ne 0) { throw "Stage 24.40.1 Mighty Hoax 4-6..4-10 preflight failed exit=$mighty401Exit report=$mighty401Contract" }
Write-Host "[stage24.40.1-mighty] Mighty Hoax 4-6..4-10 transport + untouched map preflight PASS report=$mighty401Contract"

# Stage 24.40.2: v0.26.127 runtime proves 4-6..4-10 clean. Transport the
# remaining untouched Pack4 page-1 sequence through 4-21 and observe stock
# page-completion/Next behavior. No progression override.
$mighty402Contract = Join-Path $outputDir 'stage24.40.2-mighty-hoax-4-21-closure-contract.txt'
$mighty402Lines = @(& $python (Join-Path $root 'tools\stage24402_mighty_hoax_4_21_closure_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$mighty402Exit = $LASTEXITCODE
$mighty402Lines | Set-Content -Encoding UTF8 $mighty402Contract
if ($mighty402Exit -ne 0) { throw "Stage 24.40.2 Mighty Hoax 4-11..4-21 closure preflight failed exit=$mighty402Exit report=$mighty402Contract" }
Write-Host "[stage24.40.2-mighty] Mighty Hoax 4-11..4-21 transport + closure observer preflight PASS report=$mighty402Contract"

# Stage 24.41.0: restore the generic native checkForLuaFile existence query used
# by untouched hasLevelPack2/3/4, then enter Mighty Hoax page/theme 5 through
# 5-10. The stock Lua remains owner of episode-card visibility and progression.
$mighty410Contract = Join-Path $outputDir 'stage24.41.0-checkforluafile-mighty-page2-contract.txt'
$mighty410Lines = @(& $python (Join-Path $root 'tools\stage24410_checkforluafile_mighty_page2_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$mighty410Exit = $LASTEXITCODE
$mighty410Lines | Set-Content -Encoding UTF8 $mighty410Contract
if ($mighty410Exit -ne 0) { throw "Stage 24.41.0 checkForLuaFile + Mighty Hoax 5-1..5-10 preflight failed exit=$mighty410Exit report=$mighty410Contract" }
Write-Host "[stage24.41.0-mighty] Generic checkForLuaFile + Mighty Hoax page2/theme5 transport preflight PASS report=$mighty410Contract"

# Stage 24.41.1: v0.26.129 runtime proves 5-1..5-10 and the generic
# checkForLuaFile contract. Close the same untouched Pack5 page through 5-21
# and observe stock theme5/page-completion behavior.
$mighty411Contract = Join-Path $outputDir 'stage24.41.1-mighty-hoax-5-21-closure-contract.txt'
$mighty411Lines = @(& $python (Join-Path $root 'tools\stage24411_mighty_hoax_5_21_closure_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$mighty411Exit = $LASTEXITCODE
$mighty411Lines | Set-Content -Encoding UTF8 $mighty411Contract
if ($mighty411Exit -ne 0) { throw "Stage 24.41.1 Mighty Hoax 5-11..5-21 closure preflight failed exit=$mighty411Exit report=$mighty411Contract" }
Write-Host "[stage24.41.1-mighty] Mighty Hoax 5-11..5-21 transport + page closure observer preflight PASS report=$mighty411Contract"

# Stage 24.42.0: v0.26.130 runtime closes Mighty Hoax. Enter Danger Above as
# one natural 15-level page/theme QA boundary. Theme6 introduces SKIES_2,
# PARALLAX_6 and GROUND_6; Boomerang remains untouched Lua-owned.
$danger420Contract = Join-Path $outputDir 'stage24.42.0-danger-above-theme6-boomerang-contract.txt'
$danger420Lines = @(& $python (Join-Path $root 'tools\stage24420_danger_above_theme6_boomerang_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$danger420Exit = $LASTEXITCODE
$danger420Lines | Set-Content -Encoding UTF8 $danger420Contract
if ($danger420Exit -ne 0) { throw "Stage 24.42.0 Danger Above theme6 + Boomerang preflight failed exit=$danger420Exit report=$danger420Contract" }
Write-Host "[stage24.42.0-danger] Danger Above 6-1..6-15 Theme6 + Boomerang observer preflight PASS report=$danger420Contract"

# Stage 24.42.1: the first Boomerang run proves the Lua specialty itself, then
# exposes the intentionally fail-closed nonlegacy bird-destruction velocity
# branch left from Stage 16. Reconstruct that exact ARMv7 deferred producer and
# add a read-only glass/wood physics-enable/contact audit.
$danger421Contract = Join-Path $outputDir 'stage24.42.1-nonlegacy-bird-velocity-physics-audit-contract.txt'
$danger421Lines = @(& $python (Join-Path $root 'tools\stage24421_nonlegacy_bird_velocity_physics_audit_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') $blockScoreOwnershipAudit 2>&1 | ForEach-Object { "$_" })
$danger421Exit = $LASTEXITCODE
$danger421Lines | Set-Content -Encoding UTF8 $danger421Contract
if ($danger421Exit -ne 0) { throw "Stage 24.42.1 nonlegacy bird velocity + physics audit preflight failed exit=$danger421Exit report=$danger421Contract" }
Write-Host "[stage24.42.1-nonlegacy] Deferred bird velocity + passive glass/wood physics audit preflight PASS report=$danger421Contract"


# Stage 24.43.0: discovery-only pass for the remaining original joint contract
# plus high-value physics/lifecycle stubs.  The build captures exact ARMv7
# createJoint/destroyJoint/setLevelLimits/setMaxTranslation/setGameOn bodies;
# runtime probes preserve historical no-mutation behavior and expose real 5-11 args.
if (!$armv7Lib) { throw 'Stage 24.43.0 requires the original ARMv7 libangrybirds.so for joint/bounds discovery.' }
$joint430Contract = Join-Path $outputDir 'stage24.43.0-joint-bounds-discovery-contract.txt'
$joint430Lines = @(& $python (Join-Path $root 'tools\stage24430_joint_bounds_discovery_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') 2>&1 | ForEach-Object { "$_" })
$joint430Exit = $LASTEXITCODE
$joint430Lines | Set-Content -Encoding UTF8 $joint430Contract
if ($joint430Exit -ne 0) { throw "Stage 24.43.0 joint/bounds discovery preflight failed exit=$joint430Exit report=$joint430Contract" }
Write-Host "[stage24.43.0-joint] ARMv7 joint + bounds/lifecycle discovery preflight PASS report=$joint430Contract"

# Stage 24.43.1: consume the captured ARMv7 contract. Live Danger Above 6-15
# issued nine type=1/coordType=2 joints from pigs to static balloon anchors and
# then self-destructed before a shot when those joints were absent. Reconstruct
# the generic type=1 b2DistanceJoint path; bounds/lifecycle probes stay passive.
$joint431Contract = Join-Path $outputDir 'stage24.43.1-distance-joint-contract.txt'
$joint431Lines = @(& $python (Join-Path $root 'tools\stage24431_distance_joint_contract.py') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') $joint430Contract 2>&1 | ForEach-Object { "$_" })
$joint431Exit = $LASTEXITCODE
$joint431Lines | Set-Content -Encoding UTF8 $joint431Contract
if ($joint431Exit -ne 0) { throw "Stage 24.43.1 distance-joint reconstruction preflight failed exit=$joint431Exit report=$joint431Contract" }
Write-Host "[stage24.43.1-joint] Original type=1 distance-joint reconstruction preflight PASS report=$joint431Contract"

# Stage 24.44.0 fork-level prerequisite: stock Box2D 2.1.2 exposes
# b2_maxTranslation as macros, while untouched ARMv7 setMaxTranslation writes
# two globals at runtime. Reconstruct only this proven Rovio mutability delta.
$maxTranslationPatchReport = Join-Path $outputDir 'stage24.44.0-box2d-maxtranslation-patch.txt'
$maxTranslationPatchLines = @(& $python (Join-Path $root 'tools\patch_box2d212_rovio_max_translation.py') $boxDir 2>&1 | ForEach-Object { "$_" })
$maxTranslationPatchExit = $LASTEXITCODE
$maxTranslationPatchLines | Set-Content -Encoding UTF8 $maxTranslationPatchReport
if ($maxTranslationPatchExit -ne 0) { throw "Stage 24.44.0 Rovio Box2D max-translation patch failed exit=$maxTranslationPatchExit report=$maxTranslationPatchReport" }
Write-Host "[stage24.44.0-maxtranslation] Rovio mutable max-translation Box2D patch PASS report=$maxTranslationPatchReport"

# Stage 24.44.0: with joints now live-validated, close one small exact Box2D
# setter immediately (setMaxTranslation) and perform a deeper ownership pass
# before enforcing setLevelLimits or setGameOn. The static report scans every
# GameLua ARMv7 body for +0x24c/+0x250 consumers and cross-checks the pinned
# Box2D 2.1.2 b2_maxTranslation globals. Runtime remains passive for bounds.
$bounds440Contract = Join-Path $outputDir 'stage24.44.0-bounds-lifecycle-ownership-contract.txt'
$bounds440Lines = @(& $python (Join-Path $root 'tools\stage24440_bounds_lifecycle_ownership_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') $joint430Contract 2>&1 | ForEach-Object { "$_" })
$bounds440Exit = $LASTEXITCODE
$bounds440Lines | Set-Content -Encoding UTF8 $bounds440Contract
if ($bounds440Exit -ne 0) { throw "Stage 24.44.0 bounds/lifecycle ownership preflight failed exit=$bounds440Exit report=$bounds440Contract" }
Write-Host "[stage24.44.0a-bounds] Max-translation reconstruction + level-limit/lifecycle ownership cross-proof PASS report=$bounds440Contract"

# Stage 24.44.1: the first live bounds witness produced the exact old failure
# shape: a Red bird crossed maxX and remained native/live for ~19 seconds while
# the level kept waiting. Capture the FULL original GameLua::update(float) and
# every named GameLua method that actually reads/writes +0x24c/+0x250 before
# changing motion/end-of-level semantics. Runtime adds shadow telemetry only.
$bounds441Contract = Join-Path $outputDir 'stage24.44.1-level-limit-update-consumer-contract.txt'
$bounds441Lines = @(& $python (Join-Path $root 'tools\stage24441_level_limit_update_consumer_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'pull-stage24-live-log.ps1') 2>&1 | ForEach-Object { "$_" })
$bounds441Exit = $LASTEXITCODE
$bounds441Lines | Set-Content -Encoding UTF8 $bounds441Contract
if ($bounds441Exit -ne 0) { throw "Stage 24.44.1 level-limit/update consumer capture preflight failed exit=$bounds441Exit report=$bounds441Contract" }
Write-Host "[stage24.44.1-bounds] Full ARMv7 update/level-limit consumer capture PASS report=$bounds441Contract"

# Stage 24.44.2: reconstruct the exact consumer now proven by the complete
# ARMv7 update body: crossing x limits (or synchronized y>20) sets the Lua
# object field `frozen=true`; untouched Lua updateGame owns removal.
$bounds442Contract = Join-Path $outputDir 'stage24.44.2-level-limit-frozen-contract.txt'
$stage220Report = Join-Path $outputDir 'stage24.22.0-level-failed-contract.txt'
$bounds442Lines = @(& $python (Join-Path $root 'tools\stage24442_level_limit_frozen_contract.py') $bounds441Contract (Join-Path $root 'stage24_live_surface.cpp') $stage220Report 2>&1 | ForEach-Object { "$_" })
$bounds442Exit = $LASTEXITCODE
$bounds442Lines | Set-Content -Encoding UTF8 $bounds442Contract
if ($bounds442Exit -ne 0) { throw "Stage 24.44.2 exact frozen level-limit contract preflight failed exit=$bounds442Exit report=$bounds442Contract" }
Write-Host "[stage24.44.2-bounds] Exact ARMv7 frozen level-limit consumer reconstruction preflight PASS report=$bounds442Contract"

# Stage 24.44.3: close the last lifecycle stub without inventing a modern
# Android side effect. Original setGameOn(bool) calls the App OSInterface
# virtual slot +0x18 with !gameOn. Resolve that exact slot through the original
# AndroidOSInterface vtable and require it to be allowSleep(bool); the shipping
# Android implementation must remain the exact one-instruction bx lr no-op.
$gameOn443Contract = Join-Path $outputDir 'stage24.44.3-setgameon-android-contract.txt'
$gameOn443Lines = @(& $python (Join-Path $root 'tools\stage24443_setgameon_android_contract.py') $llvmNm $llvmObjdump $armv7Lib.FullName $joint430Contract $nativeResolutionOwnershipAudit (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$gameOn443Exit = $LASTEXITCODE
$gameOn443Lines | Set-Content -Encoding UTF8 $gameOn443Contract
if ($gameOn443Exit -ne 0) { throw "Stage 24.44.3 setGameOn Android closure preflight failed exit=$gameOn443Exit report=$gameOn443Contract" }
Write-Host "[stage24.44.3-gameon] Exact Android setGameOn/allowSleep no-op contract PASS report=$gameOn443Contract"

# Stage 24.45.0: Stage24.44 lifecycle is closed. Resume the untouched Danger
# Above progression at its next natural 15-level page/theme boundary (pack7).
$danger450Contract = Join-Path $outputDir 'stage24.45.0-danger-above-theme7-contract.txt'
$danger450Lines = @(& $python (Join-Path $root 'tools\stage24450_danger_above_theme7_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$danger450Exit = $LASTEXITCODE
$danger450Lines | Set-Content -Encoding UTF8 $danger450Contract
if ($danger450Exit -ne 0) { throw "Stage 24.45.0 Danger Above theme7 preflight failed exit=$danger450Exit report=$danger450Contract" }
Write-Host "[stage24.45.0-danger] Danger Above 7-1..7-15 Theme7 transport/ownership preflight PASS report=$danger450Contract"


# Stage 24.45.1: close untouched Danger Above with its third/final 15-level
# page/theme boundary (pack8/theme8). Progression remains entirely Lua-owned.
$danger451Contract = Join-Path $outputDir 'stage24.45.1-danger-above-theme8-contract.txt'
$danger451Lines = @(& $python (Join-Path $root 'tools\stage24451_danger_above_theme8_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$danger451Exit = $LASTEXITCODE
$danger451Lines | Set-Content -Encoding UTF8 $danger451Contract
if ($danger451Exit -ne 0) { throw "Stage 24.45.1 Danger Above theme8 preflight failed exit=$danger451Exit report=$danger451Contract" }
Write-Host "[stage24.45.1-danger] Danger Above 8-1..8-15 Theme8 transport/ownership preflight PASS report=$danger451Contract"

# Stage 24.46.0: enter untouched The Big Setup through pack9/theme9.
# The exact theme9 layer table is intentionally discovered live by the generic
# setTheme observer; only original assets that already exist in the 1.4.2 payload
# are transported here, including the previously-unused crane parallax sheet.
$bigSetup460Contract = Join-Path $outputDir 'stage24.46.0-big-setup-theme9-contract.txt'
$bigSetup460Lines = @(& $python (Join-Path $root 'tools\stage24460_big_setup_theme9_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$bigSetup460Exit = $LASTEXITCODE
$bigSetup460Lines | Set-Content -Encoding UTF8 $bigSetup460Contract
if ($bigSetup460Exit -ne 0) { throw "Stage 24.46.0 Big Setup theme9 preflight failed exit=$bigSetup460Exit report=$bigSetup460Contract" }
Write-Host "[stage24.46.0-bigsetup] The Big Setup 9-1..9-15 pack9 transport + Theme9 discovery preflight PASS report=$bigSetup460Contract"

# Stage 24.46.1: Theme9 is the first original theme to exercise the recovered
# bgLayers repeat=false path. Reconstruct that branch directly from the
# Stage24.15.1 ARMv7 GameLua::drawBackground() disassembly rather than from
# appearance. The same exact geometry is used by gameplay and menu theme draws.
$nonrepeat461Contract = Join-Path $outputDir 'stage24.46.1-nonrepeat-background-contract.txt'
$nonrepeat461Lines = @(& $python (Join-Path $root 'tools\stage24461_nonrepeat_background_contract.py') $themeNativeAudit (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$nonrepeat461Exit = $LASTEXITCODE
$nonrepeat461Lines | Set-Content -Encoding UTF8 $nonrepeat461Contract
if ($nonrepeat461Exit -ne 0) { throw "Stage 24.46.1 non-repeating background reconstruction preflight failed exit=$nonrepeat461Exit report=$nonrepeat461Contract" }
Write-Host "[stage24.46.1-scene] Exact ARMv7 non-repeating background branch reconstruction PASS report=$nonrepeat461Contract"

# Stage 24.46.2: continue The Big Setup through untouched page2 / pack10.
# Scene composition remains entirely data-driven. Stage24.46.1 already proved
# the original repeat=false crane path across themes 9, 10 and 11.
$bigSetup462Contract = Join-Path $outputDir 'stage24.46.2-big-setup-pack10-contract.txt'
$bigSetup462Lines = @(& $python (Join-Path $root 'tools\stage24462_big_setup_pack10_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$bigSetup462Exit = $LASTEXITCODE
$bigSetup462Lines | Set-Content -Encoding UTF8 $bigSetup462Contract
if ($bigSetup462Exit -ne 0) { throw "Stage 24.46.2 Big Setup pack10 preflight failed exit=$bigSetup462Exit report=$bigSetup462Contract" }
Write-Host "[stage24.46.2-bigsetup] The Big Setup 10-1..10-15 pack10 transport/ownership preflight PASS report=$bigSetup462Contract"

# Stage 24.46.3: final untouched The Big Setup page / pack11.
# No theme/renderer behavior is invented here; the existing generic scene
# path remains authoritative and runtime will expose any truly new native debt.
$bigSetup463Contract = Join-Path $outputDir 'stage24.46.3-big-setup-pack11-contract.txt'
$bigSetup463Lines = @(& $python (Join-Path $root 'tools\stage24463_big_setup_pack11_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$bigSetup463Exit = $LASTEXITCODE
$bigSetup463Lines | Set-Content -Encoding UTF8 $bigSetup463Contract
if ($bigSetup463Exit -ne 0) { throw "Stage 24.46.3 Big Setup pack11 preflight failed exit=$bigSetup463Exit report=$bigSetup463Contract" }
Write-Host "[stage24.46.3-bigsetup] The Big Setup 11-1..11-15 pack11 transport/ownership preflight PASS report=$bigSetup463Contract"

# Stage 24.47.0: enter the Golden Eggs branch after the full campaign closure.
# Transport all 15 gameplay LevelGE files proven by untouched levelOrder_goldenEggs.
# The 4 soundboards and every unlock/selectability/completion write remain Lua-owned.
$golden470Contract = Join-Path $outputDir 'stage24.47.0-golden-eggs-contract.txt'
$golden470Lines = @(& $python (Join-Path $root 'tools\stage24470_golden_eggs_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$golden470Exit = $LASTEXITCODE
$golden470Lines | Set-Content -Encoding UTF8 $golden470Contract
if ($golden470Exit -ne 0) { throw "Stage 24.47.0 Golden Eggs preflight failed exit=$golden470Exit report=$golden470Contract" }
Write-Host "[stage24.47.0-golden] Golden Eggs 15-level transport/menu ownership preflight PASS report=$golden470Contract"

# Stage 24.47.0A: untouched Golden Eggs paths are relative to the original
# data root (levels/goldeneggs1/...), unlike campaign paths that already carry
# data/levels/.... Reconstruct that generic native resource-search root.
$golden470aContract = Join-Path $outputDir 'stage24.47.0a-golden-eggs-resource-root-contract.txt'
$golden470aLines = @(& $python (Join-Path $root 'tools\stage24470a_golden_eggs_resource_root_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') 2>&1 | ForEach-Object { "$_" })
$golden470aExit = $LASTEXITCODE
$golden470aLines | Set-Content -Encoding UTF8 $golden470aContract
if ($golden470aExit -ne 0) { throw "Stage 24.47.0A Golden Eggs resource-root preflight failed exit=$golden470aExit report=$golden470aContract" }
Write-Host "[stage24.47.0a-golden] Golden Eggs data-root resource-search reconstruction preflight PASS report=$golden470aContract"

# Stage 24.47.1: the same long-standing rubber/beachball physics mismatch is
# reproducible in Golden Egg 2 and Danger Above 8-3. Do not tune restitution
# or inject impulses from observation. Capture pre-solver state, the solver
# impulse and post-Step velocities while retaining every prior ARMv7 Box2D gate.
$rubber471Contract = Join-Path $outputDir 'stage24.47.1-rubber-physics-audit-contract.txt'
$rubber471Lines = @(& $python (Join-Path $root 'tools\stage24471_rubber_physics_audit_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'test-stage24-rubber-physics-audit.ps1') 2>&1 | ForEach-Object { "$_" })
$rubber471Exit = $LASTEXITCODE
$rubber471Lines | Set-Content -Encoding UTF8 $rubber471Contract
if ($rubber471Exit -ne 0) { throw "Stage 24.47.1 rubber physics audit preflight failed exit=$rubber471Exit report=$rubber471Contract" }
Write-Host "[stage24.47.1-rubber] Rubber/beachball pre-solver/solver/post-step audit preflight PASS report=$rubber471Contract"

# Stage 24.47.2: the visible "molenga" rubber structure is a network of
# type=1 b2DistanceJoint springs. Acquire the untouched ARMv7 constructor and
# solver bodies beside the pinned Box2D 2.1.2 source, then gate a runtime
# observer that measures strain/reaction force without changing physics.
$spring472Native = Join-Path $outputDir 'stage24.47.2-distance-joint-solver-native-audit.txt'
$spring472NativeLines = @(& $python (Join-Path $root 'tools\stage24472_distance_joint_solver_native_audit.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
$spring472NativeExit = $LASTEXITCODE
$spring472NativeLines | Set-Content -Encoding UTF8 $spring472Native
if ($spring472NativeExit -ne 0) { throw "Stage 24.47.2 distance-joint native solver audit failed exit=$spring472NativeExit report=$spring472Native" }
Write-Host "[stage24.47.2-spring] ARMv7 distance-joint solver acquisition PASS report=$spring472Native"

$spring472Contract = Join-Path $outputDir 'stage24.47.2-distance-joint-spring-audit-contract.txt'
$spring472Lines = @(& $python (Join-Path $root 'tools\stage24472_distance_joint_spring_audit_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'test-stage24-distance-joint-spring-audit.ps1') (Join-Path $root 'tools\stage24472_distance_joint_solver_native_audit.py') 2>&1 | ForEach-Object { "$_" })
$spring472Exit = $LASTEXITCODE
$spring472Lines | Set-Content -Encoding UTF8 $spring472Contract
if ($spring472Exit -ne 0) { throw "Stage 24.47.2 distance-joint spring audit preflight failed exit=$spring472Exit report=$spring472Contract" }
Write-Host "[stage24.47.2-spring] Distance-joint spring runtime audit preflight PASS report=$spring472Contract"

# Stage 24.47.3: Stage47.2 closed the obvious distance-joint/timestep
# hypotheses. Cross-proof the original high-restitution contact solver before
# touching the intentional rubber restitution=5.5. LevelGE_2 provides free
# ExtraRubberBall contacts without the 4 Hz spring network.
$contact473Native = Join-Path $outputDir 'stage24.47.3-high-restitution-contact-solver-native-audit.txt'
$contact473NativeLines = @(& $python (Join-Path $root 'tools\stage24473_high_restitution_contact_solver_native_audit.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
$contact473NativeExit = $LASTEXITCODE
$contact473NativeLines | Set-Content -Encoding UTF8 $contact473Native
if ($contact473NativeExit -ne 0) { throw "Stage 24.47.3 high-restitution contact solver native audit failed exit=$contact473NativeExit report=$contact473Native" }
Write-Host "[stage24.47.3-contact] ARMv7 high-restitution contact solver acquisition PASS report=$contact473Native"

$contact473Contract = Join-Path $outputDir 'stage24.47.3-high-restitution-contact-solver-audit-contract.txt'
$contact473Lines = @(& $python (Join-Path $root 'tools\stage24473_high_restitution_contact_solver_audit_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'test-stage24-high-restitution-contact-solver-audit.ps1') (Join-Path $root 'tools\stage24473_high_restitution_contact_solver_native_audit.py') 2>&1 | ForEach-Object { "$_" })
$contact473Exit = $LASTEXITCODE
$contact473Lines | Set-Content -Encoding UTF8 $contact473Contract
if ($contact473Exit -ne 0) { throw "Stage 24.47.3 high-restitution contact solver audit preflight failed exit=$contact473Exit report=$contact473Contract" }
Write-Host "[stage24.47.3-contact] High-restitution contact solver runtime cross-proof preflight PASS report=$contact473Contract"

# Stage 24.47.4: Stage47.3 cross-proofed the core normal contact solve, while
# the latest network run showed many rubber bodies finishing exactly on the
# b2_maxTranslation cap. Audit the remaining manifold warm-start carryover,
# b2Island integration/clamp order and PostSolve timing before touching physics.
$warm474Native = Join-Path $outputDir 'stage24.47.4-rubber-warmstart-integration-native-audit.txt'
$warm474NativeLines = @(& $python (Join-Path $root 'tools\stage24474_rubber_warmstart_integration_native_audit.py') $llvmNm $llvmObjdump $armv7Lib.FullName $boxDir 2>&1 | ForEach-Object { "$_" })
$warm474NativeExit = $LASTEXITCODE
$warm474NativeLines | Set-Content -Encoding UTF8 $warm474Native
if ($warm474NativeExit -ne 0) { throw "Stage 24.47.4 rubber warm-start/integration native audit failed exit=$warm474NativeExit report=$warm474Native" }
Write-Host "[stage24.47.4-warm] ARMv7 contact-update/island integration acquisition PASS report=$warm474Native"

$warm474Contract = Join-Path $outputDir 'stage24.47.4-rubber-warmstart-integration-contract.txt'
$warm474Lines = @(& $python (Join-Path $root 'tools\stage24474_rubber_warmstart_integration_contract.py') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'test-stage24-rubber-warmstart-integration-audit.ps1') (Join-Path $root 'tools\stage24474_rubber_warmstart_integration_native_audit.py') 2>&1 | ForEach-Object { "$_" })
$warm474Exit = $LASTEXITCODE
$warm474Lines | Set-Content -Encoding UTF8 $warm474Contract
if ($warm474Exit -ne 0) { throw "Stage 24.47.4 rubber warm-start/integration preflight failed exit=$warm474Exit report=$warm474Contract" }
Write-Host "[stage24.47.4-warm] Rubber manifold warm-start/integration runtime preflight PASS report=$warm474Contract"

# Stage 24.47.5: ARMv7 scalar float operations in the recovered Box2D paths
# cross helper-call rounding boundaries.  Make that numerical contract explicit
# on AArch64 by disabling FP contraction for box2d212 and the live bridge.
$fp475Contract = Join-Path $outputDir 'stage24.47.5-fp-contraction-contract.txt'
$fp475Lines = @(& $python (Join-Path $root 'tools\stage24475_fp_contraction_contract.py') (Join-Path $root 'CMakeLists.txt') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'test-stage24-fp-contraction-order-audit.ps1') (Join-Path $root 'tools\stage24475_fp_contraction_binary_audit.py') 2>&1 | ForEach-Object { "$_" })
$fp475Exit = $LASTEXITCODE
$fp475Lines | Set-Content -Encoding UTF8 $fp475Contract
if ($fp475Exit -ne 0) { throw "Stage 24.47.5 FP-contraction preflight failed exit=$fp475Exit report=$fp475Contract" }
Write-Host "[stage24.47.5-fp] FP-contraction/order preflight PASS report=$fp475Contract"

# Stage 24.47.6: Android NativeActivity may destroy/recreate only its Surface
# while the process remains alive (for example when opening Recents). Acquire
# the original ARMv7 JNI lifecycle entrypoints and fail closed unless our
# wrapper preserves engine state across TERM_WINDOW and rebinds only EGLSurface.
$lifecycle476Native = Join-Path $outputDir 'stage24.47.6-native-jni-lifecycle-audit.txt'
$lifecycle476NativeLines = @(& $python (Join-Path $root 'tools\stage24476_native_jni_lifecycle_audit.py') $llvmNm $llvmObjdump $armv7Lib.FullName 2>&1 | ForEach-Object { "$_" })
$lifecycle476NativeExit = $LASTEXITCODE
$lifecycle476NativeLines | Set-Content -Encoding UTF8 $lifecycle476Native
if ($lifecycle476NativeExit -ne 0) { throw "Stage 24.47.6 native JNI lifecycle audit failed exit=$lifecycle476NativeExit report=$lifecycle476Native" }
Write-Host "[stage24.47.6-lifecycle] Original JNI lifecycle acquisition PASS report=$lifecycle476Native"

$lifecycle476Contract = Join-Path $outputDir 'stage24.47.6-android-lifecycle-contract.txt'
$lifecycle476Lines = @(& $python (Join-Path $root 'tools\stage24476_android_lifecycle_contract.py') (Join-Path $root 'stage24_live_surface.cpp') (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1') (Join-Path $root 'pull-stage24-live-log.ps1') (Join-Path $root 'test-stage24-android-lifecycle-resume.ps1') (Join-Path $root 'tools\stage24476_native_jni_lifecycle_audit.py') 2>&1 | ForEach-Object { "$_" })
$lifecycle476Exit = $LASTEXITCODE
$lifecycle476Lines | Set-Content -Encoding UTF8 $lifecycle476Contract
if ($lifecycle476Exit -ne 0) { throw "Stage 24.47.6 Android lifecycle contract failed exit=$lifecycle476Exit report=$lifecycle476Contract" }
Write-Host "[stage24.47.6-lifecycle] Surface-resume lifecycle preflight PASS report=$lifecycle476Contract"

# Stage 24.48.0: freeze the proven v0.26.157 runtime as the first release-
# candidate baseline and inventory only release-envelope debt. This audit does
# not mutate gameplay, physics, lifecycle, save state or original assets.
$rc480Contract = Join-Path $outputDir 'stage24.48.0-release-candidate-contract.txt'
$rc480Lines = @(& $python (Join-Path $root 'tools\stage24480_release_candidate_contract.py') $root 2>&1 | ForEach-Object { "$_" })
$rc480Exit = $LASTEXITCODE
$rc480Lines | Set-Content -Encoding UTF8 $rc480Contract
if ($rc480Exit -ne 0) { throw "Stage 24.48.0 release-candidate baseline audit failed exit=$rc480Exit report=$rc480Contract" }
Write-Host "[stage24.48.0-rc] Engine baseline PASS; release-envelope debt inventoried report=$rc480Contract"

# Stage24.48.1: release branding is packaging-only. The launcher label is the
# original public-facing name and the icon bytes are discovered from the user's
# own original APK/extracted res tree at build time; no Rovio icon is distributed
# in this source archive.
$branding481Contract = Join-Path $outputDir 'stage24.48.1-release-branding-contract.txt'
$branding481Lines = @(& $python (Join-Path $root 'tools\stage24481_release_branding_contract.py') $root 2>&1 | ForEach-Object { "$_" })
$branding481Exit = $LASTEXITCODE
$branding481Lines | Set-Content -Encoding UTF8 $branding481Contract
if ($branding481Exit -ne 0) { throw "Stage 24.48.1 release-branding contract failed exit=$branding481Exit report=$branding481Contract" }
Write-Host "[stage24.48.1-branding] Static release-branding contract PASS report=$branding481Contract"

# Extract untouched original RGBA4444 PVRs locally. They are packaged into the
# APK only on the user's machine; this bootstrap ZIP does not redistribute them.
$pvrTmp = Join-Path $apkWork 'pvr'
if (Test-Path $apkWork) { Remove-Item $apkWork -Recurse -Force }
New-Item -ItemType Directory -Force -Path $pvrTmp | Out-Null
$blocksPvr = Expand-SinglePvr $blocksZip (Join-Path $pvrTmp 'blocks')
$birdsPvr = Expand-SinglePvr $birdsZip (Join-Path $pvrTmp 'birds')
if (Test-Path $themeGroundDirect) {
    $themeGroundPvr = $themeGroundDirect
} else {
    $themeGroundPvr = Expand-SinglePvr $themeGroundZip (Join-Path $pvrTmp 'theme_ground_1')
}
Write-Host "[stage24.14.4-mask] Terrain fill transport prepared: $themeGroundPvr bytes=$((Get-Item $themeGroundPvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGroundPvr
if (Test-Path $themeGround2Direct) {
    $themeGround2Pvr = $themeGround2Direct
} else {
    $themeGround2Pvr = Expand-SinglePvr $themeGround2Zip (Join-Path $pvrTmp 'theme_ground_2')
}
Write-Host "[stage24.35.2-mask] Theme2 terrain fill transport prepared: $themeGround2Pvr bytes=$((Get-Item $themeGround2Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround2Pvr
if ($LASTEXITCODE -ne 0) { throw 'PVR v2 header audit helper failed.' }
if (Test-Path $themeGround3Direct) {
    $themeGround3Pvr = $themeGround3Direct
} else {
    $themeGround3Pvr = Expand-SinglePvr $themeGround3Zip (Join-Path $pvrTmp 'theme_ground_3')
}
Write-Host "[stage24.38.0-mask] Theme3 terrain fill transport prepared: $themeGround3Pvr bytes=$((Get-Item $themeGround3Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround3Pvr

if (Test-Path $themeGround4Direct) {
    $themeGround4Pvr = $themeGround4Direct
} else {
    $themeGround4Pvr = Expand-SinglePvr $themeGround4Zip (Join-Path $pvrTmp 'theme_ground_4')
}
Write-Host "[stage24.39.0-mask] Theme4 terrain fill transport prepared: $themeGround4Pvr bytes=$((Get-Item $themeGround4Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround4Pvr
if (Test-Path $themeGround5Direct) {
    $themeGround5Pvr = $themeGround5Direct
} else {
    $themeGround5Pvr = Expand-SinglePvr $themeGround5Zip (Join-Path $pvrTmp 'theme_ground_5')
}
Write-Host "[stage24.41.0-mask] Theme5 terrain fill transport prepared: $themeGround5Pvr bytes=$((Get-Item $themeGround5Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround5Pvr

if (Test-Path $themeGround6Direct) {
    $themeGround6Pvr = $themeGround6Direct
} else {
    $themeGround6Pvr = Expand-SinglePvr $themeGround6Zip (Join-Path $pvrTmp 'theme_ground_6')
}
Write-Host "[stage24.42.0-mask] Theme6 terrain fill transport prepared: $themeGround6Pvr bytes=$((Get-Item $themeGround6Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround6Pvr
if ($LASTEXITCODE -ne 0) { throw 'Theme6 PVR v2 header audit helper failed.' }
if (Test-Path $themeGround7Direct) {
    $themeGround7Pvr = $themeGround7Direct
} else {
    $themeGround7Pvr = Expand-SinglePvr $themeGround7Zip (Join-Path $pvrTmp 'theme_ground_7')
}
Write-Host "[stage24.45.0-mask] Theme7 terrain fill transport prepared: $themeGround7Pvr bytes=$((Get-Item $themeGround7Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround7Pvr
if ($LASTEXITCODE -ne 0) { throw 'Theme7 PVR v2 header audit helper failed.' }

if (Test-Path $themeGround8Direct) {
    $themeGround8Pvr = $themeGround8Direct
} else {
    $themeGround8Pvr = Expand-SinglePvr $themeGround8Zip (Join-Path $pvrTmp 'theme_ground_8')
}
Write-Host "[stage24.45.1-mask] Theme8 terrain fill transport prepared: $themeGround8Pvr bytes=$((Get-Item $themeGround8Pvr).Length)"
& $python (Join-Path $root 'tools\pvr_v2_rgba4444_audit.py') $themeGround8Pvr
if ($LASTEXITCODE -ne 0) { throw 'Theme8 PVR v2 header audit helper failed.' }

# Materialize exact menu texture pixels into a runtime-friendly transport.
# PVR RGBA4444 stays byte-identical. PNG is losslessly decoded at build time
# to ABR8 (width/height + RGBA8) using only Python's standard library; this
# changes no pixels and avoids adding an unrelated image decoder to the ARM64
# runtime while the resource renderer is being reconstructed.
$menuTextureInputs = @()
foreach ($textureName in $menuTextureNames) {
    $src = Join-Path $imageRoot $textureName
    if ($textureName.EndsWith('.pvr', [StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path $src) {
            $materialized = $src
        } else {
            $zip = "$src.zip"
            if (!(Test-Path $zip)) { throw "Original menu PVR not found: $src or $zip" }
            $safe = [IO.Path]::GetFileNameWithoutExtension($textureName)
            $materialized = Expand-SinglePvr $zip (Join-Path $pvrTmp ("menu_" + $safe))
        }
        # Stage 24.13.2b: never expose the original .pvr extension to aapt/
        # AssetManager.  The previous build proved the entry existed in the APK
        # yet AAssetManager_open() could not resolve it at runtime.  Treat PVR as
        # opaque transport bytes and give the packaged asset a neutral .bin
        # suffix; the manifest still records kind=pvr4444 and the runtime writes
        #/parses the exact bytes without conversion.
        $assetName = "$textureName.bin"
        $menuTextureInputs += [pscustomobject]@{ Logical=$textureName; Kind='pvr4444'; Path=$materialized; Asset=$assetName }
    } elseif ($textureName.EndsWith('.png', [StringComparison]::OrdinalIgnoreCase)) {
        if (!(Test-Path $src)) { throw "Original menu PNG not found: $src" }
        $assetName = "$textureName.rgba8.bin"
        $materialized = Join-Path $pvrTmp $assetName
        & $python (Join-Path $root 'tools\png_to_rgba8.py') $src $materialized
        if ($LASTEXITCODE -ne 0 -or !(Test-Path $materialized)) { throw "PNG -> RGBA8 conversion failed: $src" }
        $menuTextureInputs += [pscustomobject]@{ Logical=$textureName; Kind='rgba8'; Path=$materialized; Asset=$assetName }
    } else {
        throw "Unsupported menu texture extension from DAT: $textureName"
    }
}
Write-Host "[stage24.13.2b] Neutral .bin menu texture transport PASS count=$($menuTextureInputs.Count)"

# Stage 24.30.1: materialize dynamic cutscene texture transports. PVR bytes
# remain exact; they are decoded/uploaded only when createSpriteSheet acquires
# the owning DAT at runtime.
$cutsceneTextureInputs = @()
foreach ($textureName in $cutsceneTextureNames) {
    $src = Join-Path $imageRoot $textureName
    if ($textureName.EndsWith('.pvr', [StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path $src) {
            $materialized = $src
        } else {
            $zip = "$src.zip"
            if (!(Test-Path $zip)) { throw "Original cutscene PVR not found: $src or $zip" }
            $safe = [IO.Path]::GetFileNameWithoutExtension($textureName)
            $materialized = Expand-SinglePvr $zip (Join-Path $pvrTmp ("cutscene_" + $safe))
        }
        $assetName = "$textureName.bin"
        $cutsceneTextureInputs += [pscustomobject]@{ Logical=$textureName; Kind='pvrv2'; Path=$materialized; Asset=$assetName }
    } elseif ($textureName.EndsWith('.png', [StringComparison]::OrdinalIgnoreCase)) {
        if (!(Test-Path $src)) { throw "Original cutscene PNG not found: $src" }
        $assetName = "$textureName.rgba8.bin"
        $materialized = Join-Path $pvrTmp $assetName
        & $python (Join-Path $root 'tools\png_to_rgba8.py') $src $materialized
        if ($LASTEXITCODE -ne 0 -or !(Test-Path $materialized)) { throw "Cutscene PNG -> RGBA8 conversion failed: $src" }
        $cutsceneTextureInputs += [pscustomobject]@{ Logical=$textureName; Kind='rgba8'; Path=$materialized; Asset=$assetName }
    } else {
        throw "Unsupported dynamic cutscene texture extension: $textureName"
    }
}
Write-Host "[stage24.30.1-cutscene] Dynamic neutral texture transport PASS count=$($cutsceneTextureInputs.Count)"

# Stage 24.13.4: the original FONT DAT contains the exact bitmap image name.
# Recover it from the untouched FONT DATs instead of guessing a texture
# filename. Stage24.21.0 adds FONT_SCORE for floatingScores; Stage24.23.3 adds
# FONT_MENU because the untouched pause drawMenu path switches to it before
# drawing pause-page labels. Stage24.28.2 adds FONT_LS_SMALL because the first
# real Level Selection draw reached that exact original bitmap font and proved
# its texture was the next transport hole.
$fontRenderDatNames = @('FONT_BASIC.dat','FONT_BIG_NUMBERS.dat','FONT_SCORE.dat','FONT_MENU.dat','FONT_LS_SMALL.dat')
$fontTextureInputs = @()
$fontTextureSeen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($fontDatName in $fontRenderDatNames) {
    $fontDat = Join-Path $fontProfileRoot $fontDatName
    $fontImageName = (& $python (Join-Path $root 'tools\font_dat_image_name.py') $fontDat | Select-Object -Last 1).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($fontImageName)) {
        throw "Could not recover bitmap image name from $fontDat"
    }
    if (!$fontTextureSeen.Add($fontImageName)) { continue }

    $rel = $fontImageName.Replace('/','\')
    $basename = [IO.Path]::GetFileName($rel)
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($rel.StartsWith('data\',[StringComparison]::OrdinalIgnoreCase)) {
        $candidates.Add((Join-Path $dataRoot $rel.Substring(5)))
    } elseif ($rel.StartsWith('fonts\',[StringComparison]::OrdinalIgnoreCase)) {
        $candidates.Add((Join-Path $dataRoot $rel))
    }
    $candidates.Add((Join-Path $fontProfileRoot $basename))
    $src = $null
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { $src = $candidate; break }
    }
    if (!$src) {
        $found = @(Get-ChildItem -Path $dataRoot -Recurse -File -Filter $basename -ErrorAction SilentlyContinue)
        if ($found.Count -eq 1) { $src = $found[0].FullName }
        elseif ($found.Count -gt 1) {
            $profileMatch = @($found | Where-Object { $_.FullName -like '*fonts*864x480*' })
            if ($profileMatch.Count -eq 1) { $src = $profileMatch[0].FullName }
        }
    }

    $ext = [IO.Path]::GetExtension($basename).ToLowerInvariant()
    $safeFont = [IO.Path]::GetFileNameWithoutExtension($fontDatName)
    if ($ext -eq '.pvr') {
        if (!$src) {
            $zipCandidates = @()
            foreach ($candidate in $candidates) { $zipCandidates += "$candidate.zip" }
            foreach ($candidate in $zipCandidates) {
                if (Test-Path $candidate) {
                    $src = Expand-SinglePvr $candidate (Join-Path $pvrTmp ("font_" + $safeFont))
                    break
                }
            }
        }
        if (!$src) { throw "Original bitmap-font PVR not found for $fontDatName image='$fontImageName'" }
        $assetName = "$safeFont-$basename.bin"
        $fontTextureInputs += [pscustomobject]@{ Logical=$fontImageName; Kind='pvr4444'; Path=$src; Asset=$assetName; Font=$safeFont }
    } elseif ($ext -eq '.png') {
        if (!$src) { throw "Original bitmap-font PNG not found for $fontDatName image='$fontImageName'" }
        $assetName = "$safeFont-$basename.rgba8.bin"
        $materialized = Join-Path $pvrTmp $assetName
        & $python (Join-Path $root 'tools\png_to_rgba8.py') $src $materialized
        if ($LASTEXITCODE -ne 0 -or !(Test-Path $materialized)) { throw "Font PNG -> RGBA8 conversion failed: $src" }
        $fontTextureInputs += [pscustomobject]@{ Logical=$fontImageName; Kind='rgba8'; Path=$materialized; Asset=$assetName; Font=$safeFont }
    } else {
        throw "Unsupported bitmap-font image extension '$ext' from $fontDatName image='$fontImageName'"
    }
    Write-Host "[stage24.13.4-font] $safeFont -> '$fontImageName' kind=$($fontTextureInputs[-1].Kind)"
}
Write-Host "[stage24.23.3-font] Exact visible bitmap-font texture contract PASS count=$($fontTextureInputs.Count)"

# Stage24.49.0A: ZIP timestamps are timezone-naive. A source archive created
# under UTC and extracted on a UTC-03 Windows host can make CMakeLists.txt
# appear hours newer than the local clock. Ninja then sees its manifest input
# permanently newer than build.ninja and loops forever on "Re-running CMake".
# Normalize only filesystem metadata; the file contents/SHA-256 stay frozen.
$cmakeRootInput = Join-Path $root 'CMakeLists.txt'
$cmakeStampBefore = (Get-Item -LiteralPath $cmakeRootInput).LastWriteTime
$cmakeStampSafe = (Get-Date).AddSeconds(-10)
(Get-Item -LiteralPath $cmakeRootInput).LastWriteTime = $cmakeStampSafe
Write-Host ("[stage24.49.0a-release] CMake timestamp guard PASS before={0:o} after={1:o} contentSha256={2}" -f `
    $cmakeStampBefore, `
    (Get-Item -LiteralPath $cmakeRootInput).LastWriteTime, `
    ((Get-FileHash -LiteralPath $cmakeRootInput -Algorithm SHA256).Hash.ToLowerInvariant()))

if (Test-Path $build) { Remove-Item $build -Recurse -Force }
Write-Host "[stage24.20.1] Display mode=$DisplayMode (default wvga854 test harness; native preserves recovered Context contract)."
Write-Host '[stage24] Building libangryarm64.so (NativeActivity / ANativeWindow / GLES1 / real touch)...'
& $cmake `
    -S $root `
    -B $build `
    -G Ninja `
    "-DCMAKE_MAKE_PROGRAM=$ninja" `
    "-DCMAKE_TOOLCHAIN_FILE=$toolchain" `
    "-DANDROID_ABI=arm64-v8a" `
    "-DANDROID_PLATFORM=android-23" `
    "-DANDROID_STL=c++_static" `
    "-DCMAKE_BUILD_TYPE=Release" `
    "-DSTAGE24_DISPLAY_MODE=$DisplayMode" `
    "-DSTAGE24282_GLOBAL_SPRITE_REGISTRY=$stage24282GlobalLookupCmake" `
    "-DBOX2D212_ROOT=$boxDir"
if ($LASTEXITCODE -ne 0) { throw "CMake configure failed: $LASTEXITCODE" }
& $cmake --build $build --target stage24_live_surface
if ($LASTEXITCODE -ne 0) { throw "CMake build failed: $LASTEXITCODE" }

$so = Join-Path $build 'libangryarm64.so'
if (!(Test-Path $so)) { throw "Stage24 native library missing: $so" }
$readelf = Join-Path $ndk.FullName 'toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-readelf.exe'
if (Test-Path $readelf) {
    $hdr = @(& $readelf -h $so 2>&1)
    if (($hdr -join "`n") -notmatch 'AArch64') { throw 'Stage24 output is not AArch64.' }
    Write-Host '[stage24] Native library architecture=AArch64 PASS.'
}

# Stage24.47.5 post-build proof: fail closed if Clang emitted fused
# multiply-add/subtract in the relevant AArch64 physics functions despite the
# explicit non-contraction policy.
$fp475Binary = Join-Path $outputDir 'stage24.47.5-fp-contraction-binary-audit.txt'
$fp475BinaryLines = @(& $python (Join-Path $root 'tools\stage24475_fp_contraction_binary_audit.py') $llvmObjdump $armv7Lib.FullName $so $boxDir (Join-Path $root 'CMakeLists.txt') 2>&1 | ForEach-Object { "$_" })
$fp475BinaryExit = $LASTEXITCODE
$fp475BinaryLines | Set-Content -Encoding UTF8 $fp475Binary
if ($fp475BinaryExit -ne 0) { throw "Stage 24.47.5 FP-contraction binary audit failed exit=$fp475BinaryExit report=$fp475Binary" }
Write-Host "[stage24.47.5-fp] ARMv7/AArch64 FP contraction binary cross-proof PASS report=$fp475Binary"

# Build APK asset tree from the user's own extracted 1.4.2 files.
# Stage24.48.1 also creates the Android resource tree. The icon itself is NEVER
# stored in this source package: it is copied from the user's original extraction
# (or original Angry/Rovio APK in Downloads) during the local build.
$resRoot = Join-Path $apkWork 'res'
$resDrawable = Join-Path $resRoot 'drawable'
New-Item -ItemType Directory -Force -Path $resDrawable | Out-Null
$launcherIcon481 = Join-Path $resDrawable 'app_icon.png'
if (Test-Path $launcherIcon481) { Remove-Item $launcherIcon481 -Force }
$launcherIcon481Report = Join-Path $outputDir 'stage24.48.1-original-launcher-icon.txt'
$downloadsRoot = Join-Path $env:USERPROFILE 'Downloads'
$icon481Lines = @(& $python (Join-Path $root 'tools\stage24481_find_original_launcher_icon.py') $angryReRoot $downloadsRoot $launcherIcon481 2>&1 | ForEach-Object { "$_" })
$icon481Exit = $LASTEXITCODE
$icon481Lines | Set-Content -Encoding UTF8 $launcherIcon481Report
if ($icon481Exit -ne 0 -or !(Test-Path $launcherIcon481)) { throw "Stage 24.48.1 original launcher icon discovery failed exit=$icon481Exit report=$launcherIcon481Report" }
Write-Host "[stage24.48.1-branding] Original launcher icon staged locally report=$launcherIcon481Report"

$assetsRoot = Join-Path $apkWork 'assets'
$assetsStage = Join-Path $assetsRoot 'stage24'
$assetsScripts = Join-Path $assetsStage 'scripts'
$assetsSpriteMeta = Join-Path $assetsStage 'sprite-meta'
$assetsLocalization = Join-Path $assetsStage 'localization'
$assetsFonts = Join-Path $assetsStage 'fonts\864x480'
$assetsFontTextures = Join-Path $assetsStage 'font-textures'
$assetsLevelPack1 = Join-Path $assetsStage 'data\levels\pack1'
$assetsLevelPack2 = Join-Path $assetsStage 'data\levels\pack2'
$assetsLevelPack3 = Join-Path $assetsStage 'data\levels\pack3'
$assetsLevelPack4 = Join-Path $assetsStage 'data\levels\pack4'
$assetsLevelPack5 = Join-Path $assetsStage 'data\levels\pack5'
$assetsLevelPack6 = Join-Path $assetsStage 'data\levels\pack6'
$assetsLevelPack7 = Join-Path $assetsStage 'data\levels\pack7'
$assetsLevelPack8 = Join-Path $assetsStage 'data\levels\pack8'
$assetsLevelPack9 = Join-Path $assetsStage 'data\levels\pack9'
$assetsLevelPack10 = Join-Path $assetsStage 'data\levels\pack10'
$assetsLevelPack11 = Join-Path $assetsStage 'data\levels\pack11'
$assetsLevelGoldenEggs1 = Join-Path $assetsStage 'data\levels\goldeneggs1'
$assetsMenuTextures = Join-Path $assetsStage 'menu-textures'
$assetsSceneMeta = Join-Path $assetsStage 'scene-meta'
$assetsSceneTextures = Join-Path $assetsStage 'scene-textures'
$assetsDynamicSheets = Join-Path $assetsStage 'dynamic-sheets'
$assetsDynamicTextures = Join-Path $assetsStage 'dynamic-textures'
$assetsAudio = Join-Path $assetsStage 'data\audio'
New-Item -ItemType Directory -Force -Path $assetsScripts,$assetsSpriteMeta,$assetsLocalization,$assetsFonts,$assetsFontTextures,$assetsLevelPack1,$assetsLevelPack2,$assetsLevelPack3,$assetsLevelPack4,$assetsLevelPack5,$assetsLevelPack6,$assetsLevelPack7,$assetsLevelPack8,$assetsLevelPack9,$assetsLevelPack10,$assetsLevelPack11,$assetsMenuTextures,$assetsSceneMeta,$assetsSceneTextures,$assetsDynamicSheets,$assetsDynamicTextures,$assetsAudio | Out-Null
New-Item -ItemType Directory -Force -Path $assetsLevelGoldenEggs1 | Out-Null
foreach ($name in @('animations.lua','blocks.lua','gamelogic.lua','loadlist.lua','particles.lua','starLimits.lua')) {
    Copy-Item (Join-Path $scripts $name) (Join-Path $assetsScripts $name) -Force
}
Copy-Item $level1 (Join-Path $assetsStage 'Level1.lua') -Force
Copy-Item $level1 (Join-Path $assetsLevelPack1 'Level1.lua') -Force
Copy-Item $level57 (Join-Path $assetsLevelPack1 'Level57.lua') -Force
Copy-Item $level53 (Join-Path $assetsLevelPack1 'Level53.lua') -Force
Copy-Item $level3 (Join-Path $assetsLevelPack1 'Level3.lua') -Force
Copy-Item $level6 (Join-Path $assetsLevelPack1 'Level6.lua') -Force
Copy-Item $level2 (Join-Path $assetsLevelPack1 'Level2.lua') -Force
Copy-Item $level4 (Join-Path $assetsLevelPack1 'Level4.lua') -Force
Copy-Item $level5 (Join-Path $assetsLevelPack1 'Level5.lua') -Force
Copy-Item $level7 (Join-Path $assetsLevelPack1 'Level7.lua') -Force
Copy-Item $level8 (Join-Path $assetsLevelPack1 'Level8.lua') -Force
Copy-Item $level9 (Join-Path $assetsLevelPack1 'Level9.lua') -Force
Copy-Item $level13 (Join-Path $assetsLevelPack1 'Level13.lua') -Force
Copy-Item $level10 (Join-Path $assetsLevelPack1 'Level10.lua') -Force
Copy-Item $level39 (Join-Path $assetsLevelPack1 'Level39.lua') -Force
Copy-Item $level12 (Join-Path $assetsLevelPack1 'Level12.lua') -Force
Copy-Item $level15 (Join-Path $assetsLevelPack1 'Level15.lua') -Force
Copy-Item $level17 (Join-Path $assetsLevelPack1 'Level17.lua') -Force
Copy-Item $level14 (Join-Path $assetsLevelPack1 'Level14.lua') -Force
Copy-Item $level16 (Join-Path $assetsLevelPack1 'Level16.lua') -Force
Copy-Item $level23 (Join-Path $assetsLevelPack1 'Level23.lua') -Force
Copy-Item $level44 (Join-Path $assetsLevelPack1 'Level44.lua') -Force
Copy-Item $level52p2 (Join-Path $assetsLevelPack2 'Level52.lua') -Force
Copy-Item $level34p2 (Join-Path $assetsLevelPack2 'Level34.lua') -Force
Copy-Item $level42p2 (Join-Path $assetsLevelPack2 'Level42.lua') -Force
Copy-Item $level24p2 (Join-Path $assetsLevelPack2 'Level24.lua') -Force
Copy-Item $level88p2 (Join-Path $assetsLevelPack2 'Level88.lua') -Force
Copy-Item $level36p2 (Join-Path $assetsLevelPack2 'Level36.lua') -Force
Copy-Item $level31p2 (Join-Path $assetsLevelPack2 'Level31.lua') -Force
Copy-Item $level21p2 (Join-Path $assetsLevelPack2 'Level21.lua') -Force
Copy-Item $level41p2 (Join-Path $assetsLevelPack2 'Level41.lua') -Force
Copy-Item $level76p2 (Join-Path $assetsLevelPack2 'Level76.lua') -Force
Copy-Item $level38p2 (Join-Path $assetsLevelPack2 'Level38.lua') -Force
Copy-Item $level35p2 (Join-Path $assetsLevelPack2 'Level35.lua') -Force
Copy-Item $level20p2 (Join-Path $assetsLevelPack2 'Level20.lua') -Force
Copy-Item $level26p2 (Join-Path $assetsLevelPack2 'Level26.lua') -Force
Copy-Item $level66p2 (Join-Path $assetsLevelPack2 'Level66.lua') -Force
Copy-Item $level85p2 (Join-Path $assetsLevelPack2 'Level85.lua') -Force
Copy-Item $level27p2 (Join-Path $assetsLevelPack2 'Level27.lua') -Force
Copy-Item $level32p2 (Join-Path $assetsLevelPack2 'Level32.lua') -Force
Copy-Item $level72p2 (Join-Path $assetsLevelPack2 'Level72.lua') -Force
Copy-Item $level90p2 (Join-Path $assetsLevelPack2 'Level90.lua') -Force
Copy-Item $level96p2 (Join-Path $assetsLevelPack2 'Level96.lua') -Force
Copy-Item $level43p3 (Join-Path $assetsLevelPack3 'Level43.lua') -Force
Copy-Item $level77p3 (Join-Path $assetsLevelPack3 'Level77.lua') -Force
Copy-Item $level28p3 (Join-Path $assetsLevelPack3 'Level28.lua') -Force
Copy-Item $level29p3 (Join-Path $assetsLevelPack3 'Level29.lua') -Force
Copy-Item $level87p3 (Join-Path $assetsLevelPack3 'Level87.lua') -Force
Copy-Item $level18p3 (Join-Path $assetsLevelPack3 'Level18.lua') -Force
Copy-Item $level91p3 (Join-Path $assetsLevelPack3 'Level91.lua') -Force
Copy-Item $level49p3 (Join-Path $assetsLevelPack3 'Level49.lua') -Force
Copy-Item $level45p3 (Join-Path $assetsLevelPack3 'Level45.lua') -Force
Copy-Item $level75p3 (Join-Path $assetsLevelPack3 'Level75.lua') -Force
Copy-Item $level51p3 (Join-Path $assetsLevelPack3 'Level51.lua') -Force
Copy-Item $level30p3 (Join-Path $assetsLevelPack3 'Level30.lua') -Force
Copy-Item $level79p3 (Join-Path $assetsLevelPack3 'Level79.lua') -Force
Copy-Item $level40p3 (Join-Path $assetsLevelPack3 'Level40.lua') -Force
Copy-Item $level59p3 (Join-Path $assetsLevelPack3 'Level59.lua') -Force
Copy-Item $level58p3 (Join-Path $assetsLevelPack3 'Level58.lua') -Force
Copy-Item $level95p3 (Join-Path $assetsLevelPack3 'Level95.lua') -Force
Copy-Item $level82p3 (Join-Path $assetsLevelPack3 'Level82.lua') -Force
Copy-Item $level22p3 (Join-Path $assetsLevelPack3 'Level22.lua') -Force
Copy-Item $level89p3 (Join-Path $assetsLevelPack3 'Level89.lua') -Force
Copy-Item $level81p3 (Join-Path $assetsLevelPack3 'Level81.lua') -Force
Copy-Item $levelP2_103p4 (Join-Path $assetsLevelPack4 'LevelP2_103.lua') -Force
Copy-Item $levelP2_91p4 (Join-Path $assetsLevelPack4 'LevelP2_91.lua') -Force
Copy-Item $levelP2_65p4 (Join-Path $assetsLevelPack4 'LevelP2_65.lua') -Force
Copy-Item $levelP2_96p4 (Join-Path $assetsLevelPack4 'LevelP2_96.lua') -Force
Copy-Item $levelP2_69p4 (Join-Path $assetsLevelPack4 'LevelP2_69.lua') -Force
Copy-Item $levelP2_88p4 (Join-Path $assetsLevelPack4 'LevelP2_88.lua') -Force
Copy-Item $levelP2_64p4 (Join-Path $assetsLevelPack4 'LevelP2_64.lua') -Force
Copy-Item $levelP2_80p4 (Join-Path $assetsLevelPack4 'LevelP2_80.lua') -Force
Copy-Item $levelP2_108p4 (Join-Path $assetsLevelPack4 'LevelP2_108.lua') -Force
Copy-Item $levelP2_85p4 (Join-Path $assetsLevelPack4 'LevelP2_85.lua') -Force
Copy-Item $levelP2_82p4 (Join-Path $assetsLevelPack4 'LevelP2_82.lua') -Force
Copy-Item $levelP2_66p4 (Join-Path $assetsLevelPack4 'LevelP2_66.lua') -Force
Copy-Item $levelP2_104p4 (Join-Path $assetsLevelPack4 'LevelP2_104.lua') -Force
Copy-Item $levelP2_210p4 (Join-Path $assetsLevelPack4 'LevelP2_210.lua') -Force
Copy-Item $levelP2_83p4 (Join-Path $assetsLevelPack4 'LevelP2_83.lua') -Force
Copy-Item $levelP2_79p4 (Join-Path $assetsLevelPack4 'LevelP2_79.lua') -Force
Copy-Item $levelP2_77p4 (Join-Path $assetsLevelPack4 'LevelP2_77.lua') -Force
Copy-Item $levelP2_114p4 (Join-Path $assetsLevelPack4 'LevelP2_114.lua') -Force
Copy-Item $levelP2_81p4 (Join-Path $assetsLevelPack4 'LevelP2_81.lua') -Force
Copy-Item $levelP2_68p4 (Join-Path $assetsLevelPack4 'LevelP2_68.lua') -Force
Copy-Item $levelP2_95p4 (Join-Path $assetsLevelPack4 'LevelP2_95.lua') -Force
Copy-Item $levelP2_78p5 (Join-Path $assetsLevelPack5 'LevelP2_78.lua') -Force
Copy-Item $levelP2_100p5 (Join-Path $assetsLevelPack5 'LevelP2_100.lua') -Force
Copy-Item $levelP2_92p5 (Join-Path $assetsLevelPack5 'LevelP2_92.lua') -Force
Copy-Item $levelP2_94p5 (Join-Path $assetsLevelPack5 'LevelP2_94.lua') -Force
Copy-Item $levelP2_89p5 (Join-Path $assetsLevelPack5 'LevelP2_89.lua') -Force
Copy-Item $levelP2_73p5 (Join-Path $assetsLevelPack5 'LevelP2_73.lua') -Force
Copy-Item $levelP2_76p5 (Join-Path $assetsLevelPack5 'LevelP2_76.lua') -Force
Copy-Item $levelP2_122p5 (Join-Path $assetsLevelPack5 'LevelP2_122.lua') -Force
Copy-Item $levelP2_99p5 (Join-Path $assetsLevelPack5 'LevelP2_99.lua') -Force
Copy-Item $levelP2_84p5 (Join-Path $assetsLevelPack5 'LevelP2_84.lua') -Force
Copy-Item $levelP2_86p5 (Join-Path $assetsLevelPack5 'LevelP2_86.lua') -Force
Copy-Item $levelP2_74p5 (Join-Path $assetsLevelPack5 'LevelP2_74.lua') -Force
Copy-Item $levelP2_115p5 (Join-Path $assetsLevelPack5 'LevelP2_115.lua') -Force
Copy-Item $levelP2_98p5 (Join-Path $assetsLevelPack5 'LevelP2_98.lua') -Force
Copy-Item $levelP2_71p5 (Join-Path $assetsLevelPack5 'LevelP2_71.lua') -Force
Copy-Item $levelP2_72p5 (Join-Path $assetsLevelPack5 'LevelP2_72.lua') -Force
Copy-Item $levelP2_87p5 (Join-Path $assetsLevelPack5 'LevelP2_87.lua') -Force
Copy-Item $levelP2_93p5 (Join-Path $assetsLevelPack5 'LevelP2_93.lua') -Force
Copy-Item $levelP2_67p5 (Join-Path $assetsLevelPack5 'LevelP2_67.lua') -Force
Copy-Item $levelP2_97p5 (Join-Path $assetsLevelPack5 'LevelP2_97.lua') -Force
Copy-Item $levelP2_90p5 (Join-Path $assetsLevelPack5 'LevelP2_90.lua') -Force
Copy-Item $levelP3_212p6 (Join-Path $assetsLevelPack6 'LevelP3_212.lua') -Force
Copy-Item $levelP3_134p6 (Join-Path $assetsLevelPack6 'LevelP3_134.lua') -Force
Copy-Item $levelP3_162p6 (Join-Path $assetsLevelPack6 'LevelP3_162.lua') -Force
Copy-Item $levelP3_271p6 (Join-Path $assetsLevelPack6 'LevelP3_271.lua') -Force
Copy-Item $levelP3_224p6 (Join-Path $assetsLevelPack6 'LevelP3_224.lua') -Force
Copy-Item $levelP3_253p6 (Join-Path $assetsLevelPack6 'LevelP3_253.lua') -Force
Copy-Item $levelP3_225p6 (Join-Path $assetsLevelPack6 'LevelP3_225.lua') -Force
Copy-Item $levelP3_232p6 (Join-Path $assetsLevelPack6 'LevelP3_232.lua') -Force
Copy-Item $levelP3_150p6 (Join-Path $assetsLevelPack6 'LevelP3_150.lua') -Force
Copy-Item $levelP3_211p6 (Join-Path $assetsLevelPack6 'LevelP3_211.lua') -Force
Copy-Item $levelP3_223p6 (Join-Path $assetsLevelPack6 'LevelP3_223.lua') -Force
Copy-Item $levelP3_226p6 (Join-Path $assetsLevelPack6 'LevelP3_226.lua') -Force
Copy-Item $levelP3_215p6 (Join-Path $assetsLevelPack6 'LevelP3_215.lua') -Force
Copy-Item $levelP3_220p6 (Join-Path $assetsLevelPack6 'LevelP3_220.lua') -Force
Copy-Item $levelP3_231p6 (Join-Path $assetsLevelPack6 'LevelP3_231.lua') -Force
Copy-Item $levelP3_166p7 (Join-Path $assetsLevelPack7 'LevelP3_166.lua') -Force
Copy-Item $levelP3_237p7 (Join-Path $assetsLevelPack7 'LevelP3_237.lua') -Force
Copy-Item $levelP3_216p7 (Join-Path $assetsLevelPack7 'LevelP3_216.lua') -Force
Copy-Item $levelP3_298p7 (Join-Path $assetsLevelPack7 'LevelP3_298.lua') -Force
Copy-Item $levelP3_303p7 (Join-Path $assetsLevelPack7 'LevelP3_303.lua') -Force
Copy-Item $levelP3_214p7 (Join-Path $assetsLevelPack7 'LevelP3_214.lua') -Force
Copy-Item $levelP3_159p7 (Join-Path $assetsLevelPack7 'LevelP3_159.lua') -Force
Copy-Item $levelP3_164p7 (Join-Path $assetsLevelPack7 'LevelP3_164.lua') -Force
Copy-Item $levelP3_299p7 (Join-Path $assetsLevelPack7 'LevelP3_299.lua') -Force
Copy-Item $levelP3_302p7 (Join-Path $assetsLevelPack7 'LevelP3_302.lua') -Force
Copy-Item $levelP3_219p7 (Join-Path $assetsLevelPack7 'LevelP3_219.lua') -Force
Copy-Item $levelP3_163p7 (Join-Path $assetsLevelPack7 'LevelP3_163.lua') -Force
Copy-Item $levelP3_160p7 (Join-Path $assetsLevelPack7 'LevelP3_160.lua') -Force
Copy-Item $levelP3_161p7 (Join-Path $assetsLevelPack7 'LevelP3_161.lua') -Force
Copy-Item $levelP3_304p7 (Join-Path $assetsLevelPack7 'LevelP3_304.lua') -Force
Copy-Item $levelP3_297p8 (Join-Path $assetsLevelPack8 'LevelP3_297.lua') -Force
Copy-Item $levelP3_221p8 (Join-Path $assetsLevelPack8 'LevelP3_221.lua') -Force
Copy-Item $levelP3_306p8 (Join-Path $assetsLevelPack8 'LevelP3_306.lua') -Force
Copy-Item $levelP3_301p8 (Join-Path $assetsLevelPack8 'LevelP3_301.lua') -Force
Copy-Item $levelP3_312p8 (Join-Path $assetsLevelPack8 'LevelP3_312.lua') -Force
Copy-Item $levelP3_309p8 (Join-Path $assetsLevelPack8 'LevelP3_309.lua') -Force
Copy-Item $levelP3_168p8 (Join-Path $assetsLevelPack8 'LevelP3_168.lua') -Force
Copy-Item $levelP3_311p8 (Join-Path $assetsLevelPack8 'LevelP3_311.lua') -Force
Copy-Item $levelP3_308p8 (Join-Path $assetsLevelPack8 'LevelP3_308.lua') -Force
Copy-Item $levelP3_310p8 (Join-Path $assetsLevelPack8 'LevelP3_310.lua') -Force
Copy-Item $levelP3_217p8 (Join-Path $assetsLevelPack8 'LevelP3_217.lua') -Force
Copy-Item $levelP3_307p8 (Join-Path $assetsLevelPack8 'LevelP3_307.lua') -Force
Copy-Item $levelP3_296p8 (Join-Path $assetsLevelPack8 'LevelP3_296.lua') -Force
Copy-Item $levelP3_149p8 (Join-Path $assetsLevelPack8 'LevelP3_149.lua') -Force
Copy-Item $levelP3_313p8 (Join-Path $assetsLevelPack8 'LevelP3_313.lua') -Force
Copy-Item $levelP4_421p9 (Join-Path $assetsLevelPack9 'LevelP4_421.lua') -Force
Copy-Item $levelP4_423p9 (Join-Path $assetsLevelPack9 'LevelP4_423.lua') -Force
Copy-Item $levelP4_424p9 (Join-Path $assetsLevelPack9 'LevelP4_424.lua') -Force
Copy-Item $levelP4_425p9 (Join-Path $assetsLevelPack9 'LevelP4_425.lua') -Force
Copy-Item $levelP4_426p9 (Join-Path $assetsLevelPack9 'LevelP4_426.lua') -Force
Copy-Item $levelP4_427p9 (Join-Path $assetsLevelPack9 'LevelP4_427.lua') -Force
Copy-Item $levelP4_428p9 (Join-Path $assetsLevelPack9 'LevelP4_428.lua') -Force
Copy-Item $levelP4_429p9 (Join-Path $assetsLevelPack9 'LevelP4_429.lua') -Force
Copy-Item $levelP4_431p9 (Join-Path $assetsLevelPack9 'LevelP4_431.lua') -Force
Copy-Item $levelP4_432p9 (Join-Path $assetsLevelPack9 'LevelP4_432.lua') -Force
Copy-Item $levelP4_433p9 (Join-Path $assetsLevelPack9 'LevelP4_433.lua') -Force
Copy-Item $levelP4_436p9 (Join-Path $assetsLevelPack9 'LevelP4_436.lua') -Force
Copy-Item $levelP4_439p9 (Join-Path $assetsLevelPack9 'LevelP4_439.lua') -Force
Copy-Item $levelP4_440p9 (Join-Path $assetsLevelPack9 'LevelP4_440.lua') -Force
Copy-Item $levelP4_441p9 (Join-Path $assetsLevelPack9 'LevelP4_441.lua') -Force
Copy-Item $levelP4_442p10 (Join-Path $assetsLevelPack10 'LevelP4_442.lua') -Force
Copy-Item $levelP4_443p10 (Join-Path $assetsLevelPack10 'LevelP4_443.lua') -Force
Copy-Item $levelP4_444p10 (Join-Path $assetsLevelPack10 'LevelP4_444.lua') -Force
Copy-Item $levelP4_445p10 (Join-Path $assetsLevelPack10 'LevelP4_445.lua') -Force
Copy-Item $levelP4_448p10 (Join-Path $assetsLevelPack10 'LevelP4_448.lua') -Force
Copy-Item $levelP4_449p10 (Join-Path $assetsLevelPack10 'LevelP4_449.lua') -Force
Copy-Item $levelP4_451p10 (Join-Path $assetsLevelPack10 'LevelP4_451.lua') -Force
Copy-Item $levelP4_452p10 (Join-Path $assetsLevelPack10 'LevelP4_452.lua') -Force
Copy-Item $levelP4_453p10 (Join-Path $assetsLevelPack10 'LevelP4_453.lua') -Force
Copy-Item $levelP4_454p10 (Join-Path $assetsLevelPack10 'LevelP4_454.lua') -Force
Copy-Item $levelP4_455p10 (Join-Path $assetsLevelPack10 'LevelP4_455.lua') -Force
Copy-Item $levelP4_457p10 (Join-Path $assetsLevelPack10 'LevelP4_457.lua') -Force
Copy-Item $levelP4_458p10 (Join-Path $assetsLevelPack10 'LevelP4_458.lua') -Force
Copy-Item $levelP4_459p10 (Join-Path $assetsLevelPack10 'LevelP4_459.lua') -Force
Copy-Item $levelP4_462p10 (Join-Path $assetsLevelPack10 'LevelP4_462.lua') -Force
Copy-Item $levelP4_463p11 (Join-Path $assetsLevelPack11 'LevelP4_463.lua') -Force
Copy-Item $levelP4_464p11 (Join-Path $assetsLevelPack11 'LevelP4_464.lua') -Force
Copy-Item $levelP4_465p11 (Join-Path $assetsLevelPack11 'LevelP4_465.lua') -Force
Copy-Item $levelP4_466p11 (Join-Path $assetsLevelPack11 'LevelP4_466.lua') -Force
Copy-Item $levelP4_467p11 (Join-Path $assetsLevelPack11 'LevelP4_467.lua') -Force
Copy-Item $levelP4_468p11 (Join-Path $assetsLevelPack11 'LevelP4_468.lua') -Force
Copy-Item $levelP4_469p11 (Join-Path $assetsLevelPack11 'LevelP4_469.lua') -Force
Copy-Item $levelP4_470p11 (Join-Path $assetsLevelPack11 'LevelP4_470.lua') -Force
Copy-Item $levelP4_471p11 (Join-Path $assetsLevelPack11 'LevelP4_471.lua') -Force
Copy-Item $levelP4_472p11 (Join-Path $assetsLevelPack11 'LevelP4_472.lua') -Force
Copy-Item $levelP4_473p11 (Join-Path $assetsLevelPack11 'LevelP4_473.lua') -Force
Copy-Item $levelP4_474p11 (Join-Path $assetsLevelPack11 'LevelP4_474.lua') -Force
Copy-Item $levelP4_475p11 (Join-Path $assetsLevelPack11 'LevelP4_475.lua') -Force
Copy-Item $levelP4_477p11 (Join-Path $assetsLevelPack11 'LevelP4_477.lua') -Force
Copy-Item $levelP4_478p11 (Join-Path $assetsLevelPack11 'LevelP4_478.lua') -Force
Copy-Item $levelGE_1 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_1.lua') -Force
Copy-Item $levelGE_2 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_2.lua') -Force
Copy-Item $levelGE_3 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_3.lua') -Force
Copy-Item $levelGE_4 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_4.lua') -Force
Copy-Item $levelGE_5 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_5.lua') -Force
Copy-Item $levelGE_6 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_6.lua') -Force
Copy-Item $levelGE_7 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_7.lua') -Force
Copy-Item $levelGE_8 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_8.lua') -Force
Copy-Item $levelGE_9 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_9.lua') -Force
Copy-Item $levelGE_10 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_10.lua') -Force
Copy-Item $levelGE_11 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_11.lua') -Force
Copy-Item $levelGE_12 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_12.lua') -Force
Copy-Item $levelGE_13 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_13.lua') -Force
Copy-Item $levelGE_14 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_14.lua') -Force
Copy-Item $levelGE_15 (Join-Path $assetsLevelGoldenEggs1 'LevelGE_15.lua') -Force
Write-Host '[stage24.47.0-golden] Original Golden Eggs gameplay files LevelGE_1..LevelGE_15 staged; soundboards remain untouched Lua/menu-owned.'
Write-Host '[stage24.46.3-bigsetup] Original The Big Setup pack11 assets staged through page 3 / 11-15.'
Write-Host '[stage24.46.3-bigsetup] 11-1..11-15 map: LevelP4_463,LevelP4_464,LevelP4_465,LevelP4_466,LevelP4_467,LevelP4_468,LevelP4_469,LevelP4_470,LevelP4_471,LevelP4_472,LevelP4_473,LevelP4_474,LevelP4_475,LevelP4_477,LevelP4_478.'
Write-Host '[stage24.46.2-bigsetup] Original The Big Setup pack10 assets staged through page 2 / 10-15.'
Write-Host '[stage24.46.2-bigsetup] 10-1..10-15 map: LevelP4_442,LevelP4_443,LevelP4_444,LevelP4_445,LevelP4_448,LevelP4_449,LevelP4_451,LevelP4_452,LevelP4_453,LevelP4_454,LevelP4_455,LevelP4_457,LevelP4_458,LevelP4_459,LevelP4_462.'
Write-Host '[stage24.46.0-bigsetup] Original The Big Setup pack9 assets staged through page 1 / 9-15.'
Write-Host '[stage24.46.0-bigsetup] 9-1..9-15 map: LevelP4_421,LevelP4_423,LevelP4_424,LevelP4_425,LevelP4_426,LevelP4_427,LevelP4_428,LevelP4_429,LevelP4_431,LevelP4_432,LevelP4_433,LevelP4_436,LevelP4_439,LevelP4_440,LevelP4_441.'
Write-Host '[stage24.45.1-danger] Original Danger Above pack8 assets staged through page 3 / 8-15.'
Write-Host '[stage24.45.1-danger] 8-1..8-15 map: LevelP3_297,LevelP3_221,LevelP3_306,LevelP3_301,LevelP3_312,LevelP3_309,LevelP3_168,LevelP3_311,LevelP3_308,LevelP3_310,LevelP3_217,LevelP3_307,LevelP3_296,LevelP3_149,LevelP3_313.'
Write-Host '[stage24.45.0-danger] Original Danger Above pack7 assets staged through page 2 / 7-15.'
Write-Host '[stage24.45.0-danger] 7-1..7-15 map: LevelP3_166,LevelP3_237,LevelP3_216,LevelP3_298,LevelP3_303,LevelP3_214,LevelP3_159,LevelP3_164,LevelP3_299,LevelP3_302,LevelP3_219,LevelP3_163,LevelP3_160,LevelP3_161,LevelP3_304.'
Write-Host '[stage24.42.0-danger] Original Danger Above pack6 assets staged through page 1 / 6-15.'
Write-Host '[stage24.42.0-danger] 6-1..6-15 map: LevelP3_212,LevelP3_134,LevelP3_162,LevelP3_271,LevelP3_224,LevelP3_253,LevelP3_225,LevelP3_232,LevelP3_150,LevelP3_211,LevelP3_223,LevelP3_226,LevelP3_215,LevelP3_220,LevelP3_231.'
Write-Host '[stage24.41.1-mighty] Original Mighty Hoax pack5 assets staged through human 5-21.'
Write-Host '[stage24.41.1-mighty] 5-11..5-21 map: LevelP2_86,LevelP2_74,LevelP2_115,LevelP2_98,LevelP2_71,LevelP2_72,LevelP2_87,LevelP2_93,LevelP2_67,LevelP2_97,LevelP2_90.'
Write-Host '[stage24.41.0-mighty] Original Mighty Hoax pack5 assets staged through human 5-10.'
Write-Host '[stage24.41.0-mighty] 5-1..5-10 map: LevelP2_78,LevelP2_100,LevelP2_92,LevelP2_94,LevelP2_89,LevelP2_73,LevelP2_76,LevelP2_122,LevelP2_99,LevelP2_84.'
Write-Host '[stage24.40.2-mighty] Original Mighty Hoax pack4 assets staged through human 4-21.'
Write-Host '[stage24.40.2-mighty] 4-11..4-21 map: LevelP2_82,LevelP2_66,LevelP2_104,LevelP2_210,LevelP2_83,LevelP2_79,LevelP2_77,LevelP2_114,LevelP2_81,LevelP2_68,LevelP2_95.'
Write-Host '[stage24.40.1-mighty] Original Mighty Hoax pack4 assets staged through human 4-10.'
Write-Host '[stage24.40.1-mighty] 4-6..4-10 map: LevelP2_88,LevelP2_64,LevelP2_80,LevelP2_108,LevelP2_85.'
Write-Host '[stage24.39.0] Original Mighty Hoax pack4 assets staged through human 4-5.'
Write-Host '[stage24.39.0] Original map: 4-1=LevelP2_103 4-2=LevelP2_91 4-3=LevelP2_65 4-4=LevelP2_96 4-5=LevelP2_69.'
Write-Host '[stage24.38.1] Original pack3 assets staged through human 3-21.'
Write-Host '[stage24.38.1] Original map 3-6..3-21: Level18,Level91,Level49,Level45,Level75,Level51,Level30,Level79,Level40,Level59,Level58,Level95,Level82,Level22,Level89,Level81.'
Write-Host '[stage24.38.0] Original pack3 assets staged through human 3-5: Level43,Level77,Level28,Level29,Level87.'
Write-Host '[stage24.36.1] Original pack2 assets staged through human 2-21.'
Write-Host '[stage24.36.1] Original map 2-15..2-21: Level66,Level85,Level27,Level32,Level72,Level90,Level96.'
Write-Host '[stage24.37.0] RenderState2D re-audit active: scale is applied after local rotation/pivot + draw-origin translation.'
Write-Host '[stage24.37.0] LS_BACKGROUND remains untouched Lua-owned two-half composition; no sprite-specific geometry fix.'
Write-Host '[stage24.36.0] Original pack2 assets staged through human 2-14 (White debut).'
Write-Host '[stage24.36.0] Original map 2-6..2-14: Level36,Level31,Level21,Level41,Level76,Level38,Level35,Level20,Level26.'
Write-Host '[stage24.35.0] Original pack2 assets staged through human 2-5.'
Write-Host '[stage24.35.0] Original map: 2-1=Level52 2-2=Level34 2-3=Level42 2-4=Level24 2-5=Level88.'
Write-Host '[stage24.34.1] Original pack1 assets staged through human 1-21.'
Write-Host '[stage24.34.1] Original map: 1=Level1 2=Level57 3=Level53 4=Level3 5=Level6 6=Level2 7=Level4 8=Level5 9=Level7 10=Level8 11=Level9 12=Level13 13=Level10 14=Level39 15=Level12 16=Level15 17=Level17 18=Level14 19=Level16 20=Level23 21=Level44.'
Write-Host '[stage24.32.1] Stock getNextLevel/unlock/save remains authoritative; no level transition override is installed.'
Write-Host '[stage24] Level resource-path preflight PASS: data/levels/pack1/Level1 -> data/levels/pack1/Level1.lua'
Copy-Item $blocksDat (Join-Path $assetsStage 'INGAME_BLOCKS_1.dat') -Force
Copy-Item $birdsDat (Join-Path $assetsStage 'INGAME_BIRDS_1.dat') -Force
Copy-Item $blocksPvr (Join-Path $assetsStage 'INGAME_BLOCKS_1.pvr') -Force
Copy-Item $birdsPvr (Join-Path $assetsStage 'INGAME_BIRDS_1.pvr') -Force
Copy-Item $themeGroundPvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_1.pvr') -Force
Copy-Item $themeGround2Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_2.pvr') -Force
Copy-Item $themeGround3Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_3.pvr') -Force
Copy-Item $themeGround4Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_4.pvr') -Force
Copy-Item $themeGround5Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_5.pvr') -Force
Copy-Item $themeGround6Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_6.pvr') -Force
Copy-Item $themeGround7Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_7.pvr') -Force
Copy-Item $themeGround8Pvr (Join-Path $assetsStage 'INGAME_THEME_GROUND_8.pvr') -Force
Write-Host '[stage24.45.1-mask] Exact INGAME_THEME_GROUND_1/2/3/4/5/6/7/8.pvr staged for generic native MaskedImage terrain renderer.'

# Stage 24.15.3 + 24.35.0: transport the original global scene families
# needed by theme1 plus the recovered theme2 parallax family. PVR bytes are
# unchanged; DAT metadata remains the original KA3D SPRT rect/pivot source.
foreach ($name in $themeSceneMetaNames) {
    Copy-Item (Join-Path $imageRoot $name) (Join-Path $assetsSceneMeta $name) -Force
}
$sceneTextureManifest = @()
foreach ($name in $themeSceneTextureNames) {
    Copy-Item (Join-Path $imageRoot $name) (Join-Path $assetsSceneTextures $name) -Force
    $sceneTextureManifest += "$name`tPVRV2`t$name"
}
[IO.File]::WriteAllText((Join-Path $assetsSceneTextures 'manifest.tsv'), (($sceneTextureManifest -join "`n") + "`n"), [Text.Encoding]::ASCII)
Write-Host "[stage24.46.0-scene] Retained Theme1..8 scene families + original CRANES discovery sheet staged meta=$($themeSceneMetaNames.Count) textures=$($themeSceneTextureNames.Count)"
Copy-Item $textsBasic (Join-Path $assetsLocalization 'TEXTS_BASIC.dat') -Force
foreach ($name in $fontDatNames) {
    Copy-Item (Join-Path $fontProfileRoot $name) (Join-Path $assetsFonts $name) -Force
}
$fontTextureManifest = @()
foreach ($entry in $fontTextureInputs) {
    Copy-Item $entry.Path (Join-Path $assetsFontTextures $entry.Asset) -Force
    $fontTextureManifest += "$($entry.Logical)`t$($entry.Kind)`t$($entry.Asset)"
}
[IO.File]::WriteAllText((Join-Path $assetsFontTextures 'manifest.tsv'), (($fontTextureManifest -join "`n") + "`n"), [Text.Encoding]::ASCII)
Write-Host "[stage24.23.3-font] Bitmap-font texture transports staged: $($fontTextureManifest.Count)"
foreach ($name in $menuMetaNames) {
    Copy-Item (Join-Path $imageRoot $name) (Join-Path $assetsSpriteMeta $name) -Force
}
# Stage 24.30.4: one authoritative ordered manifest owns the pre-GPU
# MENU/OTHER SpriteDB set. The runtime uses this exact list both to extract
# DATs from the APK and to load them into the global sprite registry, avoiding
# drift between PowerShell staging and historical C++ hardcoded lists.
$bootstrapMenuMetaManifest = Join-Path $assetsSpriteMeta 'bootstrap-menu-meta.txt'
[IO.File]::WriteAllText($bootstrapMenuMetaManifest, (($menuMetaNames -join "`n") + "`n"), [Text.Encoding]::ASCII)
Write-Host "[stage24.30.4-bootstrap-meta] authoritative ordered manifest entries=$($menuMetaNames.Count) names=$($menuMetaNames -join ', ')"
Copy-Item $tutorialCompoDat (Join-Path $assetsSpriteMeta 'TUTORIALS_composprites.dat') -Force
$menuTextureManifest = @()
foreach ($entry in $menuTextureInputs) {
    Copy-Item $entry.Path (Join-Path $assetsMenuTextures $entry.Asset) -Force
    $menuTextureManifest += "$($entry.Logical)`t$($entry.Kind)`t$($entry.Asset)"
}
[IO.File]::WriteAllText((Join-Path $assetsMenuTextures 'manifest.tsv'), (($menuTextureManifest -join "`n") + "`n"), [Text.Encoding]::ASCII)
Write-Host "[stage24.13.2c] Original menu textures staged as neutral .bin transports with LF-only manifest: $($menuTextureManifest.Count) manifest entries"

# Stage 24.30.1: keep cutscene DATs and their textures outside the bootstrap
# registry. They are present in the APK but become visible to SpriteDB/GLES only
# through res.createSpriteSheet at runtime.
foreach ($name in $cutsceneMetaNames) {
    Copy-Item (Join-Path $imageRoot $name) (Join-Path $assetsDynamicSheets $name) -Force
}
$dynamicTextureManifest = @()
foreach ($entry in $cutsceneTextureInputs) {
    Copy-Item $entry.Path (Join-Path $assetsDynamicTextures $entry.Asset) -Force
    $dynamicTextureManifest += "$($entry.Logical)`t$($entry.Kind)`t$($entry.Asset)"
}
[IO.File]::WriteAllText((Join-Path $assetsDynamicTextures 'manifest.tsv'), (($dynamicTextureManifest -join "`n") + "`n"), [Text.Encoding]::ASCII)
Write-Host "[stage24.30.1-cutscene] Dynamic original transports staged meta=$($cutsceneMetaNames.Count) textures=$($dynamicTextureManifest.Count)"
Write-Host "[stage24] Original MENU/OTHER sprite metadata staged: $($menuMetaNames -join ', '), TUTORIALS_composprites.dat"
Write-Host "[stage24] Original localization staged: TEXTS_BASIC.dat"
Write-Host "[stage24] Original 864x480 bitmap-font DATs staged: $($fontDatNames -join ', ')"

# Transport the user's untouched audio subtree. Keep names, spaces, extensions
# and directory layout byte-for-byte; AAssetManager reads these entries directly
# at stage24/data/audio/... and the ZIP distributed by this project never embeds
# the proprietary payload.
Copy-Item -Path (Join-Path $audioRoot '*') -Destination $assetsAudio -Recurse -Force
$stagedAudioFiles = @(Get-ChildItem -LiteralPath $assetsAudio -Recurse -File)
$stagedWav = @($stagedAudioFiles | Where-Object { $_.Extension -ieq '.wav' })
$stagedMp3 = @($stagedAudioFiles | Where-Object { $_.Extension -ieq '.mp3' })
Write-Host "[stage24.25.2-audio] Original audio subtree staged wav=$($stagedWav.Count) mp3=$($stagedMp3.Count) total=$($stagedAudioFiles.Count)"

$manifest = if ($BuildFlavor -eq 'Release') {
    Join-Path $root 'stage24-android\AndroidManifest.release.xml'
} else {
    Join-Path $root 'stage24-android\AndroidManifest.xml'
}
# Stage24.49.0B: legacy aapt is reliable only when the -M input itself is
# named AndroidManifest.xml.  Keep flavor manifests immutable in source, but
# stage the selected one under that canonical basename before packaging.
$packageManifestDir = Join-Path $apkWork 'package-manifest'
New-Item -ItemType Directory -Force -Path $packageManifestDir | Out-Null
$packageManifest = Join-Path $packageManifestDir 'AndroidManifest.xml'
Copy-Item -LiteralPath $manifest -Destination $packageManifest -Force
$manifestSourceHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
$manifestStagedHash = (Get-FileHash -LiteralPath $packageManifest -Algorithm SHA256).Hash.ToLowerInvariant()
if ($manifestSourceHash -ne $manifestStagedHash) {
    throw "Canonical AndroidManifest.xml staging changed bytes source=$manifestSourceHash staged=$manifestStagedHash"
}
Write-Host "[stage24.49.0b-release] Canonical manifest staging PASS flavor=$BuildFlavor sha256=$manifestStagedHash"
$unsigned = Join-Path $apkWork 'stage24-unsigned.apk'
$withLib = Join-Path $apkWork 'stage24-with-lib.apk'
$aligned = Join-Path $apkWork 'stage24-aligned.apk'
$signed = if ($BuildFlavor -eq 'Release') {
    Join-Path $outputDir 'Angry-Birds-1.0.0-arm64-v8a.apk'
} else {
    Join-Path $outputDir 'angry-arm64-stage24-audited.apk'
}
foreach ($f in @($unsigned,$withLib,$aligned,$signed)) { if (Test-Path $f) { Remove-Item $f -Force } }

# Legacy Android build-tools (notably aapt/ziparchive) can mis-handle a UTF-8
# user-profile path containing non-ASCII characters even though PowerShell/.NET and
# Clang handle it correctly.  Map USERPROFILE to a temporary ASCII-only DOS
# drive for the native packaging tools.  This changes no project files and
# requires no administrator privileges.
function Get-FreeSubstDrive {
    foreach ($letter in @('Z','Y','X','W','V','U','T','S','R','Q')) {
        $drive = "${letter}:"
        if (
            !(Get-PSDrive -Name $letter -ErrorAction SilentlyContinue) -and
            !(Test-Path "$drive\")
        ) {
            return $drive
        }
    }
    throw 'No free drive letter available for Stage24 ASCII path bridge.'
}

$asciiBridges = @()

function New-AsciiPathBridge([string]$rootPath) {
    $fullRoot = [IO.Path]::GetFullPath($rootPath)

    # Preserve drive roots such as D:\ while normalizing normal directories.
    if ($fullRoot.Length -gt 3) {
        $fullRoot = $fullRoot.TrimEnd('\')
    }

    $drive = Get-FreeSubstDrive

    & subst.exe $drive $fullRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create Stage24 ASCII path bridge at $drive -> $fullRoot"
    }

    $bridge = [pscustomobject]@{
        Drive = $drive
        Root  = $fullRoot
    }

    $script:asciiBridges += $bridge

    Write-Host "[stage24] ASCII path bridge: $drive -> $fullRoot"
    return $bridge
}

function Convert-ToAsciiBridgePath([string]$path,$bridge) {
    $rootPath = [IO.Path]::GetFullPath($bridge.Root)
    if ($rootPath.Length -gt 3) {
        $rootPath = $rootPath.TrimEnd('\')
    }

    $full = [IO.Path]::GetFullPath($path)

    $same = $full.Equals(
        $rootPath,
        [StringComparison]::OrdinalIgnoreCase
    )

    $inside = $full.StartsWith(
        $rootPath.TrimEnd('\') + '\',
        [StringComparison]::OrdinalIgnoreCase
    )

    if (!$same -and !$inside) {
        throw "Path '$full' is outside ASCII bridge root '$rootPath'."
    }

    if ($same) {
        return "$($bridge.Drive)\"
    }

    $relative = $full.Substring($rootPath.TrimEnd('\').Length).TrimStart('\')
    return "$($bridge.Drive)\$relative"
}

function Remove-AsciiPathBridges {
    foreach ($bridge in @($script:asciiBridges | Select-Object -Last 100)) {
        if ($null -eq $bridge) { continue }

        & subst.exe $bridge.Drive /D 2>$null | Out-Null
    }

    $script:asciiBridges = @()
}

try {
    # Project and Android SDK can live on completely different volumes.
    $projectBridge = New-AsciiPathBridge $root
    $sdkBridge = New-AsciiPathBridge $sdk

    $aaptAscii = Convert-ToAsciiBridgePath $aapt $sdkBridge
    $androidJarAscii = Convert-ToAsciiBridgePath $androidJar $sdkBridge
    $zipalignAscii = Convert-ToAsciiBridgePath $zipalign $sdkBridge
    $apksignerAscii = Convert-ToAsciiBridgePath $apksigner $sdkBridge

    $manifestAscii = Convert-ToAsciiBridgePath $packageManifest $projectBridge
    $assetsRootAscii = Convert-ToAsciiBridgePath $assetsRoot $projectBridge
    $resRootAscii = Convert-ToAsciiBridgePath $resRoot $projectBridge
    $unsignedAscii = Convert-ToAsciiBridgePath $unsigned $projectBridge
    $withLibAscii = Convert-ToAsciiBridgePath $withLib $projectBridge
    $alignedAscii = Convert-ToAsciiBridgePath $aligned $projectBridge
    $signedAscii = Convert-ToAsciiBridgePath $signed $projectBridge

Write-Host '[stage24] Packaging NativeActivity APK with locally sourced original Level1 + Level57 (1-2) assets...'
& $aaptAscii package -f -0 mp3 -M $manifestAscii -I $androidJarAscii -S $resRootAscii -A $assetsRootAscii -F $unsignedAscii
$aaptExit = $LASTEXITCODE
if ($aaptExit -ne 0) {
    Remove-AsciiPathBridges
    throw "aapt package failed: $aaptExit"
}

# Python adds the ABI library entry without requiring Gradle/Android Studio.
$addLibPy = Join-Path $root 'tools\apk_add_native_lib.py'
& $python $addLibPy $unsigned $withLib $so 'lib/arm64-v8a/libangryarm64.so'
if ($LASTEXITCODE -ne 0) { throw 'Adding native library to APK failed.' }

# Stage 24.13.2a: aapt on this legacy packaging path can silently omit some
# nested raw PVR assets.  Verify the DAT-derived menu transport directory in
# the actual APK and inject only entries that aapt omitted.  Bytes are copied
# unchanged; this is packaging-only and does not alter renderer semantics.
$ensureMenuAssetsPy = Join-Path $root 'tools\apk_ensure_asset_dir.py'
& $python $ensureMenuAssetsPy $withLib $assetsMenuTextures 'assets/stage24/menu-textures'
if ($LASTEXITCODE -ne 0) { throw 'Menu texture APK verification/injection failed.' }
& $python $ensureMenuAssetsPy $withLib $assetsFontTextures 'assets/stage24/font-textures'
if ($LASTEXITCODE -ne 0) { throw 'Bitmap-font texture APK verification/injection failed.' }
& $python $ensureMenuAssetsPy $withLib $assetsSceneTextures 'assets/stage24/scene-textures'
if ($LASTEXITCODE -ne 0) { throw 'Theme scene texture APK verification/injection failed.' }
& $python $ensureMenuAssetsPy $withLib $assetsSceneMeta 'assets/stage24/scene-meta'
if ($LASTEXITCODE -ne 0) { throw 'Theme scene metadata APK verification/injection failed.' }
& $python $ensureMenuAssetsPy $withLib $assetsAudio 'assets/stage24/data/audio'
if ($LASTEXITCODE -ne 0) { throw 'Original audio payload APK verification/injection failed.' }
Write-Host "[stage24.25.2-audio] APK audio transport verification PASS wav=$($stagedWav.Count) mp3=$($stagedMp3.Count)"
& $zipalignAscii -f -p 4 $withLibAscii $alignedAscii
if ($LASTEXITCODE -ne 0) { throw "zipalign failed: $LASTEXITCODE" }

if ($BuildFlavor -eq 'Release') {
    if ([string]::IsNullOrWhiteSpace($ReleaseKeystore)) { throw 'Release build requires -ReleaseKeystore.' }
    if (!(Test-Path -LiteralPath $ReleaseKeystore)) { throw "Release keystore not found: $ReleaseKeystore" }
    $releaseSecret = [Environment]::GetEnvironmentVariable($ReleasePasswordEnv, 'Process')
    if ([string]::IsNullOrEmpty($releaseSecret)) { throw "Release signing password env '$ReleasePasswordEnv' is not set in this process." }
    $releaseKeyParent = Split-Path -Parent ([IO.Path]::GetFullPath($ReleaseKeystore))
    $releaseKeyBridge = New-AsciiPathBridge $releaseKeyParent
    $releaseKeyAscii = Convert-ToAsciiBridgePath $ReleaseKeystore $releaseKeyBridge
    $passSpec = "env:$ReleasePasswordEnv"
    & $apksignerAscii sign --ks $releaseKeyAscii --ks-pass $passSpec --key-pass $passSpec --ks-key-alias $ReleaseAlias --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --out $signedAscii $alignedAscii
    if ($LASTEXITCODE -ne 0) { throw "release apksigner failed: $LASTEXITCODE" }
} else {
    # Persistent local audit key: never used for public release artifacts.
    $androidHome = Join-Path $env:USERPROFILE '.android'
    New-Item -ItemType Directory -Force -Path $androidHome | Out-Null
    $debugKey = Join-Path $androidHome 'angry-arm64-stage24-debug.keystore'
    if (!(Test-Path $debugKey)) {
        $keytoolCmd = Get-Command keytool -ErrorAction SilentlyContinue
        if (!$keytoolCmd) { throw 'keytool not found; cannot create Stage24 audit signing key.' }
        & $keytoolCmd.Source -genkeypair -v -keystore $debugKey -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=Angry ARM64 Stage24 Audit,O=Local'
        if ($LASTEXITCODE -ne 0) { throw 'Stage24 audit keystore generation failed.' }
    }
    $debugKeyBridge = New-AsciiPathBridge $androidHome
    $debugKeyAscii = Convert-ToAsciiBridgePath $debugKey $debugKeyBridge
    & $apksignerAscii sign --ks $debugKeyAscii --ks-pass pass:android --key-pass pass:android --ks-key-alias androiddebugkey --out $signedAscii $alignedAscii
    if ($LASTEXITCODE -ne 0) { throw "audit apksigner failed: $LASTEXITCODE" }
}
& $apksignerAscii verify --verbose --print-certs $signedAscii
if ($LASTEXITCODE -ne 0) { throw 'APK signature verification failed.' }

# Stage 24.48.0 post-package proof: the candidate APK must contain exactly the
# reconstructed ARM64 native runtime and no ARMv7 fallback/emulation payload.
$rc480Apk = Join-Path $outputDir 'stage24.48.0-apk-payload-audit.txt'
$rc480ApkLines = @(& $python (Join-Path $root 'tools\stage24480_apk_payload_audit.py') $signed 2>&1 | ForEach-Object { "$_" })
$rc480ApkExit = $LASTEXITCODE
$rc480ApkLines | Set-Content -Encoding UTF8 $rc480Apk
if ($rc480ApkExit -ne 0) { throw "Stage 24.48.0 APK payload audit failed exit=$rc480ApkExit report=$rc480Apk" }
Write-Host "[stage24.48.0-rc] APK payload arm64-only PASS report=$rc480Apk"

# Stage24.48.1 post-package proof: the installed-facing APK must expose the
# exact Angry Birds label and a real launcher icon resource.
$branding481Apk = Join-Path $outputDir 'stage24.48.1-apk-branding-audit.txt'
$branding481Badging = @(& $aaptAscii dump badging $signedAscii 2>&1 | ForEach-Object { "$_" })
$branding481Badging | Set-Content -Encoding UTF8 $branding481Apk
$branding481Text = $branding481Badging -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Stage 24.48.1 aapt badging audit failed report=$branding481Apk" }
if ($branding481Text -notmatch "application: label='Angry Birds'") { throw "Stage 24.48.1 APK label mismatch report=$branding481Apk" }
if ($branding481Text -notmatch "icon='res/drawable/app_icon.png'") { throw "Stage 24.48.1 APK launcher icon resource missing/mismatched report=$branding481Apk" }
Write-Host "[stage24.48.1-branding] APK label/icon badging PASS report=$branding481Apk"

Write-Host "[stage24] APK ready: $signed"
if ($SkipInstall) {
    Remove-AsciiPathBridges
    Write-Host '[stage24] ASCII path bridge released.'
    Write-Host "[stage24] BuildFlavor=$BuildFlavor SkipInstall=TRUE; APK was not installed/launched."
    return
}
Write-Host "[stage24] Installing $BuildFlavor build on connected device..."
& $adb get-state
if ($LASTEXITCODE -ne 0) { throw 'adb device unavailable.' }
& $adb install -r $signedAscii
if ($LASTEXITCODE -ne 0) { Remove-AsciiPathBridges; throw "adb install failed: $LASTEXITCODE" }
Remove-AsciiPathBridges
Write-Host '[stage24] ASCII path bridge released.'
& $adb shell am force-stop $packageName | Out-Null
& $adb logcat -c
& $adb shell am start -n $component
if ($LASTEXITCODE -ne 0) { throw 'Could not launch NativeActivity.' }

Start-Sleep -Seconds 3
$logPath = Join-Path $outputDir 'stage24-initial-logcat.txt'
$initialLog = @(& $adb logcat -d -s 'AngryARM64:I' '*:S')
$initialLog | Set-Content -Encoding UTF8 $logPath
# Stage 24.15.3: raw logs belong in diagnostic files, not in an ever-growing
# terminal transcript. Keep the initial log on disk and print only a compact
# capture status; pull-stage24-live-log.ps1 packages the useful evidence.
Write-Host "[stage24] Initial logcat captured: $logPath lines=$($initialLog.Count)"

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.32.1 Pack1 1-10 + Multitouch + Specialty Audit build/install complete'
Write-Host '============================================================'
Write-Host 'Stage24.25 audio, Stage24.26 trajectory, Stage24.27 bird-rest telemetry, Stage24.28 menu/UI closure, and Stage24.29 vanilla boot remain unchanged.'
Write-Host 'STARTUP UNDER TEST: the stable Level1 scaffold may still be materialized internally, but it is frozen and hidden. No gameplay update/physics/render is allowed before branding finishes.'
Write-Host 'CORE ORIGINAL SEQUENCE: SPLASH_ROVIO 2s on white -> SPLASH_ANGRY_BIRDS 1s on black -> untouched mainMenu/updateMenu. Stage24.29.1 adds exact legacy PVR v2 RGB565 upload for the original splash atlases; no pixel conversion or substitute art.'
Write-Host 'KNOWN BOOT GAP: the untouched Android branch attempts to draw SPLASH_LOADING during the Angry Birds splash. It is not a timed splash entry, and its concrete owner is unresolved in the retained 864x480 corpus, so this stage logs/defer it instead of inventing art.'
Write-Host 'UI SEAM STATUS: Stage24.31.4e proved the remaining seams were caused by pre-raster magnification. Stage24.31.4f keeps the legacy renderer at 854x480 1:1, copies the completed frame into an outer presentation texture, and scales that single image to the modern Surface. Legacy sprite UV/sampler/POT semantics remain untouched.'
Write-Host 'GEAR/GOLDEN EGG: Stage24.31.5b recovered per-draw RenderState2D semantics remain active; user validation closed the settings-gear visual regression. Golden-Egg behavior remains governed by the same global renderer semantic.'
Write-Host 'PROGRESSION: Stage24.32.1 transports the untouched original Pack1 files through human 1-10. Stock Lua still owns next-level selection, unlocks, highscores and save.'
Write-Host 'Stage24.31.1 real save/restart persistence remains active and unchanged.'
Write-Host 'Touching a splash should skip that entry through the recovered LBUTTON semantics.'
Write-Host 'CUTSCENE IMPLEMENTATION: dynamic create/release sheet registry + texture ownership are live, and setRenderState accepts the recovered 2/4/5/7-argument forms. Navigate from fresh boot to Poached Eggs 1-1 and let gameStart run without skipping.' 
Write-Host 'VALIDATION: run .\test-stage24-pack1-multitouch-specialty.ps1; test two-finger zoom, progress through 1-9, then launch Blue on 1-10 and tap once in flight. Passive score telemetry remains enabled.'
Write-Host "APK: $signed"
Write-Host "Initial logcat: $logPath"
Write-Host 'To collect the live log after playing, run: .\pull-stage24-live-log.ps1'
} finally {
    Remove-AsciiPathBridges
}
