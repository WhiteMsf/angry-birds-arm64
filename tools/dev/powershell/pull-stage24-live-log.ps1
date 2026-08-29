param([switch]$Full)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
if (!(Test-Path $adb)) { throw 'adb.exe not found.' }
$out = Join-Path $root 'stage24-output'
New-Item -ItemType Directory -Force -Path $out | Out-Null

$logcat = Join-Path $out 'stage24-live-logcat.txt'
$stdout = Join-Path $out 'stage24-native-stdout.log'
$stderr = Join-Path $out 'stage24-native-stderr.log'
$summary = Join-Path $out 'stage24-summary.txt'
$bundle = Join-Path $out 'stage24-diagnostics.zip'
$pkg = 'dev.angryarm64.stage24'

@(& $adb logcat -d -s 'AngryARM64:I' '*:S') | Set-Content -Encoding UTF8 $logcat
& $adb exec-out run-as $pkg cat 'files/stage24/stage24-native-stdout.log' 2>$null | Set-Content -Encoding UTF8 $stdout
& $adb exec-out run-as $pkg cat 'files/stage24/stage24-native-stderr.log' 2>$null | Set-Content -Encoding UTF8 $stderr

$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add('ANGRY_STAGE24_DIAGNOSTIC_SUMMARY 1')
$summaryLines.Add(('generated=' + (Get-Date).ToString('o')))
$summaryLines.Add('')

function Add-Matches([string]$title, [string]$path, [string]$pattern) {
    $summaryLines.Add(('--- ' + $title + ' ---'))
    if (Test-Path $path) {
        $matches = Select-String -Path $path -Pattern $pattern -ErrorAction SilentlyContinue
        if ($matches) {
            foreach ($m in $matches) { $summaryLines.Add($m.Line) }
        } else {
            $summaryLines.Add('(none)')
        }
    } else {
        $summaryLines.Add('(file missing)')
    }
    $summaryLines.Add('')
}

Add-Matches 'level / mode transitions' $logcat 'loadLevel resource path|scene contract level=|native level scene reset|currentGameMode=updateLoading|currentGameMode=updateGame|currentGameMode=updateMenu'
Add-Matches 'scene contract / render' $stdout 'stage24\.15\.0-scene|stage24\.15\.2-theme|stage24\.15\.3-theme|stage24\.15\.3-scene|stage24\.15\.4-scene|stage24\.15\.5-scene|stage24\.15\.5-scene-dat'
Add-Matches 'terrain first-pass' $stdout 'first visual terrain batch'
Add-Matches 'runtime failures' $logcat 'LIVE LUA FAIL|LUA ERROR|game thread exited|GPU frame FAIL|GPU scene initialization FAIL'
Add-Matches 'native stderr failures' $stderr 'ERROR|FAIL|failed|attempt to index|addParticles|blockCollision|birdCollision'
Add-Matches 'presentation / resolution audit' $stdout 'stage24\.17\.0-context-presentation|stage24\.16\.0-live-presentation|stage24\.16\.1-selector-matrix|stage24\.15\.6-presentation|stage24\.13\.3-ui-scale'
Add-Matches 'slingshot runtime state' $logcat 'LIVE state frame=|rubberBandPos|rubberBandLength|currentBird=|flyingBird=|Stage24\.18\.2 slingshot render'
Add-Matches 'gameplay score HUD audit' $stdout 'stage24\.19\.0-score-hud-lua'
Add-Matches 'score fidelity ledger' $stdout 'stage24\.19\.1-score-ledger'
Add-Matches 'restored ordinary-contact score' $stdout 'stage24\.19\.3-block-score-restored'
Add-Matches 'gameplay score HUD runtime' $stdout 'stage24\.20\.0-score-hud'
Add-Matches 'level failed contract audit' $stdout 'stage24\.22\.0-failure-lua|stage24\.22\.0-failure-runtime'
Add-Matches 'remaining gameplay HUD runtime' $stdout 'stage24\.23\.1-gameplay-hud'
Add-Matches 'pause menu runtime' $stdout 'stage24\.23\.2-pause-menu'
Add-Matches 'particle runtime / HUD alpha audit' $stdout 'stage24\.24\.1-particle-spawn|stage24\.24\.1-hud-alpha'
Add-Matches 'trajectory system audit' $stdout 'stage24\.26\.0-trajectory-(runtime|summary|state|lua|bytecode)'
Add-Matches 'trajectory renderer / puff audit' $stdout 'stage24\.26\.1-puff-(lua|bytecode|constant|runtime)'
Add-Matches 'trajectory renderer implementation' $stdout 'stage24\.26\.2-trajectory-(render|native)'
Add-Matches 'menu render ownership / background' $stdout 'stage24\.28\.3-(render-ownership|menu-background|menu-theme)'
Add-Matches 'cutscene/story contract frontier' $stdout 'stage24\.30\.0-cutscene-(runtime|lua|table)|stage24\.30\.1-(dynamic-sheet|render-state|cutscene-runtime)|createSpriteSheet|releaseSpriteSheet|loadCutScenes|prepareCutScene' 
Add-Matches 'real save / restart persistence' $stdout 'stage24\.31\.1-persistence'
Add-Matches 'menu transform micro-fidelity frontier' $stdout 'stage24\.31\.3-ui.*(RENDER_STATE|MAIN_SETTINGS|GOLDEN_EGG)|stage24\.30\.1-render-state'
Add-Matches 'passive score fidelity' $stdout 'stage24\.31\.5-score-passive'

$presentationLive = Join-Path $out 'stage24.16.0-live-presentation-contract.txt'
$presentationLines = New-Object System.Collections.Generic.List[string]
$presentationLines.Add('ANGRY_STAGE24_16_0_LIVE_PRESENTATION_CONTRACT 1')
$presentationLines.Add('policy=diagnostic-only; records current harness and original Lua selector responses; does not assert 480x320 as original Android presentation')
$presentationLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.16\.0-live-presentation|stage24\.15\.6-presentation|stage24\.13\.3-ui-scale' -ErrorAction SilentlyContinue)) {
        $presentationLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'LIVE EGL Surface ready|Stage24\.13\.3 screen profile|Stage24\.15\.6 gameplay presentation' -ErrorAction SilentlyContinue)) {
        $presentationLines.Add($m.Line)
    }
}
$presentationLines | Set-Content -Encoding UTF8 $presentationLive

$contextPresentation = Join-Path $out 'stage24.17.0-context-presentation.txt'
$contextPresentationLines = New-Object System.Collections.Generic.List[string]
$contextPresentationLines.Add('ANGRY_STAGE24_17_0_CONTEXT_PRESENTATION 1')
$contextPresentationLines.Add('contract=JNI dimensions -> EGL_Context width/height -> GameLua screenWidth/screenHeight -> full Context viewport')
$contextPresentationLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.17\.0-context-presentation|stage24\.16\.0-live-presentation' -ErrorAction SilentlyContinue)) {
        $contextPresentationLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.17\.0|LIVE EGL Surface ready' -ErrorAction SilentlyContinue)) {
        $contextPresentationLines.Add($m.Line)
    }
}
$contextPresentationLines | Set-Content -Encoding UTF8 $contextPresentation

$presentationLua = Join-Path $out 'stage24.16.0-lua-presentation-contract.txt'
$presentationLuaLines = New-Object System.Collections.Generic.List[string]
$presentationLuaLines.Add('ANGRY_STAGE24_16_0_LUA_PRESENTATION_CONTRACT 1')
$presentationLuaLines.Add('source=untouched loaded 1.4.2 Lua closures before native bindings are replaced')
$presentationLuaLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.16\.0-lua-presentation' -ErrorAction SilentlyContinue)) {
        $presentationLuaLines.Add($m.Line)
    }
}
$presentationLuaLines | Set-Content -Encoding UTF8 $presentationLua


$selectorMatrix = Join-Path $out 'stage24.16.1-selector-matrix.txt'
$selectorMatrixLines = New-Object System.Collections.Generic.List[string]
$selectorMatrixLines.Add('ANGRY_STAGE24_16_1_SELECTOR_MATRIX 1')
$selectorMatrixLines.Add('source=untouched 1.4.2 selectAssetProfile/selectFontProfile closures; screen globals restored after matrix')
$selectorMatrixLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.16\.1-selector-matrix' -ErrorAction SilentlyContinue)) {
        $selectorMatrixLines.Add($m.Line)
    }
}
$selectorMatrixLines | Set-Content -Encoding UTF8 $selectorMatrix

$slingshotLua = Join-Path $out 'stage24.18.1-slingshot-lua-owner.txt'
$slingshotLuaLines = New-Object System.Collections.Generic.List[string]
$slingshotLuaLines.Add('ANGRY_STAGE24_18_1_SLINGSHOT_LUA_OWNER 1')
$slingshotLuaLines.Add('source=untouched 1.4.2 Lua closure tree + exact INGAME_BIRDS_1 SPRT metadata')
$slingshotLuaLines.Add('policy=diagnostic-only; no sling pixels added')
$slingshotLuaLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.18\.1-sling-lua|stage24\.18\.1-sling-assets' -ErrorAction SilentlyContinue)) {
        $slingshotLuaLines.Add($m.Line)
    }
}
$slingshotLuaLines | Set-Content -Encoding UTF8 $slingshotLua


$slingshotRender = Join-Path $out 'stage24.18.2-slingshot-render.txt'
$slingshotRenderLines = New-Object System.Collections.Generic.List[string]
$slingshotRenderLines.Add('ANGRY_STAGE24_18_2_SLINGSHOT_RENDER 1')
$slingshotRenderLines.Add('contract=untouched 1.4.2 drawGame sling layering + exact INGAME_BIRDS_1 sprites + live Lua rubber state')
$slingshotRenderLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.18\.2-sling' -ErrorAction SilentlyContinue)) {
        $slingshotRenderLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.18\.2 slingshot render' -ErrorAction SilentlyContinue)) {
        $slingshotRenderLines.Add($m.Line)
    }
}
$slingshotRenderLines | Set-Content -Encoding UTF8 $slingshotRender

$scoreHudLua = Join-Path $out 'stage24.19.0-gameplay-score-hud-lua-owner.txt'
$scoreHudLuaLines = New-Object System.Collections.Generic.List[string]
$scoreHudLuaLines.Add('ANGRY_STAGE24_19_0_GAMEPLAY_SCORE_HUD_LUA_OWNER 1')
$scoreHudLuaLines.Add('source=untouched 1.4.2 Lua closure tree before native bindings are replaced')
$scoreHudLuaLines.Add('policy=diagnostic-only; score logic remains live; no HUD pixels added')
$scoreHudLuaLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.19\.0-score-hud-lua' -ErrorAction SilentlyContinue)) {
        $scoreHudLuaLines.Add($m.Line)
    }
}
$scoreHudLuaLines | Set-Content -Encoding UTF8 $scoreHudLua

$scoreLedger = Join-Path $out 'stage24.19.1-score-fidelity-ledger.txt'
$scoreLedgerLines = New-Object System.Collections.Generic.List[string]
$scoreLedgerLines.Add('ANGRY_STAGE24_19_1_SCORE_FIDELITY_LEDGER 1')
$scoreLedgerLines.Add('policy=diagnostic-only; no score constants or gameplay values changed')
$scoreLedgerLines.Add('contract=global score is sum(scoreTable[*].score); ledger records every observed bucket delta plus birdCollision-local mutations')
$scoreLedgerLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.19\.1-score-ledger' -ErrorAction SilentlyContinue)) {
        $scoreLedgerLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'LIVE state frame=|LIVE starTable Level1' -ErrorAction SilentlyContinue)) {
        $scoreLedgerLines.Add($m.Line)
    }
}
$scoreLedgerLines | Set-Content -Encoding UTF8 $scoreLedger


$blockScoreShadow = Join-Path $out 'stage24.19.2-block-score-shadow.txt'
$blockScoreShadowLines = New-Object System.Collections.Generic.List[string]
$blockScoreShadowLines.Add('ANGRY_STAGE24_19_2_BLOCK_SCORE_SHADOW 1')
$blockScoreShadowLines.Add('legacy-stage24.19.2 shadow channel; Stage24.19.3 now applies the proven native score path')
$blockScoreShadowLines.Add('arithmetic=per ordinary BeginContact: floor(actualDamageA + actualDamageB) * 10')
$blockScoreShadowLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.19\.2-block-score-shadow' -ErrorAction SilentlyContinue)) {
        $blockScoreShadowLines.Add($m.Line)
    }
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.19\.1-score-contract.*Max score|originalLua Max score' -ErrorAction SilentlyContinue)) {
        $blockScoreShadowLines.Add($m.Line)
    }
}
$blockScoreShadowLines | Set-Content -Encoding UTF8 $blockScoreShadow

$blockScoreRestored = Join-Path $out 'stage24.19.3-block-score-restored.txt'
$blockScoreRestoredLines = New-Object System.Collections.Generic.List[string]
$blockScoreRestoredLines.Add('ANGRY_STAGE24_19_3_BLOCK_SCORE_RESTORED 1')
$blockScoreRestoredLines.Add('contract=untouched ARMv7 GameLua::BeginContact scoreTable.blocks.score += floor(actualDamageA + actualDamageB) * 10')
$blockScoreRestoredLines.Add('ordering=capture blocks.score before blockCollision; write captured + native delta after callback')
$blockScoreRestoredLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.19\.3-block-score-restored' -ErrorAction SilentlyContinue)) {
        $blockScoreRestoredLines.Add($m.Line)
    }
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.19\.1-score-contract.*Max score|originalLua Max score' -ErrorAction SilentlyContinue)) {
        $blockScoreRestoredLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'LIVE state frame=|LIVE starTable Level1' -ErrorAction SilentlyContinue)) {
        $blockScoreRestoredLines.Add($m.Line)
    }
}
$blockScoreRestoredLines | Set-Content -Encoding UTF8 $blockScoreRestored

$scoreHudRuntime = Join-Path $out 'stage24.20.0-gameplay-score-hud.txt'
$scoreHudRuntimeLines = New-Object System.Collections.Generic.List[string]
$scoreHudRuntimeLines.Add('ANGRY_STAGE24_20_0_GAMEPLAY_SCORE_HUD 1')
$scoreHudRuntimeLines.Add('contract=untouched drawGame fixed HUD: fontBasic + localized MI_SCORE/MI_HIGH_SCORE + RIGHT/TOP + screenWidth-3 + oldScoreLen')
$scoreHudRuntimeLines.Add('note=FONT_SCORE remains reserved for the separate floatingScores path after the fixed HUD')
$scoreHudRuntimeLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.20\.0-score-hud' -ErrorAction SilentlyContinue)) {
        $scoreHudRuntimeLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.20\.0 gameplay score HUD' -ErrorAction SilentlyContinue)) {
        $scoreHudRuntimeLines.Add($m.Line)
    }
}
$scoreHudRuntimeLines | Set-Content -Encoding UTF8 $scoreHudRuntime

$debugDisplay = Join-Path $out 'stage24.20.1-debug-display.txt'
$debugDisplayLines = New-Object System.Collections.Generic.List[string]
$debugDisplayLines.Add('ANGRY_STAGE24_20_1_DEBUG_DISPLAY 1')
$debugDisplayLines.Add('policy=testing harness only; wvga854 deliberately overrides logical Context while native mode preserves recovered 1.4.2 behavior')
$debugDisplayLines.Add('expected-default=logical 854x480; uniform centered viewport; black harness matte; touch mapped Surface->logical')
$debugDisplayLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.20\.1-debug-display' -ErrorAction SilentlyContinue)) {
        $debugDisplayLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.20\.1 debug display|Stage24\.20\.1 Debug/Lua invariant|TOUCH (DOWN|UP).*wvga854-debug' -ErrorAction SilentlyContinue)) {
        $debugDisplayLines.Add($m.Line)
    }
}
$debugDisplayLines | Set-Content -Encoding UTF8 $debugDisplay

$floatingScores = Join-Path $out 'stage24.21.0-floating-scores.txt'
$floatingScoreLines = New-Object System.Collections.Generic.List[string]
$floatingScoreLines.Add('ANGRY_STAGE24_21_0_FLOATING_SCORES 1')
$floatingScoreLines.Add('contract=untouched drawGame pc0558..0629: FONT_SCORE + floatingScores + physicsToWorldTransform + per-entry xs + BOTTOM/HCENTER')
$floatingScoreLines.Add('animation=untouched updateFloatingScores owns grow/hold/shrink and lifetime removal')
$floatingScoreLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.21\.0-floating-score' -ErrorAction SilentlyContinue)) {
        $floatingScoreLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.21\.0 floating scores' -ErrorAction SilentlyContinue)) {
        $floatingScoreLines.Add($m.Line)
    }
}
$floatingScoreLines | Set-Content -Encoding UTF8 $floatingScores

$failureContract = Join-Path $out 'stage24.22.0-level-failed-contract.txt'
$failureContractLines = New-Object System.Collections.Generic.List[string]
$failureContractLines.Add('ANGRY_STAGE24_22_0_LEVEL_FAILED_CONTRACT 1')
$failureContractLines.Add('policy=diagnostic-only; no failed state/menu synthesized')
$failureContractLines.Add('goal=compare untouched checkLevelFailed/initLevelFailed bytecode with live Level57 terminal-candidate inputs')
$failureContractLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.22\.0-failure-lua|stage24\.22\.0-failure-runtime' -ErrorAction SilentlyContinue)) {
        $failureContractLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.22\.0 failure candidate|LIVE state frame=|LIVE game mode' -ErrorAction SilentlyContinue)) {
        $failureContractLines.Add($m.Line)
    }
}
$failureContractLines | Set-Content -Encoding UTF8 $failureContract

$birdsLifecycle = Join-Path $out 'stage24.22.1-birds-controllable-lifecycle.txt'
$birdsLifecycleLines = New-Object System.Collections.Generic.List[string]
$birdsLifecycleLines.Add('ANGRY_STAGE24_22_1_BIRDS_CONTROLLABLE_LIFECYCLE 1')
$birdsLifecycleLines.Add('policy=diagnostic-only; inspect exact birds table consumed by checkLevelFailed')
$birdsLifecycleLines.Add('expected predicate: fail only when !hasMovingObjects (or doNotWait) and no birds[*].controllable')
$birdsLifecycleLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.22\.1-birds-runtime|stage24\.22\.1-birds-summary|stage24\.22\.0-failure-lua.*(getNextBird|fillInNextBird|updateGame)' -ErrorAction SilentlyContinue)) {
        $birdsLifecycleLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.22\.0 failure candidate|LIVE state frame=|LIVE motion gates frame=' -ErrorAction SilentlyContinue)) {
        $birdsLifecycleLines.Add($m.Line)
    }
}
$birdsLifecycleLines | Set-Content -Encoding UTF8 $birdsLifecycle

$birdSettle = Join-Path $out 'stage24.22.2-bird-removal-settle.txt'
$birdSettleLines = New-Object System.Collections.Generic.List[string]
$birdSettleLines.Add('ANGRY_STAGE24_22_2_BIRD_REMOVAL_SETTLE 1')
$birdSettleLines.Add('policy=diagnostic-only; no velocity/timer/sleep/controllable mutation')
$birdSettleLines.Add('goal=prove which exact updateGame removeBird gate keeps shot birds alive')
$birdSettleLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.22\.2-bird-settle|stage24\.22\.2-ground-settle|stage24\.22\.0-failure-lua.*removeBird|stage24\.22\.0-failure-lua.*updateGame pc=32(9[0-9]|[0-9]{2})' -ErrorAction SilentlyContinue)) {
        $birdSettleLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.22\.0 failure candidate|LIVE state frame=|LIVE motion gates frame=' -ErrorAction SilentlyContinue)) {
        $birdSettleLines.Add($m.Line)
    }
}
$birdSettleLines | Set-Content -Encoding UTF8 $birdSettle

$rovioPhysicsRuntime = Join-Path $out 'stage24.22.8-rovio-box2d-runtime.txt'
$rovioPhysicsRuntimeLines = New-Object System.Collections.Generic.List[string]
$rovioPhysicsRuntimeLines.Add('ANGRY_STAGE24_22_8_ROVIO_BOX2D_RUNTIME 1')
$rovioPhysicsRuntimeLines.Add('expected=linearSlop 0.05; polygonRadius 0.1; timeToSleep 0.25; linearSleepTolerance 0.1; velocityThreshold/maxLinearCorrection/contactBaumgarte stock')
$rovioPhysicsRuntimeLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.22\.8-rovio-physics' -ErrorAction SilentlyContinue)) {
        $rovioPhysicsRuntimeLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.22\.8 Rovio Box2D tolerances' -ErrorAction SilentlyContinue)) {
        $rovioPhysicsRuntimeLines.Add($m.Line)
    }
}
$rovioPhysicsRuntimeLines | Set-Content -Encoding UTF8 $rovioPhysicsRuntime

$terminalMenuRuntime = Join-Path $out 'stage24.22.9-terminal-menu.txt'
$terminalMenuRuntimeLines = New-Object System.Collections.Generic.List[string]
$terminalMenuRuntimeLines.Add('ANGRY_STAGE24_22_9_TERMINAL_MENU 1')
$terminalMenuRuntimeLines.Add('source=untouched original drawMenu; visible gate admits levelComplete and levelFailed')
$terminalMenuRuntimeLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.22\.9-terminal-menu|stage24\.13\.4-anim' -ErrorAction SilentlyContinue)) {
        $terminalMenuRuntimeLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.22\.9 terminal menu|LIVE game mode frame=.*updateMenu|Stage24\.22\.0 failure candidate.*levelFailed' -ErrorAction SilentlyContinue)) {
        $terminalMenuRuntimeLines.Add($m.Line)
    }
}
$terminalMenuRuntimeLines | Set-Content -Encoding UTF8 $terminalMenuRuntime

$hudRemainder = Join-Path $out 'stage24.23.0-gameplay-hud-remainder-contract.txt'
$hudRemainderLines = New-Object System.Collections.Generic.List[string]
$hudRemainderLines.Add('ANGRY_STAGE24_23_0_GAMEPLAY_HUD_REMAINDER_CONTRACT 1')
$hudRemainderLines.Add('source=untouched drawGame + initializeMenu/createMenuPages/prepareMenuPage/updateGame; diagnostic-only')
$hudRemainderLines.Add('goal=recover remaining fixed gameplay HUD, especially pause/menu button, without guessed sprite/geometry/hitbox')
$hudRemainderLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.23\.0-hud-lua|stage24\.23\.0-hud-owner|stage24\.23\.0-hud-bytecode|stage24\.23\.0-hud-sprites|stage24\.23\.0-hud-runtime' -ErrorAction SilentlyContinue)) {
        $hudRemainderLines.Add($m.Line)
    }
}
$hudRemainderLines | Set-Content -Encoding UTF8 $hudRemainder

$gameplayHudRuntime = Join-Path $out 'stage24.23.1-gameplay-hud.txt'
$gameplayHudRuntimeLines = New-Object System.Collections.Generic.List[string]
$gameplayHudRuntimeLines.Add('ANGRY_STAGE24_23_1_GAMEPLAY_HUD 1')
$gameplayHudRuntimeLines.Add('source=untouched drawGame pc0223..0268 HUD_ARROW_UP + pc0630..0671 MENU_BUTTON; input remains untouched updateGame pc0471..0495')
$gameplayHudRuntimeLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.23\.1-gameplay-hud' -ErrorAction SilentlyContinue)) {
        $gameplayHudRuntimeLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.23\.1 gameplay HUD' -ErrorAction SilentlyContinue)) {
        $gameplayHudRuntimeLines.Add($m.Line)
    }
}
$gameplayHudRuntimeLines | Set-Content -Encoding UTF8 $gameplayHudRuntime

$pauseMenuRuntime = Join-Path $out 'stage24.23.2-pause-menu.txt'
$pauseMenuRuntimeLines = New-Object System.Collections.Generic.List[string]
$pauseMenuRuntimeLines.Add('ANGRY_STAGE24_23_2_PAUSE_MENU 1')
$pauseMenuRuntimeLines.Add('source=original createMenuPages hitbox + untouched updateGame goToMenu + untouched drawMenu pause page')
$pauseMenuRuntimeLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.23\.2-pause-menu|stage24\.23\.1-gameplay-hud' -ErrorAction SilentlyContinue)) {
        $pauseMenuRuntimeLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.23\.2 pause menu|LIVE game mode frame=.*updateMenu|TOUCH (DOWN|UP).*profile=game-wvga854-debug' -ErrorAction SilentlyContinue)) {
        $pauseMenuRuntimeLines.Add($m.Line)
    }
}
$pauseMenuRuntimeLines | Set-Content -Encoding UTF8 $pauseMenuRuntime

$pauseAudioAudit = Join-Path $out 'stage24.23.4-pause-audio-contract.txt'
$pauseAudioAuditLines = New-Object System.Collections.Generic.List[string]
$pauseAudioAuditLines.Add('ANGRY_STAGE24_23_4_PAUSE_AUDIO_CONTRACT 1')
$pauseAudioAuditLines.Add('source=untouched pause Lua owners + original ARMv7 LuaResources volume methods; diagnostic-only')
$pauseAudioAuditLines.Add('repro=resume selects hidePauseMenu then returns to updateMenu next frame; SFX reaches missing res.getTrackVolume')
$pauseAudioAuditLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.23\.4-pause-lua|stage24\.23\.4-pause-audio|stage24\.23\.0-hud-bytecode.*(goToMenu|showPauseMenu|hidePauseMenu|gameResumed|updateMenu|drawMenu|setGameMode)|stage24\.12\.9-menu-audit.*(hidePauseMenu|updateLoading)|ORIGINAL update\(\) FAIL.*getTrackVolume' -ErrorAction SilentlyContinue)) {
        $pauseAudioAuditLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'LIVE game mode frame=.*(showPauseMenu|hidePauseMenu|updateMenu|updateGame|updateLoading)|getTrackVolume' -ErrorAction SilentlyContinue)) {
        $pauseAudioAuditLines.Add($m.Line)
    }
}
$nativePauseAudio = Join-Path $out 'stage24.23.4-pause-audio-native-contract.txt'
if (Test-Path $nativePauseAudio) {
    $pauseAudioAuditLines.Add('')
    $pauseAudioAuditLines.Add('--- static ARMv7 pause/audio contract ---')
    foreach ($line in @(Get-Content $nativePauseAudio -ErrorAction SilentlyContinue)) { $pauseAudioAuditLines.Add($line) }
}
$pauseAudioAuditLines | Set-Content -Encoding UTF8 $pauseAudioAudit

$pauseResumeRuntime = Join-Path $out 'stage24.23.5-pause-resume-lifecycle.txt'
$pauseResumeRuntimeLines = New-Object System.Collections.Generic.List[string]
$pauseResumeRuntimeLines.Add('ANGRY_STAGE24_23_5_PAUSE_RESUME_LIFECYCLE 1')
$pauseResumeRuntimeLines.Add('source=untouched setAnimationState + updateAnimations + hidePauseMenu; no synthetic resume transition')
$pauseResumeRuntimeLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.23\.5-pause-resume|LIVE game mode frame=.*(showPauseMenu|hidePauseMenu|updateMenu|updateGame)|\[GameLua/Box2D\] setPhysicsEnabled' -ErrorAction SilentlyContinue)) {
        $pauseResumeRuntimeLines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.23\.5 original animation closures|LIVE game mode frame=.*(showPauseMenu|hidePauseMenu|updateMenu|updateGame)' -ErrorAction SilentlyContinue)) {
        $pauseResumeRuntimeLines.Add($m.Line)
    }
}
$pauseResumeRuntimeLines | Set-Content -Encoding UTF8 $pauseResumeRuntime

$particleContract = Join-Path $out 'stage24.24.0-particle-contract.txt'
$particleContractLines = New-Object System.Collections.Generic.List[string]
$particleContractLines.Add('ANGRY_STAGE24_24_0_PARTICLE_CONTRACT 1')
$particleContractLines.Add('source=untouched particles.lua + gamelogic.lua definitions/producers + original ARMv7 Particles wrapper; diagnostic-only')
$particleContractLines.Add('runtime particles.addParticles remains headless in this stage')
$particleContractLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.24\.0-particle|stage16-particles.*(definitions|addParticles)' -ErrorAction SilentlyContinue)) {
        $particleContractLines.Add($m.Line)
    }
}
$nativeParticle = Join-Path $out 'stage24.24.0-particle-native-contract.txt'
if (Test-Path $nativeParticle) {
    $particleContractLines.Add('')
    $particleContractLines.Add('--- static ARMv7 particle contract ---')
    foreach ($line in @(Get-Content $nativeParticle -ErrorAction SilentlyContinue)) { $particleContractLines.Add($line) }
}
$particleContractLines | Set-Content -Encoding UTF8 $particleContract

$particleRuntime241 = Join-Path $out 'stage24.24.1-particle-runtime.txt'
$particleRuntime241Lines = New-Object System.Collections.Generic.List[string]
$particleRuntime241Lines.Add('ANGRY_STAGE24_24_1_PARTICLE_RUNTIME 1')
$particleRuntime241Lines.Add('signature=type,count,x,y,width,height,angle,bypassLimits; runtime boundary remains headless')
$particleRuntime241Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.24\.1-particle-spawn' -ErrorAction SilentlyContinue)) {
        $particleRuntime241Lines.Add($m.Line)
    }
}
$particleRuntime241Lines | Set-Content -Encoding UTF8 $particleRuntime241

$particleVisible242 = Join-Path $out 'stage24.24.2-visible-particles.txt'
$particleVisible242Lines = New-Object System.Collections.Generic.List[string]
$particleVisible242Lines.Add('ANGRY_STAGE24_24_2_VISIBLE_PARTICLES 1')
$particleVisible242Lines.Add('runtime=original particles.lua definitions + recovered ARMv7 custom Particles add/update/draw contract')
$particleVisible242Lines.Add('drawOrder=after native object passes, before foreground')
$particleVisible242Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.24\.2-particle-(spawn|draw)|stage24\.24\.2-particles' -ErrorAction SilentlyContinue)) {
        $particleVisible242Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.24\.2-particles' -ErrorAction SilentlyContinue)) {
        $particleVisible242Lines.Add($m.Line)
    }
}
$particleVisible242Lines | Set-Content -Encoding UTF8 $particleVisible242


$audioLua250 = Join-Path $out 'stage24.25.0-audio-lua-contract.txt'
$audioLua250Lines = New-Object System.Collections.Generic.List[string]
$audioLua250Lines.Add('ANGRY_STAGE24_25_0_AUDIO_LUA_CONTRACT 1')
$audioLua250Lines.Add('policy=diagnostic-only; playback remains headless')
$audioLua250Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.0-audio' -ErrorAction SilentlyContinue)) {
        $audioLua250Lines.Add($m.Line)
    }
}
$audioLua250Lines | Set-Content -Encoding UTF8 $audioLua250

$audioRuntime251 = Join-Path $out 'stage24.25.1-audio-runtime-probe.txt'
$audioRuntime251Lines = New-Object System.Collections.Generic.List[string]
$audioRuntime251Lines.Add('ANGRY_STAGE24_25_1_AUDIO_RUNTIME_PROBE 1')
$audioRuntime251Lines.Add('policy=diagnostic-only; playAudio returns original missing-clip sentinel -1; no playback yet')
$audioRuntime251Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.1-audio-(probe|state)' -ErrorAction SilentlyContinue)) {
        $audioRuntime251Lines.Add($m.Line)
    }
}
$audioRuntime251Lines | Set-Content -Encoding UTF8 $audioRuntime251

$audioPlayback252 = Join-Path $out 'stage24.25.2-audio-playback.txt'
$audioPlayback252Lines = New-Object System.Collections.Generic.List[string]
$audioPlayback252Lines.Add('ANGRY_STAGE24_25_2_ORIGINAL_WAV_SFX_PLAYBACK 1')
$audioPlayback252Lines.Add('scope=untouched createAssets audio registration/audioGroups + proven PCM WAV contract + OpenSL software mixer')
$audioPlayback252Lines.Add('historicalGap=Stage24.25.2 lacked MP3; Stage24.25.7 may now satisfy MP3 aliases through the proven mixer/loop contract')
$audioPlayback252Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.2-audio-(register|backend|play|volume|summary)' -ErrorAction SilentlyContinue)) {
        $audioPlayback252Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.25\.2-audio|Stage24\.25\.2' -ErrorAction SilentlyContinue)) {
        $audioPlayback252Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.25\.2-audio' -ErrorAction SilentlyContinue)) {
        $audioPlayback252Lines.Add($m.Line)
    }
}
$audioPlayback252Lines | Set-Content -Encoding UTF8 $audioPlayback252

$audioOutput253 = Join-Path $out 'stage24.25.3-audio-output-callback.txt'
$audioOutput253Lines = New-Object System.Collections.Generic.List[string]
$audioOutput253Lines.Add('ANGRY_STAGE24_25_3_AUDIO_OUTPUT_CALLBACK_AUDIT 1')
$audioOutput253Lines.Add('policy=diagnostic-only; Stage24.25.2 playback semantics unchanged; measures decoded PCM peak, primed buffers, OpenSL play/queue state, callback cadence, and callback PCM peaks')
$audioOutput253Lines.Add('decision=clipPeak>0 + prime/callback peak>0 + OpenSL PLAYING isolates failure below mixer; callbackCalls=0 isolates buffer-queue lifecycle')
$audioOutput253Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.3-audio-output' -ErrorAction SilentlyContinue)) {
        $audioOutput253Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.25\.3-audio-output|Stage24\.25\.3' -ErrorAction SilentlyContinue)) {
        $audioOutput253Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.25\.3-audio-output' -ErrorAction SilentlyContinue)) {
        $audioOutput253Lines.Add($m.Line)
    }
}
$audioOutput253Lines | Set-Content -Encoding UTF8 $audioOutput253

$audioFidelity254Runtime = Join-Path $out 'stage24.25.4-audio-fidelity-runtime.txt'
$audioFidelity254Lines = New-Object System.Collections.Generic.List[string]
$audioFidelity254Lines.Add('ANGRY_STAGE24_25_4_AUDIO_FIDELITY_RUNTIME 1')
$audioFidelity254Lines.Add('policy=audit-first; raw Lua track-volume requests are logged separately from the proven ARMv7 native-stored clamp [0,1]')
$audioFidelity254Lines.Add('history=Stage24.25.4 audited MP3 while unsupported; Stage24.25.7 adds a compatibility decoder after Stage24.25.6 closed EOF/loop ownership')
$audioFidelity254Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.4-audio|stage24\.25\.4-track-volume|stage24\.25\.2-audio-play.*(ambient_theme|title_theme|level start|level clear|level failed)|stage24\.25\.2-audio-volume' -ErrorAction SilentlyContinue)) {
        $audioFidelity254Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.25\.4|LIVE game mode|WVGA854 touch' -ErrorAction SilentlyContinue)) {
        $audioFidelity254Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.25\.4|stage24\.25\.2-audio' -ErrorAction SilentlyContinue)) {
        $audioFidelity254Lines.Add($m.Line)
    }
}
$audioFidelity254Lines | Set-Content -Encoding UTF8 $audioFidelity254Runtime

$audioRampOwner255 = Join-Path $out 'stage24.25.5-audio-ramp-owner.txt'
$audioRampOwner255Lines = New-Object System.Collections.Generic.List[string]
$audioRampOwner255Lines.Add('ANGRY_STAGE24_25_5_AUDIO_RAMP_OWNER_RUNTIME 1')
$audioRampOwner255Lines.Add('policy=read-only VM hook + untouched Lua Proto ownership; track-volume clamp remains the proven ARMv7 [0,1] behavior from Stage24.25.4')
$audioRampOwner255Lines.Add('question=identify every SETGLOBAL writer/initializer/clear of audioRampVolume and audioRampLength and correlate runtime writes with mode/page')
$audioRampOwner255Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.5-audio-ramp-(owner|write)|stage24\.25\.4-track-volume.*clamped=yes' -ErrorAction SilentlyContinue)) {
        $audioRampOwner255Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'LIVE game mode|LIVE update mode|Stage24\.25\.5|WVGA854 touch' -ErrorAction SilentlyContinue)) {
        $audioRampOwner255Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.25\.5|stage24\.25\.4' -ErrorAction SilentlyContinue)) {
        $audioRampOwner255Lines.Add($m.Line)
    }
}
$audioRampOwner255Lines | Set-Content -Encoding UTF8 $audioRampOwner255


$audioMp3257 = Join-Path $out 'stage24.25.7-mp3-playback.txt'
$audioMp3257Lines = New-Object System.Collections.Generic.List[string]
$audioMp3257Lines.Add('ANGRY_STAGE24_25_7_ORIGINAL_MP3_MUSIC_PLAYBACK 1')
$audioMp3257Lines.Add('ownership=untouched Lua createAudio/audioGroups/playAudio + Stage24.25.6 proven AudioClipInstance EOF/loop semantics')
$audioMp3257Lines.Add('decoder=Android MediaExtractor/MediaCodec compatibility decode to signed PCM; decoded PCM rejoins the same OpenSL software mixer used by WAV')
$audioMp3257Lines.Add('expected=first requested MP3 lazily decodes once; loop=true rewinds PCM cursor at EOF; track/master clamp and numeric handle semantics unchanged')
$audioMp3257Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.7-mp3-(register|decode|play)|stage24\.25\.2-audio-(register|summary)|stage24\.25\.2-audio-play.*kind=mp3' -ErrorAction SilentlyContinue)) {
        $audioMp3257Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.25\.7-mp3|Stage24\.25\.7' -ErrorAction SilentlyContinue)) {
        $audioMp3257Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.25\.7-mp3|MediaCodec|MediaExtractor' -ErrorAction SilentlyContinue)) {
        $audioMp3257Lines.Add($m.Line)
    }
}
$audioMp3257Lines | Set-Content -Encoding UTF8 $audioMp3257

$audioClosure258Runtime = Join-Path $out 'stage24.25.8-audio-closure-runtime.txt'
$audioClosure258Lines = New-Object System.Collections.Generic.List[string]
$audioClosure258Lines.Add('ANGRY_STAGE24_25_8_AUDIO_CLOSURE_RUNTIME 1')
$audioClosure258Lines.Add('policy=diagnostic-only; no intended playback semantics changed from Stage24.25.7')
$audioClosure258Lines.Add('targets=real voice EOF/END, loop wrap, query/stop ownership, output start/stop state, complete audioGroups provenance, ground_collision missing-resource behavior')
$audioClosure258Lines.Add('decisiveLoopEvidence=ambient_theme1 must emit LOOP_WRAP after its first decoded ~27.75 s cursor reaches EOF')
$audioClosure258Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.25\.8-(audio-lifecycle|output-lifecycle|ground-collision|audio-groups|audio-summary)|stage24\.25\.7-mp3-(decode|play)|stage24\.25\.2-audio-play.*ground_collision|stage24\.25\.3-audio-output.*(ambient_theme1|CALLBACK)' -ErrorAction SilentlyContinue)) {
        $audioClosure258Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.25\.8|Stage24\.25\.8' -ErrorAction SilentlyContinue)) {
        $audioClosure258Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.25\.8|stage24\.25\.7|MediaCodec|OpenSL' -ErrorAction SilentlyContinue)) {
        $audioClosure258Lines.Add($m.Line)
    }
}
$audioClosure258Lines | Set-Content -Encoding UTF8 $audioClosure258Runtime

$trajectoryLua260 = Join-Path $out 'stage24.26.0-trajectory-lua-contract.txt'
$trajectoryLua260Lines = New-Object System.Collections.Generic.List[string]
$trajectoryLua260Lines.Add('ANGRY_STAGE24_26_0_TRAJECTORY_LUA_CONTRACT 1')
$trajectoryLua260Lines.Add('policy=diagnostic-only; untouched loaded Lua Proto trees are inspected before the three trajectory bindings are replaced by headless probes')
$trajectoryLua260Lines.Add('targets=startNewTrajectory/addToTrajectory/addPuffToTrajectory plus recordTrajectory/birdTrajectory/allowTrajectoryClearing ownership windows')
$trajectoryLua260Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.26\.0-trajectory-(lua|bytecode|state)' -ErrorAction SilentlyContinue)) {
        $trajectoryLua260Lines.Add($m.Line)
    }
}
$trajectoryLua260Lines | Set-Content -Encoding UTF8 $trajectoryLua260

$trajectoryRuntime260 = Join-Path $out 'stage24.26.0-trajectory-runtime.txt'
$trajectoryRuntime260Lines = New-Object System.Collections.Generic.List[string]
$trajectoryRuntime260Lines.Add('ANGRY_STAGE24_26_0_TRAJECTORY_RUNTIME 1')
$trajectoryRuntime260Lines.Add('policy=Stage24.26.0 producer telemetry retained; Stage24.26.2 now backs the recovered calls with original two-bank native storage and visible rendering')
$trajectoryRuntime260Lines.Add('expected=normal 1-1 Red launch should produce ADD calls and a later START lifecycle boundary; PUFF may remain absent on this path')
$trajectoryRuntime260Lines.Add('fields=raw arg1/x/y, deltas/distance, generation/counters, untouched Lua state, callsite+pc')
$trajectoryRuntime260Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.26\.0-trajectory-(runtime|summary|state)|stage24\.18\.2-sling|stage16-native|stage11-contact|stage16-callback' -ErrorAction SilentlyContinue)) {
        $trajectoryRuntime260Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'Stage24\.26\.0|trajectory' -ErrorAction SilentlyContinue)) {
        $trajectoryRuntime260Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.26\.0|trajectory|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $trajectoryRuntime260Lines.Add($m.Line)
    }
}
$trajectoryRuntime260Lines | Set-Content -Encoding UTF8 $trajectoryRuntime260

$trajectoryPuffLua261 = Join-Path $out 'stage24.26.1-trajectory-puff-lua.txt'
$trajectoryPuffLua261Lines = New-Object System.Collections.Generic.List[string]
$trajectoryPuffLua261Lines.Add('ANGRY_STAGE24_26_1_TRAJECTORY_PUFF_LUA 1')
$trajectoryPuffLua261Lines.Add('policy=diagnostic-only; untouched updateGame bytecode and RK constants around every addPuffToTrajectory producer')
$trajectoryPuffLua261Lines.Add('goal=resolve exact birdSpecialty branches and producer-side semantics without requiring a puff bird in this run')
$trajectoryPuffLua261Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.26\.1-puff-(lua|bytecode|constant)' -ErrorAction SilentlyContinue)) {
        $trajectoryPuffLua261Lines.Add($m.Line)
    }
}
$trajectoryPuffLua261Lines | Set-Content -Encoding UTF8 $trajectoryPuffLua261

$trajectoryPuffRuntime261 = Join-Path $out 'stage24.26.1-trajectory-puff-runtime.txt'
$trajectoryPuffRuntime261Lines = New-Object System.Collections.Generic.List[string]
$trajectoryPuffRuntime261Lines.Add('ANGRY_STAGE24_26_1_TRAJECTORY_PUFF_RUNTIME 1')
$trajectoryPuffRuntime261Lines.Add('policy=Stage24.26.1 producer telemetry retained; Stage24.26.2 stores/renders PUFF points; calls remain optional in the standard Red 1-1 validation path')
$trajectoryPuffRuntime261Lines.Add('fields=birdSpecialty/flyingBird name+definition+sprite/callsite+pc when addPuffToTrajectory is actually exercised')
$trajectoryPuffRuntime261Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.26\.1-puff-runtime|stage24\.26\.0-trajectory-runtime.*PUFF' -ErrorAction SilentlyContinue)) {
        $trajectoryPuffRuntime261Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.26\.1|trajectory|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $trajectoryPuffRuntime261Lines.Add($m.Line)
    }
}
$trajectoryPuffRuntime261Lines | Set-Content -Encoding UTF8 $trajectoryPuffRuntime261

$trajectoryRuntime262 = Join-Path $out 'stage24.26.2-trajectory-renderer-runtime.txt'
$trajectoryRuntime262Lines = New-Object System.Collections.Generic.List[string]
$trajectoryRuntime262Lines.Add('ANGRY_STAGE24_26_2_TRAJECTORY_RENDERER_RUNTIME 1')
$trajectoryRuntime262Lines.Add('contract=original two-bank x three-slot storage; normal TRAIL_WHITE_1/2/3 modulo-3; puff BIRD_SPECIAL; render after native pass1 before pass2')
$trajectoryRuntime262Lines.Add('test=launch two Reds in Level 1-1 when practical; previous bank may coexist while current bank receives the second trajectory; PUFF is optional on Red')
$trajectoryRuntime262Lines.Add('physics=UNCHANGED; bird settle/angular sleep/remove/level-end behavior is not patched by Stage24.26.2')
$trajectoryRuntime262Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.26\.2-trajectory-(render|native)|stage24\.26\.0-trajectory-(runtime|summary)' -ErrorAction SilentlyContinue)) {
        $trajectoryRuntime262Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.26\.2|trajectory|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $trajectoryRuntime262Lines.Add($m.Line)
    }
}
$trajectoryRuntime262Lines | Set-Content -Encoding UTF8 $trajectoryRuntime262

# Stage 24.27.0: focused bird-rest/angular/removal/end-state evidence.
$birdRestLua270 = Join-Path $out 'stage24.27.0-bird-rest-lua-contract.txt'
$birdRestLua270Lines = New-Object System.Collections.Generic.List[string]
$birdRestLua270Lines.Add('ANGRY_STAGE24_27_0_BIRD_REST_LUA_CONTRACT 1')
$birdRestLua270Lines.Add('policy=diagnostic-only; targeted untouched Lua closure windows around removeBird, speed/timer, camera, moving-object and terminal gates')
$birdRestLua270Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.27\.0-rest-lua' -ErrorAction SilentlyContinue)) {
        $birdRestLua270Lines.Add($m.Line)
    }
}
$birdRestLua270Lines | Set-Content -Encoding UTF8 $birdRestLua270

$birdRestRuntime270 = Join-Path $out 'stage24.27.0-bird-rest-runtime.txt'
$birdRestRuntime270Lines = New-Object System.Collections.Generic.List[string]
$birdRestRuntime270Lines.Add('ANGRY_STAGE24_27_0_BIRD_REST_RUNTIME 1')
$birdRestRuntime270Lines.Add('policy=diagnostic-only; physics and Lua lifecycle are unchanged')
$birdRestRuntime270Lines.Add('sampling=shot birds ~10Hz plus immediate awake/contact/remove-threshold/timer-sign transitions')
$birdRestRuntime270Lines.Add('effectiveThresholds=Lua remove speed<0.05; Rovio linear sleep tolerance=0.10; angular sleep tolerance=0.034906588 rad/s; timeToSleep=0.25s (private m_sleepTime is not read or mutated; observed consecutive-below-threshold durations are reported instead)')
$birdRestRuntime270Lines.Add('test=one Red slow-settle/tumble repro; after it looks almost stopped, touch nothing for >=15s; level completion is unnecessary')
$birdRestRuntime270Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.27\.0-bird-rest|stage24\.22\.2-bird-settle|stage21-lifecycle' -ErrorAction SilentlyContinue)) {
        $birdRestRuntime270Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.27\.0|Box2D|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $birdRestRuntime270Lines.Add($m.Line)
    }
}
$birdRestRuntime270Lines | Set-Content -Encoding UTF8 $birdRestRuntime270


# Stage 24.28.0: giant menu/UI inventory from the untouched initializeMenu
# state plus actual navigation transitions observed during the live run.
$menuUiRuntime280 = Join-Path $out 'stage24.28.0-menu-ui-runtime-inventory.txt'
$menuUiRuntime280Lines = New-Object System.Collections.Generic.List[string]
$menuUiRuntime280Lines.Add('ANGRY_STAGE24_28_0_MENU_UI_RUNTIME_INVENTORY 1')
$menuUiRuntime280Lines.Add('policy=diagnostic-only; inventory captured after untouched original initializeMenu and before direct Level1 harness forcing')
$menuUiRuntime280Lines.Add('scope=global menu/page/settings tables; nested items/callbacks; relevant global+child Lua proto string constants; platform frontier globals')
$menuUiRuntime280Lines.Add('level1Film=inventory-only; playVideo/cutscene ownership is audited but not implemented here')
$menuUiRuntime280Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.0-menu-(inventory|table|proto|global)' -ErrorAction SilentlyContinue)) {
        $menuUiRuntime280Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.0|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $menuUiRuntime280Lines.Add($m.Line)
    }
}
$menuUiRuntime280Lines | Set-Content -Encoding UTF8 $menuUiRuntime280

$navigationRuntime280 = Join-Path $out 'stage24.28.0-navigation-runtime.txt'
$navigationRuntime280Lines = New-Object System.Collections.Generic.List[string]
$navigationRuntime280Lines.Add('ANGRY_STAGE24_28_0_NAVIGATION_RUNTIME 1')
$navigationRuntime280Lines.Add('policy=read-only transition observer; currentGameMode/current+old+new menu pages/popups/loadLevelDelayed/platform flags')
$navigationRuntime280Lines.Add('test=boot Level1; exercise Pause and one terminal flow when convenient; click result buttons that are reachable; not every screen must be visited because the full table inventory is separate')
$navigationRuntime280Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.0-navigation-runtime|stage24\.12\.9-menu-audit|stage24\.23\.2-pause-menu|stage24\.22\.9-terminal-menu|\[GameLua stub\] (playVideo|saveLuaFile|unlockAchievement|showAchievements|showLeaderboards|activateCrystalUI|deactivateCrystalUI|showAdvertisement|hideAdvertisement|showVideoAdvertisement|requestVideoAd|requestAndShowVideo|requestAd)' -ErrorAction SilentlyContinue)) {
        $navigationRuntime280Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.0|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $navigationRuntime280Lines.Add($m.Line)
    }
}
$navigationRuntime280Lines | Set-Content -Encoding UTF8 $navigationRuntime280

# Stage 24.28.1: every original updateMenu/currentMenuPage is now passed to the
# already-proven untouched drawMenu renderer. Keep this report compact so a
# visual failure can be tied to the exact page and first missing primitive.
$visibleMenu281 = Join-Path $out 'stage24.28.1-visible-menu-runtime.txt'
$visibleMenu281Lines = New-Object System.Collections.Generic.List[string]
$visibleMenu281Lines.Add('ANGRY_STAGE24_28_1_VISIBLE_MENU_RUNTIME 1')
$visibleMenu281Lines.Add('policy=original Lua pages/callbacks/navigation; renderer allow-list lifted from pause+terminal to any updateMenu/currentMenuPage')
$visibleMenu281Lines.Add('test=finish/fail 1-1 -> Menu/Home -> inspect Level Selection -> use Back/Home/Play to reach Episode Selection/Main Menu when available')
$visibleMenu281Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.1-visible-menu|stage24\.13\.2-menu|stage24\.13\.4-anim|stage24\.28\.0-navigation-runtime|stage24\.22\.9-terminal-menu|stage24\.23\.2-pause-menu' -ErrorAction SilentlyContinue)) {
        $visibleMenu281Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.1|stage24\.13\.2-menu|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $visibleMenu281Lines.Add($m.Line)
    }
}
$visibleMenu281Lines | Set-Content -Encoding UTF8 $visibleMenu281

$startupLua281 = Join-Path $out 'stage24.28.1-startup-branding-lua-contract.txt'
$startupLua281Lines = New-Object System.Collections.Generic.List[string]
$startupLua281Lines.Add('ANGRY_STAGE24_28_1_STARTUP_BRANDING_LUA_CONTRACT 1')
$startupLua281Lines.Add('policy=diagnostic-only; Stage24 still boots directly into Level1; do not infer splash duration/order from filenames')
$startupLua281Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.1-boot-(lua|state)' -ErrorAction SilentlyContinue)) {
        $startupLua281Lines.Add($m.Line)
    }
}
$startupLua281Lines | Set-Content -Encoding UTF8 $startupLua281


# Stage 24.28.2: compact Level Selection resource closure report.  It keeps the
# exact sheet/global lookup provenance, bitmap-font transport/use, menu page
# transition, and first subsequent missing primitive together.
$levelSelectionRuntime282 = Join-Path $out 'stage24.28.2-level-selection-runtime.txt'
$levelSelectionRuntime282Lines = New-Object System.Collections.Generic.List[string]
$levelSelectionRuntime282Lines.Add('ANGRY_STAGE24_28_2_LEVEL_SELECTION_RUNTIME 1')
$levelSelectionRuntime282Lines.Add('policy=FONT_LS_SMALL exact texture transport + ARMv7-conditioned unique-owner sprite lookup; startup splashes still disabled')
$levelSelectionRuntime282Lines.Add('test=finish/fail 1-1 -> Menu/Home -> inspect Level Selection; keep navigating if it renders')
$levelSelectionRuntime282Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.2-resource-lookup|stage24\.28\.1-visible-menu|stage24\.28\.0-navigation-runtime|stage24\.13\.4-font|stage24\.13\.2-menu' -ErrorAction SilentlyContinue)) {
        $levelSelectionRuntime282Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.2|stage24\.13\.4-font|stage24\.13\.2-menu|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $levelSelectionRuntime282Lines.Add($m.Line)
    }
}
$levelSelectionRuntime282Lines | Set-Content -Encoding UTF8 $levelSelectionRuntime282

# Stage 24.28.3: isolate the frame-ownership fix from the very large menu trace.
# This report must prove that updateMenu frames skip reconstructed gameplay world/HUD
# and that untouched drawMenu itself reaches the recovered native theme renderer.
$menuRenderOwnership283 = Join-Path $out 'stage24.28.3-menu-render-ownership-runtime.txt'
$menuRenderOwnership283Lines = New-Object System.Collections.Generic.List[string]
$menuRenderOwnership283Lines.Add('ANGRY_STAGE24_28_3_MENU_RENDER_OWNERSHIP_RUNTIME 1')
$menuRenderOwnership283Lines.Add('expected=updateMenu owns full frame; gameplay world/HUD/pause skipped; original drawMenu calls recovered drawBackgroundNative/drawForegroundNative')
$menuRenderOwnership283Lines.Add('test=finish 1-1 -> Menu/Home -> Level Selection -> Episode Selection -> Main Menu -> About/side panels')
$menuRenderOwnership283Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.3-(render-ownership|menu-background|menu-theme)|stage24\.28\.2-resource-lookup|stage24\.28\.1-visible-menu|stage24\.28\.0-navigation-runtime' -ErrorAction SilentlyContinue)) {
        $menuRenderOwnership283Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.3|LUA ERROR|FAIL' -ErrorAction SilentlyContinue)) {
        $menuRenderOwnership283Lines.Add($m.Line)
    }
}
$menuRenderOwnership283Lines | Set-Content -Encoding UTF8 $menuRenderOwnership283

# Stage 24.28.4: split the regression/fault run into a compact overlay renderer
# report and a Lua/platform-boundary report. The runtime file should prove that
# pause/result pages redraw gameplay before untouched drawMenu while root menus
# remain full-frame. URL_REQUEST must be non-fatal and no-launch in this stage.
$overlayPlatformRuntime284 = Join-Path $out 'stage24.28.4-overlay-platform-runtime.txt'
$overlayPlatformRuntime284Lines = New-Object System.Collections.Generic.List[string]
$overlayPlatformRuntime284Lines.Add('ANGRY_STAGE24_28_4_OVERLAY_PLATFORM_RUNTIME 1')
$overlayPlatformRuntime284Lines.Add('expected=GAMEPLAY_OVERLAY for pause/result pages; FULL_FRAME_MENU for ordinary menus; openURL diagnostic no-launch keeps Lua alive')
$overlayPlatformRuntime284Lines.Add('test=try slow-settling Red -> finish 1-1 -> inspect dim final scene -> Main Menu -> click trailer -> continue navigating')
$overlayPlatformRuntime284Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.4-(render-ownership|platform-boundary)|stage24\.28\.3-(menu-background|render-ownership)|stage24\.28\.0-navigation-runtime|stage24\.27\.0-bird-rest' -ErrorAction SilentlyContinue)) {
        $overlayPlatformRuntime284Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.4|openURL|LUA ERROR|FAIL|quarantine' -ErrorAction SilentlyContinue)) {
        $overlayPlatformRuntime284Lines.Add($m.Line)
    }
}
$overlayPlatformRuntime284Lines | Set-Content -Encoding UTF8 $overlayPlatformRuntime284

$overlayPlatformLua284 = Join-Path $out 'stage24.28.4-overlay-platform-lua-contract.txt'
$overlayPlatformLua284Lines = New-Object System.Collections.Generic.List[string]
$overlayPlatformLua284Lines.Add('ANGRY_STAGE24_28_4_OVERLAY_PLATFORM_LUA_CONTRACT 1')
$overlayPlatformLua284Lines.Add('source=untouched Lua closures dumped before native binding replacement')
$overlayPlatformLua284Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.4-lua-contract' -ErrorAction SilentlyContinue)) {
        $overlayPlatformLua284Lines.Add($m.Line)
    }
}
$overlayPlatformLua284Lines | Set-Content -Encoding UTF8 $overlayPlatformLua284

# Stage 24.28.5: exact Level/Episode selection base-color + res.openURL closure.
$menuBgPlatformRuntime285 = Join-Path $out 'stage24.28.5-menu-bg-platform-runtime.txt'
$menuBgPlatformRuntime285Lines = New-Object System.Collections.Generic.List[string]
$menuBgPlatformRuntime285Lines.Add('ANGRY_STAGE24_28_5_MENU_BG_PLATFORM_RUNTIME 1')
$menuBgPlatformRuntime285Lines.Add('expected=FULL_FRAME_MENU clear uses untouched currentMenuPage.bgColor; _G.res.openURL is installed diagnostic no-launch and Lua survives')
$menuBgPlatformRuntime285Lines.Add('test=finish 1-1 -> Menu -> inspect Level Selection upper background -> Episode Selection -> Main Menu -> click trailer -> continue navigating')
$menuBgPlatformRuntime285Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.5-(bgcolor|platform-boundary)|stage24\.28\.4-(render-ownership|platform-boundary)|stage24\.28\.0-navigation-runtime' -ErrorAction SilentlyContinue)) {
        $menuBgPlatformRuntime285Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.28\.5|openURL|LUA ERROR|FAIL|quarantine' -ErrorAction SilentlyContinue)) {
        $menuBgPlatformRuntime285Lines.Add($m.Line)
    }
}
$menuBgPlatformRuntime285Lines | Set-Content -Encoding UTF8 $menuBgPlatformRuntime285

$menuBgPlatformLua285 = Join-Path $out 'stage24.28.5-menu-bg-platform-lua-contract.txt'
$menuBgPlatformLua285Lines = New-Object System.Collections.Generic.List[string]
$menuBgPlatformLua285Lines.Add('ANGRY_STAGE24_28_5_MENU_BG_PLATFORM_LUA_CONTRACT 1')
$menuBgPlatformLua285Lines.Add('source=untouched updateMenu/drawLevelSelectionBackground/gotoAngryBirdsTrailer bytecode before native replacement')
$menuBgPlatformLua285Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.28\.5-lua-contract|drawLevelSelectionBackground|gotoAngryBirdsTrailer' -ErrorAction SilentlyContinue)) {
        $menuBgPlatformLua285Lines.Add($m.Line)
    }
}
$menuBgPlatformLua285Lines | Set-Content -Encoding UTF8 $menuBgPlatformLua285

# Stage 24.29.0: user-visible startup/splash boot restoration.
$startupBootRuntime290 = Join-Path $out 'stage24.29.0-startup-boot-runtime.txt'
$startupBootRuntime290Lines = New-Object System.Collections.Generic.List[string]
$startupBootRuntime290Lines.Add('ANGRY_STAGE24_29_0_STARTUP_BOOT_RUNTIME 1')
$startupBootRuntime290Lines.Add('expected=core startup branding owns screen before any gameplay; Rovio 2s white -> Angry Birds 1s black -> untouched mainMenu/updateMenu. Clickgamer is shown only when a concrete retained sprite owner exists.')
$startupBootRuntime290Lines.Add('test=fresh launch -> observe branding -> Main Menu/title_theme -> Play -> Episode -> Poached Eggs -> Level 1. No Level1 frame may appear before UI navigation.')
$startupBootRuntime290Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.29\.0-boot|LIVE game mode|LIVE update mode|title_theme|currentMenu.*mainMenu|prepareMenuPage' -ErrorAction SilentlyContinue)) {
        $startupBootRuntime290Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.29\.0|LUA ERROR|FAIL|eglSwapBuffers startup' -ErrorAction SilentlyContinue)) {
        $startupBootRuntime290Lines.Add($m.Line)
    }
}
$startupBootRuntime290Lines | Set-Content -Encoding UTF8 $startupBootRuntime290

# Stage 24.29.1: first-frame black-screen closure for legacy RGB565 PVR v2
# splash atlases. Keep the boot trace plus exact parser/upload evidence compact.
$rgb565StartupRuntime291 = Join-Path $out 'stage24.29.1-rgb565-startup-runtime.txt'
$rgb565StartupRuntime291Lines = New-Object System.Collections.Generic.List[string]
$rgb565StartupRuntime291Lines.Add('ANGRY_STAGE24_29_1_RGB565_STARTUP_RUNTIME 1')
$rgb565StartupRuntime291Lines.Add('expected=SPLASHES_SHEET_1/2 parse as exact RGB565-v2 and upload as GL_RGB/GL_UNSIGNED_SHORT_5_6_5; boot DISPLAY must advance past Rovio instead of render FAIL frame=1')
$rgb565StartupRuntime291Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.29\.0-boot|stage24\.14\.4-pvr.*(SPLASHES_SHEET|BACKGROUNDS_GE_1|BACKGROUNDS_MAIN_1)|stage23\.6C-upload.*(SPLASHES_SHEET|BACKGROUNDS_GE_1|BACKGROUNDS_MAIN_1)' -ErrorAction SilentlyContinue)) {
        $rgb565StartupRuntime291Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.29\.0-boot|stage24\.14\.4-pvr.*(SPLASHES_SHEET|BACKGROUNDS_GE_1|BACKGROUNDS_MAIN_1)|render FAIL|splash draw failed' -ErrorAction SilentlyContinue)) {
        $rgb565StartupRuntime291Lines.Add($m.Line)
    }
}
$rgb565StartupRuntime291Lines | Set-Content -Encoding UTF8 $rgb565StartupRuntime291

# Stage 24.30.0: first-entry story/cutscene contract frontier. The live probe
# intentionally does not load resources; it records createSpriteSheet/release
# calls and lets untouched Lua reveal the next native dependency.
$cutsceneRuntime300 = Join-Path $out 'stage24.30.0-cutscene-story-runtime.txt'
$cutsceneRuntime300Lines = New-Object System.Collections.Generic.List[string]
$cutsceneRuntime300Lines.Add('ANGRY_STAGE24_30_0_CUTSCENE_STORY_RUNTIME 1')
$cutsceneRuntime300Lines.Add('historical_stage30_0_context=AUDIT_ONLY evidence retained; Stage24.30.1 now replaces only res.createSpriteSheet/res.releaseSpriteSheet with the recovered dynamic bridge and preserves original releaseCutScenes Lua ownership')
$cutsceneRuntime300Lines.Add('test=fresh boot -> Main Menu -> Play -> Poached Eggs -> Level 1-1; allow first-entry story path to advance until the next genuine missing boundary')
$cutsceneRuntime300Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.0-cutscene-runtime|createSpriteSheet|releaseSpriteSheet|loadCutScenes|prepareCutScene|releaseCutScenes|currentMenu.*theme1Start|STORY_|CUTSCENE_' -ErrorAction SilentlyContinue)) {
        $cutsceneRuntime300Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'LUA ERROR|attempt to call field|stage24\.30\.0|FAIL' -ErrorAction SilentlyContinue)) {
        $cutsceneRuntime300Lines.Add($m.Line)
    }
}
$cutsceneRuntime300Lines | Set-Content -Encoding UTF8 $cutsceneRuntime300

$cutsceneLua300 = Join-Path $out 'stage24.30.0-cutscene-lua-contract.txt'
$cutsceneLua300Lines = New-Object System.Collections.Generic.List[string]
$cutsceneLua300Lines.Add('ANGRY_STAGE24_30_0_CUTSCENE_LUA_CONTRACT 1')
$cutsceneLua300Lines.Add('source=untouched Lua 5.1 closures/tables captured before native replacement and after original initializeMenu')
$cutsceneLua300Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.0-cutscene-lua|stage24\.30\.0-cutscene-table' -ErrorAction SilentlyContinue)) {
        $cutsceneLua300Lines.Add($m.Line)
    }
}
$cutsceneLua300Lines | Set-Content -Encoding UTF8 $cutsceneLua300

# Stage 24.30.2: bootstrap reuse hotfix.  The pre-loader scaffold may replay
# force=false image creation before GPU init; already-resident sheets must be
# reused without requiring dynamic texture ownership.
$cutsceneBootstrap302 = Join-Path $out 'stage24.30.2-pre-gpu-bootstrap-runtime.txt'
$cutsceneBootstrap302Lines = New-Object System.Collections.Generic.List[string]
$cutsceneBootstrap302Lines.Add('ANGRY_STAGE24_30_2_PRE_GPU_BOOTSTRAP_RUNTIME 1')
$cutsceneBootstrap302Lines.Add('expected=pre-loader force=false requests for resident sheets log REUSE_PRELOADED gpuReady=no; no dynamic-resource-bridge startup fault; splashes then boot normally')
$cutsceneBootstrap302Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.2-pre-gpu-reuse|stage24\.29\.[01]-boot|stage24\.30\.1-dynamic-sheet|pre-loader scaffold' -ErrorAction SilentlyContinue)) {
        $cutsceneBootstrap302Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'dynamic resource bridge unavailable|dynamic GPU bridge unavailable|createSpriteSheet|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $cutsceneBootstrap302Lines.Add($m.Line)
    }
}
$cutsceneBootstrap302Lines | Set-Content -Encoding UTF8 $cutsceneBootstrap302

# Stage 24.30.3: close the concrete supplemental MENU/OTHER residency frontier
# exposed by v0.26.93 (GOLDEN_EGGS_SHEET_2 before GLES exists).
$preGpuMenu303 = Join-Path $out 'stage24.30.3-pre-gpu-menu-resource-closure-runtime.txt'
$preGpuMenu303Lines = New-Object System.Collections.Generic.List[string]
$preGpuMenu303Lines.Add('ANGRY_STAGE24_30_3_PRE_GPU_MENU_RESOURCE_CLOSURE_RUNTIME 1')
$preGpuMenu303Lines.Add("expected=GOLDEN_EGGS_SHEET_2 reaches REUSE_PRELOADED gpuReady=no; pre-loader continues without dynamic GPU bridge fault; CUTSCENES remain dynamic after normal menu navigation")
$preGpuMenu303Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.2-pre-gpu-reuse.*(GOLDEN_EGGS_SHEET_2|GOLDEN_EGGS_SHEET_4|ACHIEVEMENTS_SHEET_1|LEVELSELECTION_SHEET_2|MENU_ELEMENTS_[23]|SPLASHES_SHEET_3)|stage24\.29\.[01]-boot|stage24\.30\.1-dynamic-sheet.*CUTSCENES' -ErrorAction SilentlyContinue)) {
        $preGpuMenu303Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'dynamic GPU bridge unavailable|dynamic resource bridge unavailable|createSpriteSheet|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $preGpuMenu303Lines.Add($m.Line)
    }
}
$preGpuMenu303Lines | Set-Content -Encoding UTF8 $preGpuMenu303

# Stage 24.30.4: authoritative bootstrap metadata manifest. v0.26.94 staged
# supplemental DAT/texture assets but historical C++ extraction/load lists did
# not consume them, so GOLDEN_EGGS_SHEET_2 still appeared non-resident.
$bootstrapMeta304 = Join-Path $out 'stage24.30.4-bootstrap-meta-manifest-runtime.txt'
$bootstrapMeta304Lines = New-Object System.Collections.Generic.List[string]
$bootstrapMeta304Lines.Add('ANGRY_STAGE24_30_4_BOOTSTRAP_META_MANIFEST_RUNTIME 1')
$bootstrapMeta304Lines.Add('expected=EXTRACT and LOAD include GOLDEN_EGGS_SHEET_2; then pre-GPU createSpriteSheet logs REUSE_PRELOADED gpuReady=no; no dynamic GPU bridge startup fault')
$bootstrapMeta304Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.4-bootstrap-meta|stage24\.30\.2-pre-gpu-reuse.*GOLDEN_EGGS_SHEET_2|stage24\.29\.[01]-boot|stage24\.30\.1-dynamic-sheet.*CUTSCENES' -ErrorAction SilentlyContinue)) {
        $bootstrapMeta304Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'dynamic GPU bridge unavailable|createSpriteSheet|LUA ERROR|stage24\.30\.4-bootstrap-meta' -ErrorAction SilentlyContinue)) {
        $bootstrapMeta304Lines.Add($m.Line)
    }
}
$bootstrapMeta304Lines | Set-Content -Encoding UTF8 $bootstrapMeta304

# Stage 24.31.2: first-run Red tutorial restoration.
$tutorial312 = Join-Path $out 'stage24.31.2-first-run-tutorial-runtime.txt'
$tutorial312Lines = New-Object System.Collections.Generic.List[string]
$tutorial312Lines.Add('ANGRY_STAGE24_31_2_FIRST_RUN_TUTORIAL_RUNTIME 1')
$tutorial312Lines.Add('expected=hidden bootstrap may produce TUTORIAL_1 but 31.2a rolls its queue+seen mutation back; real post-cutscene updateLoading queues TUTORIAL_1; overlay persists with physics paused until TUTORIAL_OK; after saved restart seen-state suppresses queue')
$tutorial312Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.2a-tutorial\]|stage24\.31\.2-tutorial\]|TUTORIAL_RED|TUTORIAL_1|TUTORIAL_OK|stage24\.31\.1-persistence\].*(WRITE|LOAD).*settings\.lua' -ErrorAction SilentlyContinue)) {
        $tutorial312Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.2-tutorial|drawCompoSprite|TUTORIAL|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $tutorial312Lines.Add($m.Line)
    }
}
$tutorial312Lines | Set-Content -Encoding UTF8 $tutorial312

# Stage 24.31.3: settings gear / Golden Egg effect / global UI seam telemetry.
$ui313 = Join-Path $out 'stage24.31.3-ui-microfidelity-runtime.txt'
$ui313Lines = New-Object System.Collections.Generic.List[string]
$ui313Lines.Add('ANGRY_STAGE24_31_3_UI_MICROFIDELITY_RUNTIME 1')
$ui313Lines.Add('expected=Stage24.31.3 telemetry retained for gear/Golden Egg; Stage24.31.4 may center-sample target-sized UI quads while preserving the same transform evidence')
$ui313Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.3-ui\]|GOLDEN_EGG_STAR_EFFECT|MAIN_SETTINGS_(LEFT|RIGHT)|MENU_SLIDER_BG|TUTORIAL_RED' -ErrorAction SilentlyContinue)) {
        $ui313Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.3-ui|GOLDEN_EGG|MAIN_SETTINGS|drawCompoSprite|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $ui313Lines.Add($m.Line)
    }
}
$ui313Lines | Set-Content -Encoding UTF8 $ui313

# Stage 24.31.4: evidence-backed target-size center-of-texel seam fix.
$ui314 = Join-Path $out 'stage24.31.4-ui-seam-runtime.txt'
$ui314Lines = New-Object System.Collections.Generic.List[string]
$ui314Lines.Add('ANGRY_STAGE24_31_4_UI_SEAM_RUNTIME 1')
$ui314Lines.Add('expected=target-sized UI pieces log CENTER_SAMPLE action=APPLY; visually straight seams disappear from Episode Selection cards/tutorial boxes while natural-size sprites remain unchanged')
$ui314Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.4-seam\]|MENU_SLIDER_BG|MAIN_SETTINGS_(LEFT|RIGHT)|TUTORIAL_RED' -ErrorAction SilentlyContinue)) {
        $ui314Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.4-seam|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $ui314Lines.Add($m.Line)
    }
}
$ui314Lines | Set-Content -Encoding UTF8 $ui314

# Stage 24.31.4f: legacy 1:1 raster + outer composited modern presentation.
$ui314f = Join-Path $out 'stage24.31.4f-composited-presentation-runtime.txt'
$ui314fLines = New-Object System.Collections.Generic.List[string]
$ui314fLines.Add('ANGRY_STAGE24_31_4F_COMPOSITED_PRESENTATION_RUNTIME 1')
$ui314fLines.Add('expected=RASTER_INIT reports legacy rasterScale=1x1; PRESENT_PASS exists for boot/menu/gameplay; visible output is aspect-fit modern scale; touch maps OUTPUT_VIEWPORT_TO_LOGICAL')
$ui314fLines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.4f-presentation\]' -ErrorAction SilentlyContinue)) {
        $ui314fLines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.4f-presentation|COPY_FAIL|PRESENT_FAIL|DRAW_FAIL|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $ui314fLines.Add($m.Line)
    }
}
$ui314fLines | Set-Content -Encoding UTF8 $ui314f

# Stage 24.31.5: menu transform runtime. Keep the existing .31.3 target
# telemetry, but collect it under the current RenderState2D contract frontier.
$ui315 = Join-Path $out 'stage24.31.5-menu-transform-runtime.txt'
$ui315Lines = New-Object System.Collections.Generic.List[string]
$ui315Lines.Add('ANGRY_STAGE24_31_5B_MENU_TRANSFORM_RUNTIME 1')
$ui315Lines.Add('policy=VALIDATE_RECOVERED_CONSUMER; target sprites must use PER_DRAW_LOCAL_AFFINE and keep their pivotWorld at the untouched draw position while rotating')
$ui315Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.3-ui.*(RENDER_STATE|BUTTON_OPTIONS|MAIN_SETTINGS|GOLDEN_EGG)|stage24\.31\.5b-ui|stage24\.30\.1-render-state.*(MAIN_SETTINGS|GOLDEN_EGG)' -ErrorAction SilentlyContinue)) {
        $ui315Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.3-ui|MAIN_SETTINGS|GOLDEN_EGG_STAR_EFFECT|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $ui315Lines.Add($m.Line)
    }
}
$ui315Lines | Set-Content -Encoding UTF8 $ui315

# Stage 24.31.5: passive score-fidelity runtime. No score writes are performed
# by this observer; it only records values after the untouched scoring update.
$score315 = Join-Path $out 'stage24.31.5-score-passive-runtime.txt'
$score315Lines = New-Object System.Collections.Generic.List[string]
$score315Lines.Add('ANGRY_STAGE24_31_5_SCORE_PASSIVE_RUNTIME 1')
$score315Lines.Add('policy=OBSERVE_ONLY; compare maxScore, star thresholds, scoreTable bucket deltas, completion gate, post-complete bird bonus, and RESULT_STARS')
$score315Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.5-score-passive|stage24\.19\.1-score-ledger|stage24\.19\.3-block-score-restored' -ErrorAction SilentlyContinue)) {
        $score315Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.5-score-passive|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $score315Lines.Add($m.Line)
    }
}
$score315Lines | Set-Content -Encoding UTF8 $score315

# Stage 24.32.0: focused progression runtime.  This collects the original
# levelSelectionPagesBasic mapping and live Level57 -> Level53 transition.
$progress320 = Join-Path $out 'stage24.32.0-progression-runtime.txt'
$progress320Lines = New-Object System.Collections.Generic.List[string]
$progress320Lines.Add('ANGRY_STAGE24_32_0_PROGRESSION_RUNTIME 1')
$progress320Lines.Add('policy=OBSERVE_ONLY; expected original map 1-1=Level1, 1-2=Level57, 1-3=Level53; no unlock/save/progression override')
$progress320Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.32-progression|stage24\.12\.9-menu-audit.*stage24\.32-progression-map|stage24\.12\.9-menu-audit.*getNextLevel\(\x27Level57\x27\)' -ErrorAction SilentlyContinue)) {
        $progress320Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.32-progression|Level53|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $progress320Lines.Add($m.Line)
    }
}
$progress320Lines | Set-Content -Encoding UTF8 $progress320


# Stage 24.32.1: widened progression, multi-pointer producer, and specialty
# state. Everything here is read-only diagnostics from the live runtime.
$pack321 = Join-Path $out 'stage24.32.1-pack1-multitouch-specialty-runtime.txt'
$pack321Lines = New-Object System.Collections.Generic.List[string]
$pack321Lines.Add('ANGRY_STAGE24_32_1_PACK1_MULTITOUCH_SPECIALTY_RUNTIME 1')
$pack321Lines.Add('policy=OBSERVE_ONLY diagnostics; expected Pack1 map through 1-10; pinch bridge writes zoomLevel only; CLUSTER_BOMB remains untouched Lua-owned')
$pack321Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.32-progression|stage24\.32\.1-multitouch|stage24\.32\.1-specialty|stage24\.12\.9-menu-audit.*stage24\.32-progression-map|stage24\.12\.9-menu-audit.*getNextLevel|\[Level1/GameLua\] CIRCLE' -ErrorAction SilentlyContinue)) {
        $pack321Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.32\.1|Level3|Level6|Level2|Level4|Level5|Level7|Level8|CLUSTER_BOMB|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $pack321Lines.Add($m.Line)
    }
}
$pack321Lines | Set-Content -Encoding UTF8 $pack321

# Stage 24.34.0: Pack1 1-11..1-16 expansion and untouched Yellow BOOST audit.
$yellow340 = Join-Path $out 'stage24.34.0-pack1-yellow-boost-runtime.txt'
$yellow340Lines = New-Object System.Collections.Generic.List[string]
$yellow340Lines.Add('ANGRY_STAGE24_34_0_PACK1_YELLOW_BOOST_RUNTIME 1')
$yellow340Lines.Add('policy=OBSERVE_ONLY; expected stock Pack1 chain through 1-16; BOOST remains untouched Lua-owned')
$yellow340Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.32-progression|stage24\.32\.1-specialty|stage24\.34\.0-boost|Level9|Level13|Level10|Level39|Level12|Level15|BOOST|BIRD_YELLOW_SPECIAL' -ErrorAction SilentlyContinue)) {
        $yellow340Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.34\.0|Level9|Level13|Level10|Level39|Level12|Level15|BOOST|BIRD_YELLOW_SPECIAL|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $yellow340Lines.Add($m.Line)
    }
}
$yellow340Lines | Set-Content -Encoding UTF8 $yellow340


# Stage 24.34.1: first Pack 1 chapter closure (human 1-17..1-21).
$chapter341 = Join-Path $out 'stage24.34.1-pack1-chapter1-closure-runtime.txt'
$chapter341Lines = New-Object System.Collections.Generic.List[string]
$chapter341Lines.Add('ANGRY_STAGE24_34_1_PACK1_CHAPTER1_CLOSURE_RUNTIME 1')
$chapter341Lines.Add('policy=OBSERVE_ONLY; expected untouched Pack1 progression through human 1-21')
$chapter341Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.32-progression|stage24\.12\.9-menu-audit.*getNextLevel|Level17|Level14|Level16|Level23|Level44|LEVEL_ACTIVE|RESULT_MENU' -ErrorAction SilentlyContinue)) {
        $chapter341Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.34\.1|Level17|Level14|Level16|Level23|Level44|LUA ERROR|FATAL|Exception' -ErrorAction SilentlyContinue)) {
        $chapter341Lines.Add($m.Line)
    }
}
$chapter341Lines | Set-Content -Encoding UTF8 $chapter341

# Stage 24.35.0: Pack2 2-1..2-5 transport and untouched Bomb/BOMB audit.
$bomb350 = Join-Path $out 'stage24.35.0-pack2-bomb-runtime.txt'
$bomb350Lines = New-Object System.Collections.Generic.List[string]
$bomb350Lines.Add('ANGRY_STAGE24_35_0_PACK2_BOMB_RUNTIME 1')
$bomb350Lines.Add('policy=OBSERVE_ONLY; expected stock Pack2 2-1..2-5 map; BOMB/makeExplosion remains untouched Lua-owned')
$bomb350Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.35\.0-pack2|stage24\.32\.1-specialty|stage24\.12\.9-menu-audit.*stage24\.35\.0-pack2-chain|Level52|Level34|Level42|Level24|Level88|BOMB|special_explosion|makeExplosion|LEVEL_ACTIVE|RESULT_MENU' -ErrorAction SilentlyContinue)) {
        $bomb350Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.35\.0|Level52|Level34|Level42|Level24|Level88|BOMB|makeExplosion|LUA ERROR|FATAL|Exception|abort' -ErrorAction SilentlyContinue)) {
        $bomb350Lines.Add($m.Line)
    }
}
$bomb350Lines | Set-Content -Encoding UTF8 $bomb350


# Stage 24.35.2: generic MaskedImage fill selection across theme-ground families.
$ground352 = Join-Path $out 'stage24.35.2-theme-ground-fill-runtime.txt'
$ground352Lines = New-Object System.Collections.Generic.List[string]
$ground352Lines.Add('ANGRY_STAGE24_35_2_THEME_GROUND_FILL_RUNTIME 1')
$ground352Lines.Add('expected=Level34 loads with producer textureName=INGAME_THEME_GROUND_2 and MaskedImage flush PASS using fill=INGAME_THEME_GROUND_2')
$ground352Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.35\.2-mask|Level34|INGAME_THEME_GROUND_2|GROUND_BLOCK_0[245]|LIVE frame' -ErrorAction SilentlyContinue)) {
        $ground352Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.35\.2-mask|INGAME_THEME_GROUND_2|LUA ERROR|FATAL|Exception|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $ground352Lines.Add($m.Line)
    }
}
$ground352Lines | Set-Content -Encoding UTF8 $ground352


# Stage 24.36.0: Pack2 2-6..2-14 and untouched White/DROPPABLE_EGG audit.
$white360 = Join-Path $out 'stage24.36.0-pack2-white-runtime.txt'
$white360Lines = New-Object System.Collections.Generic.List[string]
$white360Lines.Add('ANGRY_STAGE24_36_0_PACK2_WHITE_RUNTIME 1')
$white360Lines.Add('policy=OBSERVE_ONLY; expected stock Pack2 map through 2-14; DROPPABLE_EGG remains untouched Lua-owned')
$white360Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.36\.0-white|stage24\.32\.1-specialty|stage24\.12\.9-menu-audit.*stage24\.36\.0-white-chain|Level36|Level31|Level21|Level41|Level76|Level38|Level35|Level20|Level26|DROPPABLE_EGG|flyingGrenades|special_|LEVEL_ACTIVE|RESULT_MENU|CIRCLE' -ErrorAction SilentlyContinue)) {
        $white360Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.36\.0|Level36|Level31|Level21|Level41|Level76|Level38|Level35|Level20|Level26|DROPPABLE_EGG|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $white360Lines.Add($m.Line)
    }
}
$white360Lines | Set-Content -Encoding UTF8 $white360

# Stage 24.36.1: Pack2 2-15..2-21 pure chapter/page closure.
$chapter361 = Join-Path $out 'stage24.36.1-pack2-chapter2-closure-runtime.txt'
$chapter361Lines = New-Object System.Collections.Generic.List[string]
$chapter361Lines.Add('ANGRY_STAGE24_36_1_PACK2_CHAPTER2_CLOSURE_RUNTIME 1')
$chapter361Lines.Add('policy=OBSERVE_ONLY; expected stock Pack2 map through 2-21; stock Next/theme2Complete/save remain authoritative')
$chapter361Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.36\.1-chapter2|stage24\.12\.9-menu-audit.*stage24\.36\.1-chapter2-chain|Level66|Level85|Level27|Level32|Level72|Level90|Level96|LEVEL_ACTIVE|RESULT_MENU|theme2Complete|theme2Completed|BUTTON_NEXTLEVEL|saveLuaFile-real|levelSelectionPagesBasic' -ErrorAction SilentlyContinue)) {
        $chapter361Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.36\.1|Level66|Level85|Level27|Level32|Level72|Level90|Level96|theme2Complete|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $chapter361Lines.Add($m.Line)
    }
}
$chapter361Lines | Set-Content -Encoding UTF8 $chapter361

# Stage 24.37.0: generic RenderState2D negative-scale/background composition proof.
$render370 = Join-Path $out 'stage24.37.0-renderstate-negative-scale-runtime.txt'
$render370Lines = New-Object System.Collections.Generic.List[string]
$render370Lines.Add('ANGRY_STAGE24_37_0_RENDERSTATE_NEGATIVE_SCALE_RUNTIME 1')
$render370Lines.Add('policy=OBSERVE_ONLY; expected LS_BACKGROUND halves cover x=0..854 with generic post-affine scale; no sprite-specific geometry fix')
$render370Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.37\.0-renderstate|LS_BACKGROUND|drawLevelSelectionBackground|stage24\.28\.5-bgcolor.*FRAME_CLEAR|stage24\.31\.3-ui.*RENDER_STATE' -ErrorAction SilentlyContinue)) {
        $render370Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.37\.0|LS_BACKGROUND|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $render370Lines.Add($m.Line)
    }
}
$render370Lines | Set-Content -Encoding UTF8 $render370

# Stage 24.38.0: first Pack3/theme3 runtime frontier through 3-5.
$theme380 = Join-Path $out 'stage24.38.0-pack3-theme3-runtime.txt'
$theme380Lines = New-Object System.Collections.Generic.List[string]
$theme380Lines.Add('ANGRY_STAGE24_38_0_PACK3_THEME3_RUNTIME 1')
$theme380Lines.Add('policy=OBSERVE_ONLY; expected 3-1..3-5 map Level43,Level77,Level28,Level29,Level87; theme3 scene/fill remain original-data owned')
$theme380Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.38\.0-theme3|stage24\.38\.0-mask|stage24\.15\.[23]-scene|stage24\.12\.9-menu-audit.*stage24\.38\.0-theme3-chain|Level43|Level77|Level28|Level29|Level87|theme3|INGAME_PARALLAX_3|INGAME_THEME_GROUND_3|LEVEL_ACTIVE|RESULT_MENU' -ErrorAction SilentlyContinue)) {
        $theme380Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.38\.0|Level43|Level77|Level28|Level29|Level87|theme3|INGAME_PARALLAX_3|INGAME_THEME_GROUND_3|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $theme380Lines.Add($m.Line)
    }
}
$theme380Lines | Set-Content -Encoding UTF8 $theme380


# Stage 24.38.1: Pack3 3-6..3-21 pure page/chapter closure.
$chapter381 = Join-Path $out 'stage24.38.1-pack3-chapter3-closure-runtime.txt'
$chapter381Lines = New-Object System.Collections.Generic.List[string]
$chapter381Lines.Add('ANGRY_STAGE24_38_1_PACK3_CHAPTER3_CLOSURE_RUNTIME 1')
$chapter381Lines.Add('policy=OBSERVE_ONLY; expected stock Pack3 map through 3-21; stock Next/theme3Complete/save remain authoritative')
$chapter381Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.38\.1-chapter3|stage24\.12\.9-menu-audit.*stage24\.38\.1-chapter3-chain|Level18|Level91|Level49|Level45|Level75|Level51|Level30|Level79|Level40|Level59|Level58|Level95|Level82|Level22|Level89|Level81|LEVEL_ACTIVE|RESULT_MENU|theme3Complete|theme3Completed|BUTTON_NEXTLEVEL|saveLuaFile-real|levelSelectionPagesBasic' -ErrorAction SilentlyContinue)) {
        $chapter381Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.38\.1|Level18|Level91|Level49|Level45|Level75|Level51|Level30|Level79|Level40|Level59|Level58|Level95|Level82|Level22|Level89|Level81|theme3Complete|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $chapter381Lines.Add($m.Line)
    }
}
$chapter381Lines | Set-Content -Encoding UTF8 $chapter381

# Stage 24.38.2: regression proof for the original levelFailed menu page table.
$failure382 = Join-Path $out 'stage24.38.2-level-failed-menu-boot-regression-runtime.txt'
$failure382Lines = New-Object System.Collections.Generic.List[string]
$failure382Lines.Add('ANGRY_STAGE24_38_2_LEVEL_FAILED_MENU_BOOT_REGRESSION_RUNTIME 1')
$failure382Lines.Add('policy=OBSERVE_ONLY; original initializeMenu levelFailed table + levelFailedTimer/updateLevelEnding remain authoritative')
$failure382Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.38\.2-failure-menu|stage24\.22\.9 terminal menu|stage24\.28\.0-navigation-runtime.*levelFailed|stage24\.28\.4-render-ownership.*levelFailed|LIVE game mode.*updateMenu' -ErrorAction SilentlyContinue)) {
        $failure382Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.38\.2-failure-menu|Stage24\.22\.9 terminal menu|levelFailed|LUA ERROR|LIVE LUA FAIL|game thread exited' -ErrorAction SilentlyContinue)) {
        $failure382Lines.Add($m.Line)
    }
}
$failure382Lines | Set-Content -Encoding UTF8 $failure382

# Stage 24.39.0: Mighty Hoax 4-1..4-5 + Theme4 first-entry audit.
$mighty390 = Join-Path $out 'stage24.39.0-mighty-hoax-theme4-runtime.txt'
$mighty390Lines = New-Object System.Collections.Generic.List[string]
$mighty390Lines.Add('ANGRY_STAGE24_39_0_MIGHTY_HOAX_THEME4_RUNTIME 1')
$mighty390Lines.Add('policy=OBSERVE_ONLY; untouched levelSelectionPagesExtra/levelOrder.pack4 + Theme4 scene/render/save/progression remain authoritative')
$mighty390Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.39\.0-mighty|stage24\.39\.0-mask|stage24\.39\.0 scene metadata|stage24\.15\.[23]-scene|stage24\.12\.9-menu-audit.*stage24\.39\.0-mighty-theme4-chain|LevelP2_103|LevelP2_91|LevelP2_65|LevelP2_96|LevelP2_69|theme4|INGAME_PARALLAX_4|INGAME_THEME_GROUND_4|levelSelectionPagesExtra|LEVEL_ACTIVE|RESULT_MENU|saveLuaFile-real' -ErrorAction SilentlyContinue)) {
        $mighty390Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.39\.0|LevelP2_103|LevelP2_91|LevelP2_65|LevelP2_96|LevelP2_69|theme4|INGAME_PARALLAX_4|INGAME_THEME_GROUND_4|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException' -ErrorAction SilentlyContinue)) {
        $mighty390Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.39\.0|LevelP2_103|LevelP2_91|LevelP2_65|LevelP2_96|LevelP2_69|theme4|INGAME_PARALLAX_4|INGAME_THEME_GROUND_4|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $mighty390Lines.Add($m.Line)
    }
}
$mighty390Lines | Set-Content -Encoding UTF8 $mighty390

# Stage 24.40.0: first live polygon-object reconstruction, exposed by Mighty Hoax 4-1.
$polygon400 = Join-Path $out 'stage24.40.0-polygon-native-runtime.txt'
$polygon400Lines = New-Object System.Collections.Generic.List[string]
$polygon400Lines.Add('ANGRY_STAGE24_40_0_POLYGON_NATIVE_RUNTIME 1')
$polygon400Lines.Add('policy=original Lua createObject owns polygon production; native bridge only reconstructs clearVertices/addVertex/createPolygon generic physics+Lua object contract')
$polygon400Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.40\.0-polygon|GameLua/Box2D|LevelP2_103|createPolygon|clearVertices|addVertex|LEVEL_ACTIVE|RESULT_MENU' -ErrorAction SilentlyContinue)) {
        $polygon400Lines.Add($m.Line)
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.40\.0-polygon|LevelP2_103|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException' -ErrorAction SilentlyContinue)) {
        $polygon400Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.40\.0-polygon|createPolygon|LUA ERROR|FATAL|Exception|abort' -ErrorAction SilentlyContinue)) {
        $polygon400Lines.Add($m.Line)
    }
}
$polygon400Lines | Set-Content -Encoding UTF8 $polygon400

# Stage 24.40.1: Mighty Hoax transport frontier through 4-10.
$mighty401 = Join-Path $out 'stage24.40.1-mighty-hoax-4-10-runtime.txt'
@(
    'ANGRY_STAGE24_40_1_MIGHTY_HOAX_4_10_RUNTIME 1'
    'policy=observe untouched Pack4 4-6..4-10; no per-level gameplay override'
) | Set-Content -Encoding UTF8 $mighty401
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.40\.1-mighty|stage24\.40\.0-polygon|LevelP2_88|LevelP2_64|LevelP2_80|LevelP2_108|LevelP2_85|LEVEL_ACTIVE|RESULT_MENU|saveLuaFile-real' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty401
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.40\.1|LevelP2_88|LevelP2_64|LevelP2_80|LevelP2_108|LevelP2_85|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty401
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.40\.1|LevelP2_88|LevelP2_64|LevelP2_80|LevelP2_108|LevelP2_85|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty401
    }
}

# Stage 24.40.2: close Mighty Hoax page 1 through 4-21 and capture stock
# page-completion/Next behavior after LevelP2_95.
$mighty402 = Join-Path $out 'stage24.40.2-mighty-hoax-4-21-closure-runtime.txt'
@(
    'ANGRY_STAGE24_40_2_MIGHTY_HOAX_4_21_CLOSURE_RUNTIME 1'
    'policy=observe untouched Pack4 4-11..4-21 + stock completion/Next; no progression override'
) | Set-Content -Encoding UTF8 $mighty402
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.40\.2-mighty|stage24\.40\.0-polygon|LevelP2_82|LevelP2_66|LevelP2_104|LevelP2_210|LevelP2_83|LevelP2_79|LevelP2_77|LevelP2_114|LevelP2_81|LevelP2_68|LevelP2_95|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|BUTTON_NEXTLEVEL|theme4Complete|theme4Completed|levelSelectionPagesExtra|saveLuaFile-real|gameComplete' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty402
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.40\.2|LevelP2_82|LevelP2_66|LevelP2_104|LevelP2_210|LevelP2_83|LevelP2_79|LevelP2_77|LevelP2_114|LevelP2_81|LevelP2_68|LevelP2_95|theme4Complete|theme4Completed|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|cannot open|No such file' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty402
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.40\.2|LevelP2_82|LevelP2_66|LevelP2_104|LevelP2_210|LevelP2_83|LevelP2_79|LevelP2_77|LevelP2_114|LevelP2_81|LevelP2_68|LevelP2_95|theme4Complete|theme4Completed|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL|cannot open|No such file' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty402
    }
}

# Stage 24.41.0: generic checkForLuaFile episode-availability repair + Mighty
# Hoax page/theme 5 frontier through 5-10.
$mighty410 = Join-Path $out 'stage24.41.0-checkforluafile-mighty-page2-runtime.txt'
@(
    'ANGRY_STAGE24_41_0_CHECKFORLUAFILE_MIGHTY_PAGE2_RUNTIME 1'
    'policy=generic read-only file-existence query; untouched hasLevelPack2/prepareMenuPage owns episode visuals; Pack5 5-1..5-10 transport only'
) | Set-Content -Encoding UTF8 $mighty410
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.41\.0-checklua|stage24\.41\.0-mighty|stage24\.41\.0-mask|LevelP2_78|LevelP2_100|LevelP2_92|LevelP2_94|LevelP2_89|LevelP2_73|LevelP2_76|LevelP2_122|LevelP2_99|LevelP2_84|hasLevelPack2|episodeSelectionPage|AVAILABLE_ON_APP_STORE|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty410
    }
}
if (Test-Path $logcat) {
    foreach ($m in @(Select-String -Path $logcat -Pattern 'stage24\.41\.0|LevelP2_78|LevelP2_100|LevelP2_92|LevelP2_94|LevelP2_89|LevelP2_73|LevelP2_76|LevelP2_122|LevelP2_99|LevelP2_84|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|cannot open|No such file' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty410
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.41\.0|LevelP2_78|LevelP2_100|LevelP2_92|LevelP2_94|LevelP2_89|LevelP2_73|LevelP2_76|LevelP2_122|LevelP2_99|LevelP2_84|LUA ERROR|FATAL|Exception|abort|LIVE GPU frame FAIL|cannot open|No such file' -ErrorAction SilentlyContinue)) {
        $m.Line | Add-Content -Encoding UTF8 $mighty410
    }
}

# Stage 24.41.1: close Mighty Hoax Pack5 page 2 through 5-21 and observe stock page completion.
$mighty411 = Join-Path $out 'stage24.41.1-mighty-hoax-5-21-closure-runtime.txt'
@(
    'ANGRY_STAGE24_41_1_MIGHTY_HOAX_5_21_CLOSURE_RUNTIME 1'
    'policy=Pack5 page-sized transport only; stock Next/theme5 completion remains Lua-owned; stop on first runtime failure'
) | Set-Content -Encoding UTF8 $mighty411
$pat411 = 'stage24\.41\.1|stage24\.41\.0-checklua|LevelP2_86|LevelP2_74|LevelP2_115|LevelP2_98|LevelP2_71|LevelP2_72|LevelP2_87|LevelP2_93|LevelP2_67|LevelP2_97|LevelP2_90|theme5Complete|theme5Completed|BUTTON_NEXTLEVEL|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat411 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $mighty411 }
    }
}

# Stage 24.42.0: Danger Above page/theme 6 + Boomerang specialty passive audit.
$danger420 = Join-Path $out 'stage24.42.0-danger-above-theme6-boomerang-runtime.txt'
@(
    'ANGRY_STAGE24_42_0_DANGER_ABOVE_THEME6_BOOMERANG_RUNTIME 1'
    'policy=one natural 15-level page/theme QA boundary; Theme6 transport + untouched Lua BOOMERANG; stop on first runtime failure'
) | Set-Content -Encoding UTF8 $danger420
$pat420 = 'stage24\.42\.0|LevelP3_212|LevelP3_134|LevelP3_162|LevelP3_271|LevelP3_224|LevelP3_253|LevelP3_225|LevelP3_232|LevelP3_150|LevelP3_211|LevelP3_223|LevelP3_226|LevelP3_215|LevelP3_220|LevelP3_231|theme6Start|theme6Complete|theme6Completed|BOOMERANG|BIRD_BOOMERANG|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|checkForLuaFile|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat420 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $danger420 }
    }
}

# Stage 24.42.1: exact nonlegacy deferred bird velocity + passive glass/wood physics audit.
$danger421 = Join-Path $out 'stage24.42.1-nonlegacy-bird-velocity-physics-audit-runtime.txt'
@(
    'ANGRY_STAGE24_42_1_NONLEGACY_BIRD_VELOCITY_PHYSICS_AUDIT_RUNTIME 1'
    'policy=exact ARMv7 nonlegacy deferred bird velocity; glass/wood physics telemetry is OBSERVE_ONLY'
) | Set-Content -Encoding UTF8 $danger421
$pat421 = 'stage24\.42\.1-nonlegacy|DEFER_STORE|DEFER_APPLY|stage24\.42\.1-glasswood|stage24\.42\.0-boomerang|LevelP3_224|LevelP3_253|LevelP3_225|LevelP3_232|LevelP3_150|LevelP3_211|LevelP3_223|LevelP3_226|LevelP3_215|LevelP3_220|LevelP3_231|BOOMERANG|BIRD_BOOMERANG|stage16-native|stage16-callback|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|theme6Complete|theme6Completed|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat421 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $danger421 }
    }
}


# Stage 24.45.0: resume Danger Above at pack7/theme7 and observe stock completion.
$danger450 = Join-Path $out 'stage24.45.0-danger-above-theme7-runtime.txt'
@(
    'ANGRY_STAGE24_45_0_DANGER_ABOVE_THEME7_RUNTIME 1'
    'policy=one natural 15-level page/theme QA boundary; exact Theme7 transport; stock Next/theme7 completion remains Lua-owned'
) | Set-Content -Encoding UTF8 $danger450
$pat450 = 'stage24\.45\.0|LevelP3_166|LevelP3_237|LevelP3_216|LevelP3_298|LevelP3_303|LevelP3_214|LevelP3_159|LevelP3_164|LevelP3_299|LevelP3_302|LevelP3_219|LevelP3_163|LevelP3_160|LevelP3_161|LevelP3_304|theme7Start|theme7Complete|theme7Completed|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat450 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $danger450 }
    }
}

# Stage 24.45.1: close Danger Above at pack8/theme8 and observe stock episode completion.
$danger451 = Join-Path $out 'stage24.45.1-danger-above-theme8-runtime.txt'
@(
    'ANGRY_STAGE24_45_1_DANGER_ABOVE_THEME8_RUNTIME 1'
    'policy=third/final 15-level Danger Above page; exact Theme8 transport; stock Next/theme8 completion remains Lua-owned'
) | Set-Content -Encoding UTF8 $danger451
$pat451 = 'stage24\.45\.1|LevelP3_297|LevelP3_221|LevelP3_306|LevelP3_301|LevelP3_312|LevelP3_309|LevelP3_168|LevelP3_311|LevelP3_308|LevelP3_310|LevelP3_217|LevelP3_307|LevelP3_296|LevelP3_149|LevelP3_313|theme8Start|theme8Complete|theme8Completed|levelSelectionPagesPack3|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat451 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $danger451 }
    }
}

# Stage 24.46.0: enter The Big Setup at pack9/theme9. Capture both the exact
# untouched map and the generic setTheme live table so scene composition is
# proven rather than inferred from asset names.
$bigSetup460 = Join-Path $out 'stage24.46.0-big-setup-theme9-runtime.txt'
@(
    'ANGRY_STAGE24_46_0_BIG_SETUP_THEME9_RUNTIME 1'
    'policy=first 15-level The Big Setup page; exact pack9 transport; Theme9 scene table remains live-original and Lua-owned'
) | Set-Content -Encoding UTF8 $bigSetup460
$pat460 = 'stage24\.46\.0|LevelP4_421|LevelP4_423|LevelP4_424|LevelP4_425|LevelP4_426|LevelP4_427|LevelP4_428|LevelP4_429|LevelP4_431|LevelP4_432|LevelP4_433|LevelP4_436|LevelP4_439|LevelP4_440|LevelP4_441|theme9Start|theme9Complete|theme9Completed|levelSelectionPagesPack4|stage24\.15\.2-theme|stage24\.15\.3-theme|INGAME_PARALLAX_CRANES|SPRITE MISS|missing sprite|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat460 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $bigSetup460 }
    }
}

# Stage 24.46.1: exact original non-repeating background branch first exercised
# by Theme9 crane layers. Capture the four one-shot layer draws and normal
# progression after the previously fail-closed first gameplay frame.
$nonrepeat461 = Join-Path $out 'stage24.46.1-nonrepeat-background-runtime.txt'
@(
    'ANGRY_STAGE24_46_1_NONREPEAT_BACKGROUND_RUNTIME 1'
    'policy=ARMv7 drawBackground repeat=false branch reconstructed exactly; Theme9 remains untouched Lua-owned data'
) | Set-Content -Encoding UTF8 $nonrepeat461
$pat461 = 'stage24\.46\.1|NONREPEAT_DRAW|ARMV7_DRAWBACKGROUND_NONREPEAT|PARALLAX_CRANE_[1-4]|LevelP4_421|LevelP4_423|LevelP4_424|LevelP4_425|LevelP4_426|LevelP4_427|LevelP4_428|LevelP4_429|LevelP4_431|LevelP4_432|LevelP4_433|LevelP4_436|LevelP4_439|LevelP4_440|LevelP4_441|theme9Start|theme9Complete|theme9Completed|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat461 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $nonrepeat461 }
    }
}

# Stage 24.46.2: continue The Big Setup through page2 / pack10. The renderer
# is unchanged from 46.1; capture exact progression, theme evolution and stock
# theme10Complete transition while retaining crash/resource sentinels.
$bigSetup462 = Join-Path $out 'stage24.46.2-big-setup-pack10-runtime.txt'
@(
    'ANGRY_STAGE24_46_2_BIG_SETUP_PACK10_RUNTIME 1'
    'policy=second 15-level The Big Setup page; exact pack10 transport; scene themes and completion remain untouched Lua-owned data'
) | Set-Content -Encoding UTF8 $bigSetup462
$pat462 = 'stage24\.46\.2|NONREPEAT_DRAW|LevelP4_442|LevelP4_443|LevelP4_444|LevelP4_445|LevelP4_448|LevelP4_449|LevelP4_451|LevelP4_452|LevelP4_453|LevelP4_454|LevelP4_455|LevelP4_457|LevelP4_458|LevelP4_459|LevelP4_462|theme10Start|theme10Complete|theme10Completed|levelSelectionPagesPack4|stage24\.15\.3-theme|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat462 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $bigSetup462 }
    }
}

# Stage 24.46.3: final The Big Setup page / pack11. Capture the complete stock
# chapter-ending path while retaining all resource/GPU/Lua/fatal sentinels.
$bigSetup463 = Join-Path $out 'stage24.46.3-big-setup-pack11-runtime.txt'
@(
    'ANGRY_STAGE24_46_3_BIG_SETUP_PACK11_RUNTIME 1'
    'policy=final 15-level The Big Setup page; exact pack11 transport; chapter completion remains untouched Lua-owned data'
) | Set-Content -Encoding UTF8 $bigSetup463
$pat463 = 'stage24\.46\.3|NONREPEAT_DRAW|LevelP4_463|LevelP4_464|LevelP4_465|LevelP4_466|LevelP4_467|LevelP4_468|LevelP4_469|LevelP4_470|LevelP4_471|LevelP4_472|LevelP4_473|LevelP4_474|LevelP4_475|LevelP4_477|LevelP4_478|theme11Start|theme11Complete|theme11Completed|gameFinishedLP4|levelSelectionPagesPack4|stage24\.15\.3-theme|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat463 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $bigSetup463 }
    }
}


# Stage 24.47.0: Golden Eggs branch discovery. Capture exact menu mapping,
# all gameplay/soundboard owners, completion/unlock ownership and fatal sentinels.
$golden470 = Join-Path $out 'stage24.47.0-golden-eggs-runtime.txt'
@(
    'ANGRY_STAGE24_47_0_GOLDEN_EGGS_RUNTIME 1'
    'policy=15 original LevelGE transports + 4 untouched Lua soundboards; no synthetic unlock/completion'
) | Set-Content -Encoding UTF8 $golden470
$pat470 = 'stage24\.47\.0|LevelGE_1|LevelGE_2|LevelGE_3|LevelGE_4|LevelGE_5|LevelGE_6|LevelGE_7|LevelGE_8|LevelGE_9|LevelGE_10|LevelGE_11|LevelGE_12|LevelGE_13|LevelGE_14|LevelGE_15|goldenEgg|GoldenEgg|levelSelectionPagesGoldenEggs|levelOrder_goldenEggs|goldenEggLevelMapping|openGoldenEggLevels|SOUNDBOARD1|RADIO|KEYBOARD|SEQUENCER|goldenEggStarAchieved|calculateStarsFromGoldenEggLevels|stage24\.15\.3-theme|LEVEL_ACTIVE|COMPLETE_GATE|RESULT_MENU|saveLuaFile-real|FROZEN_WRITE|ORIGINAL_ANDROID_NOOP|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat470 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $golden470 }
    }
}

# Stage 24.47.0A: capture the resolved resource path proving that untouched
# levels/... Golden Eggs requests search the original data/ root.
$golden470a = Join-Path $out 'stage24.47.0a-golden-eggs-resource-root-runtime.txt'
@(
    'ANGRY_STAGE24_47_0A_GOLDEN_EGGS_RESOURCE_ROOT_RUNTIME 1'
    'policy=generic levels/... -> data/levels/... resource-root search; no GE filename special case'
) | Set-Content -Encoding UTF8 $golden470a
$pat470a = 'stage24\.47\.0a|stage24\.12\.8-levelpath|levels/goldeneggs1|data/levels/goldeneggs1|LevelGE_|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat470a -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $golden470a }
    }
}

# Stage 24.47.1: focused read-only rubber/beachball solver witness.
# Egg-2 and Danger Above 8-3 are independent repros of the same legacy mismatch.
$rubber471 = Join-Path $out 'stage24.47.1-rubber-physics-audit-runtime.txt'
@(
    'ANGRY_STAGE24_47_1_RUBBER_PHYSICS_AUDIT_RUNTIME 1'
    'policy=OBSERVE_ONLY; no restitution/damping/impulse/geometry mutation'
    'reproA=LevelGE_2'
    'reproB=LevelP3_306 (Danger Above 8-3)'
) | Set-Content -Encoding UTF8 $rubber471
$pat471 = 'stage24\.47\.1-rubber|LevelGE_2|LevelP3_306|ExtraRubberBall|BLOCK_BEACHBALL|material=''rubber''|ball_bounce|stage24\.44\.0-maxtranslation|stage24\.42\.1-nonlegacy|stage16-native|stage16-callback|LEVEL_ACTIVE|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat471 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $rubber471 }
    }
}

# Stage 24.47.2: read-only distance-joint spring network witness. The native
# ARMv7 solver audit is produced during build and included separately below.
$spring472 = Join-Path $out 'stage24.47.2-distance-joint-spring-runtime.txt'
@(
    'ANGRY_STAGE24_47_2_DISTANCE_JOINT_SPRING_RUNTIME 1'
    'policy=OBSERVE_ONLY; measure rubber-owned distance-joint rest/current length, strain, anchor velocity and reaction force'
    'reproA=LevelGE_3 (latest live rubber/super-ball network)'
    'reproB=LevelP3_306 (Danger Above 8-3)'
) | Set-Content -Encoding UTF8 $spring472
$pat472 = 'stage24\.47\.2-spring|stage24\.43\.1-joint|LevelGE_3|LevelP3_306|ExtraTrampoline|ExtraRubberBall|BLOCK_SUPER_BALL|BLOCK_BEACHBALL|material=''rubber''|frequencyHz=4\.000000|dampingRatio=0\.500000|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat472 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $spring472 }
    }
}

# Stage 24.47.3: high-restitution contact solver cross-proof.  LevelGE_2's
# free ExtraRubberBall bodies are the clean isolation case; 8-3 is the
# distance-joint network cross-check.  Ratios are explicitly diagnostic and
# are not treated as direct access to Box2D's internal velocityBias.
$contact473 = Join-Path $out 'stage24.47.3-high-restitution-contact-solver-runtime.txt'
@(
    'ANGRY_STAGE24_47_3_HIGH_RESTITUTION_CONTACT_SOLVER_RUNTIME 1'
    'policy=OBSERVE_ONLY; isolate free rubber contacts and compare coarse begin/after normal-velocity response'
    'reproA=LevelGE_2 / ExtraRubberBall / BLOCK_BEACHBALL / no spring network'
    'reproB=LevelP3_306 / 8-3 / ExtraTrampoline spring network'
    'caveat=BeginContact velocity precedes island gravity/constraint solve; ratios are diagnostics, not direct internal velocityBias'
) | Set-Content -Encoding UTF8 $contact473
$pat473 = 'stage24\.47\.3-contact|stage24\.47\.1-rubber|LevelGE_2|LevelP3_306|ExtraRubberBall|ExtraTrampoline|BLOCK_BEACHBALL|BLOCK_SUPER_BALL|mixedRestitution=5\.5|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat473 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $contact473 }
    }
}

# Stage 24.47.4: manifold warm-start carryover + island integration/clamp
# witness. This corrects the older 47.1 wording: Box2D PostSolve is emitted
# from b2Island::Report after position integration/clamps, not directly after
# SolveVelocityConstraints.
$warm474 = Join-Path $out 'stage24.47.4-rubber-warmstart-integration-runtime.txt'
@(
    'ANGRY_STAGE24_47_4_RUBBER_WARMSTART_INTEGRATION_RUNTIME 1'
    'policy=OBSERVE_ONLY; no contact/joint/body/Lua mutation'
    'question=do manifold warm-start carryover or island linear/angular integration caps explain the remaining rubber network mismatch?'
    'reproA=LevelGE_2 / free ExtraRubberBall isolation when available'
    'reproB=LevelP3_306 / 8-3 ExtraTrampoline network'
    'timing=CONTACT_PRE is manifold state entering World::Step; CONTACT_POST/BODY_POST are after b2Island::Report and integration clamps'
) | Set-Content -Encoding UTF8 $warm474
$pat474 = 'stage24\.47\.4-warm|stage24\.47\.4-integrate|stage24\.47\.3-contact|stage24\.47\.1-rubber|LevelGE_2|LevelGE_3|LevelP3_306|ExtraRubberBall|ExtraTrampoline|mixedRestitution=5\.5|maxTranslation=2|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat474 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $warm474 }
    }
}

# Stage 24.47.5: cross-architecture float-rounding experiment plus generic
# world-joint-list order witness. The build report proves whether AArch64
# relevant physics contains FMADD/FMSUB after -ffp-contract=off.
$fp475 = Join-Path $out 'stage24.47.5-fp-contraction-order-runtime.txt'
@(
    'ANGRY_STAGE24_47_5_FP_CONTRACTION_ORDER_RUNTIME 1'
    'policy=NUMERICAL_FIDELITY_BUILD + OBSERVE_ONLY_RUNTIME_ORDER'
    'change=-ffp-contract=off on box2d212 and stage24_live_surface; no recovered physics constant changed'
    'reproA=visual Golden Egg #2 -> untouched LevelGE_3 rubber trampoline network'
    'reproB=LevelP3_306 / Danger Above 8-3 rubber trampoline network'
    'orderCaveat=WORLD_JOINT_LIST is recorded exactly but is not asserted to equal per-island DFS solver ordering'
) | Set-Content -Encoding UTF8 $fp475
$pat475 = 'stage24\.47\.5-fp|stage24\.47\.5-order|stage24\.47\.4-warm|stage24\.47\.4-integrate|stage24\.47\.2-spring|LevelGE_3|LevelP3_306|ExtraTrampoline|BLOCK_SUPER_BALL|mixedRestitution=5\.5|linearCap=true|angularCap=true|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat475 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $fp475 }
    }
}

# Stage 24.47.6: Android Recents/background Surface lifecycle. A passing run
# must show TERM_WINDOW preserving the existing engine, then INIT_WINDOW ->
# SURFACE_REBOUND without a second game-thread start or startup splash replay.
$lifecycle476 = Join-Path $out 'stage24.47.6-android-lifecycle-runtime.txt'
@(
    'ANGRY_STAGE24_47_6_ANDROID_LIFECYCLE_RUNTIME 1'
    'expected=TERM_WINDOW action=PRESERVE_ENGINE -> INIT_WINDOW action=REBIND_EXISTING_ENGINE -> SURFACE_REBOUND splashReplay=no'
    'forbidden=engine restart / second boot splash merely from opening Android multitarefa/Recents'
) | Set-Content -Encoding UTF8 $lifecycle476
$pat476 = 'stage24\.47\.6-lifecycle|APP_CMD_INIT_WINDOW|APP_CMD_TERM_WINDOW|APP_CMD_PAUSE|APP_CMD_RESUME|APP_CMD_DESTROY|Stage24 native ARM64 game thread starting|Stage24 native ARM64 game thread exited|stage24\.29\.0-boot.*START|stage24\.29\.0-boot.*DISPLAY|eglSwapBuffers|EGL_CONTEXT_LOST|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|glError=0x[1-9A-Fa-f]'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat476 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $lifecycle476 }
    }
}

# Stage 24.43.0: exact joint argument discovery + high-value bounds/lifecycle stub telemetry.
$joint430 = Join-Path $out 'stage24.43.0-joint-bounds-discovery-runtime.txt'
@(
    'ANGRY_STAGE24_43_0_JOINT_BOUNDS_DISCOVERY_RUNTIME 1'
    'policy=historical discovery evidence; later proven consumers may replace stubs; setGameOn may close only as the exact Android allowSleep no-op'
) | Set-Content -Encoding UTF8 $joint430
$pat430 = 'stage24\.43\.0-joint|stage24\.43\.0-bounds|LevelP2_86|LevelP3_215|LevelP3_220|LevelP3_231|LEVEL_ACTIVE|LOAD_LEVEL|setPhysicsEnabled|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat430 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $joint430 }
    }
}

# Stage 24.43.1: reconstructed original type=1 distance joint + retained bounds telemetry.
$joint431 = Join-Path $out 'stage24.43.1-distance-joint-runtime.txt'
@(
    'ANGRY_STAGE24_43_1_DISTANCE_JOINT_RUNTIME 1'
    'policy=type=1 createJoint/destroyJoint reconstructed from ARMv7; retained historical bounds/lifecycle telemetry'
) | Set-Content -Encoding UTF8 $joint431
$pat431 = 'stage24\.43\.1-joint|stage24\.43\.0-joint|stage24\.43\.0-bounds|LevelP2_86|LevelP3_231|LEVEL_ACTIVE|SCORE_CHANGE|birdsShot=0|levelGoals=|COMPLETE_GATE|RESULT_MENU|theme6Complete|theme6Completed|DestroyJoint|CreateJoint|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat431 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $joint431 }
    }
}

# Stage 24.44.0: exact max-translation consumer + passive original-limit crossing witness.
$bounds440 = Join-Path $out 'stage24.44.0-bounds-lifecycle-runtime.txt'
@(
    'ANGRY_STAGE24_44_0_BOUNDS_LIFECYCLE_RUNTIME 1'
    'policy=setMaxTranslation reconstructed exactly; setLevelLimits original integer state + passive OUTSIDE telemetry; setGameOn may be exact Android allowSleep no-op by Stage24.44.3'
) | Set-Content -Encoding UTF8 $bounds440
$pat440 = 'stage24\.44\.0-bounds|stage24\.44\.0-maxtranslation|stage24\.43\.0-bounds|OUTSIDE_ENTER|OUTSIDE_EXIT|OUTSIDE_SUMMARY|failure candidate|hasMovingObjects|levelGoals=|birdsShot=|LEVEL_ACTIVE|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat440 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $bounds440 }
    }
}

# Stage 24.44.1: correlate the live outside-body delay with a shadow version
# of the already-proven motion gates while the build-time report captures the
# exact original GameLua::update/+0x24c/+0x250 consumer. Still observe-only.
$bounds441 = Join-Path $out 'stage24.44.1-level-limit-runtime.txt'
@(
    'ANGRY_STAGE24_44_1_LEVEL_LIMIT_RUNTIME 1'
    'policy=level-limit ownership discovery; SHADOW/OUTSIDE_CLASSIFY/REMOVE_OBJECT_WHILE_OUTSIDE are OBSERVE_ONLY and do not alter Lua or Box2D state'
) | Set-Content -Encoding UTF8 $bounds441
$pat441 = 'stage24\.44\.1-bounds|stage24\.44\.0-bounds|stage24\.44\.0-maxtranslation|stage24\.43\.0-bounds|OUTSIDE_|REMOVE_OBJECT_WHILE_OUTSIDE|LIFECYCLE_END|COMPLETE_GATE|RESULT_MENU|hasMovingObjects|birdsShot=|LEVEL_ACTIVE|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat441 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $bounds441 }
    }
}

# Stage 24.44.2: exact original level-limit consumer now reconstructed.
$bounds442 = Join-Path $out 'stage24.44.2-level-limit-frozen-runtime.txt'
@(
    'ANGRY_STAGE24_44_2_LEVEL_LIMIT_FROZEN_RUNTIME 1'
    'policy=ARMv7 GameLua::update exact consumer: positive-mass object crossing x limits or synchronized y>20 sets object.frozen=true; untouched Lua owns removal'
) | Set-Content -Encoding UTF8 $bounds442
$pat442 = 'stage24\.44\.2-bounds|stage24\.44\.1-bounds|stage24\.44\.0-bounds|REMOVE_OBJECT_WHILE_OUTSIDE|OUTSIDE_|COMPLETE_GATE|RESULT_MENU|hasMovingObjects|birdsShot=|LEVEL_ACTIVE|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat442 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $bounds442 }
    }
}

# Stage 24.44.3: exact Android setGameOn closure. The original virtual target
# is AndroidOSInterface::allowSleep(!gameOn), whose Android body is bx lr.
$gameOn443 = Join-Path $out 'stage24.44.3-setgameon-android-runtime.txt'
@(
    'ANGRY_STAGE24_44_3_SETGAMEON_ANDROID_RUNTIME 1'
    'policy=original Android contract: setGameOn -> allowSleep(!gameOn); allowSleep is a shipping no-op'
) | Set-Content -Encoding UTF8 $gameOn443
$pat443 = 'stage24\.44\.3-gameon|stage24\.28\.0-navigation-runtime|setPhysicsEnabled|LEVEL_ACTIVE|RESULT_MENU|LUA ERROR|LIVE LUA FAIL|LIVE GPU frame FAIL|FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|RuntimeException|callback failed|cannot open|No such file'
foreach ($src in @($stdout,$logcat,$stderr)) {
    if (Test-Path $src) {
        foreach ($m in @(Select-String -Path $src -Pattern $pat443 -ErrorAction SilentlyContinue)) { $m.Line | Add-Content -Encoding UTF8 $gameOn443 }
    }
}

$savePersistence311 = Join-Path $out 'stage24.31.1-save-restart-runtime.txt'
$savePersistence311Lines = New-Object System.Collections.Generic.List[string]
$savePersistence311Lines.Add('ANGRY_STAGE24_31_1_SAVE_RESTART_RUNTIME 1')
$savePersistence311Lines.Add('expected=RUN A writes settings.lua/highscores.lua; RUN B logs PASS_FROM_DISK before initializeMenu and restores progress/audio state')
$savePersistence311Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.1-persistence\]' -ErrorAction SilentlyContinue)) {
        $savePersistence311Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.1-persistence|settings\.lua|highscores\.lua|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $savePersistence311Lines.Add($m.Line)
    }
}
$savePersistence311Lines | Set-Content -Encoding UTF8 $savePersistence311

$profileManifest311 = Join-Path $out 'stage24.31.1-profile-files.txt'
$profileManifest311Lines = New-Object System.Collections.Generic.List[string]
$profileManifest311Lines.Add('ANGRY_STAGE24_31_1_PROFILE_FILES 1')
foreach ($leaf in @('settings.lua','highscores.lua')) {
    $remote = "files/stage24/appdata/$leaf"
    $wc = @(& $adb shell run-as $pkg wc -c $remote 2>$null)
    if ($LASTEXITCODE -eq 0 -and $wc.Count -gt 0) {
        foreach ($line in $wc) { $profileManifest311Lines.Add($line) }
        $sha = @(& $adb shell run-as $pkg sha256sum $remote 2>$null)
        foreach ($line in $sha) { $profileManifest311Lines.Add($line) }
    } else {
        $profileManifest311Lines.Add("MISSING $remote")
    }
    $local = Join-Path $out ("stage24.31.1-" + $leaf)
    $body = @(& $adb exec-out run-as $pkg cat $remote 2>$null)
    if ($LASTEXITCODE -eq 0 -and $body.Count -gt 0) {
        $body | Set-Content -Encoding UTF8 $local
    }
}
$profileManifest311Lines | Set-Content -Encoding UTF8 $profileManifest311

# Stage 24.31.0: save/progress persistence audit.  Runtime probes preserve
# the old no-return/no-write behavior while exposing exact native arguments,
# callsites and snapshots of the named settings/highscores tables.
$savePersistence310 = Join-Path $out 'stage24.31.0-save-persistence-runtime.txt'
$savePersistence310Lines = New-Object System.Collections.Generic.List[string]
$savePersistence310Lines.Add('ANGRY_STAGE24_31_0_SAVE_PERSISTENCE_RUNTIME 1')
$savePersistence310Lines.Add('policy=AUDIT_NO_WRITE; expected=SAVE_LUA_FILE calls expose path/tableName/bool and table snapshots during level complete/settings/menu activity')
$savePersistence310Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.0-persistence\]' -ErrorAction SilentlyContinue)) {
        $savePersistence310Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.31\.0-persistence|saveLuaFile|checkForLuaFile|LUA ERROR' -ErrorAction SilentlyContinue)) {
        $savePersistence310Lines.Add($m.Line)
    }
}
$savePersistence310Lines | Set-Content -Encoding UTF8 $savePersistence310

$savePersistenceLua310 = Join-Path $out 'stage24.31.0-save-persistence-lua-contract.txt'
$savePersistenceLua310Lines = New-Object System.Collections.Generic.List[string]
$savePersistenceLua310Lines.Add('ANGRY_STAGE24_31_0_SAVE_PERSISTENCE_LUA_CONTRACT 1')
$savePersistenceLua310Lines.Add('source=untouched Lua closures captured before native persistence stubs are replaced')
$savePersistenceLua310Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.31\.0-persistence-lua\]' -ErrorAction SilentlyContinue)) {
        $savePersistenceLua310Lines.Add($m.Line)
    }
}
$savePersistenceLua310Lines | Set-Content -Encoding UTF8 $savePersistenceLua310

# Stage 24.30.1: dynamic SpriteDB/GLES ownership and recovered progressive
# setRenderState forms. These are the two implementation gates needed by the
# first-entry gameStart story.
$cutsceneDynamic301 = Join-Path $out 'stage24.30.1-cutscene-dynamic-runtime.txt'
$cutsceneDynamic301Lines = New-Object System.Collections.Generic.List[string]
$cutsceneDynamic301Lines.Add('ANGRY_STAGE24_30_1_CUTSCENE_DYNAMIC_RUNTIME 1')
$cutsceneDynamic301Lines.Add('expected=create six CUTSCENES sheets into registry; acquire original textures; STORY_BEGIN_* bounds/draws become concrete; original releaseCutScenes later unloads dynamic sheets')
$cutsceneDynamic301Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.1-dynamic-sheet|stage24\.30\.1-cutscene-runtime|STORY_BEGIN_|gameStart|loadCutScenes|releaseCutScenes' -ErrorAction SilentlyContinue)) {
        $cutsceneDynamic301Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'stage24\.30\.1-dynamic-sheet|LUA ERROR|drawMenu FAIL|createSpriteSheet|releaseSpriteSheet' -ErrorAction SilentlyContinue)) {
        $cutsceneDynamic301Lines.Add($m.Line)
    }
}
$cutsceneDynamic301Lines | Set-Content -Encoding UTF8 $cutsceneDynamic301

$cutsceneRenderState301 = Join-Path $out 'stage24.30.1-cutscene-renderstate-runtime.txt'
$cutsceneRenderState301Lines = New-Object System.Collections.Generic.List[string]
$cutsceneRenderState301Lines.Add('ANGRY_STAGE24_30_1_CUTSCENE_RENDERSTATE_RUNTIME 1')
$cutsceneRenderState301Lines.Add('expected=gameStart may exercise argc=4 translation+scale without Lua error; retained argc=5/7 menu paths must continue')
$cutsceneRenderState301Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.30\.1-render-state|page=.gameStart.|STORY_BEGIN_|stage24\.28\.3-render-ownership' -ErrorAction SilentlyContinue)) {
        $cutsceneRenderState301Lines.Add($m.Line)
    }
}
if (Test-Path $stderr) {
    foreach ($m in @(Select-String -Path $stderr -Pattern 'setRenderState|LUA ERROR|drawMenu FAIL' -ErrorAction SilentlyContinue)) {
        $cutsceneRenderState301Lines.Add($m.Line)
    }
}
$cutsceneRenderState301Lines | Set-Content -Encoding UTF8 $cutsceneRenderState301

$hudAlpha241 = Join-Path $out 'stage24.24.1-hud-alpha.txt'
$hudAlpha241Lines = New-Object System.Collections.Generic.List[string]
$hudAlpha241Lines.Add('ANGRY_STAGE24_24_1_HUD_ALPHA_PROVENANCE 1')
$hudAlpha241Lines.Add('source=raw original RGBA4444 atlas texels; renderer submits glColor4f(1,1,1,1)')
$hudAlpha241Lines.Add('')
if (Test-Path $stdout) {
    foreach ($m in @(Select-String -Path $stdout -Pattern 'stage24\.24\.1-hud-alpha' -ErrorAction SilentlyContinue)) {
        $hudAlpha241Lines.Add($m.Line)
    }
}
$hudAlpha241Lines | Set-Content -Encoding UTF8 $hudAlpha241

$sceneAudit = Join-Path $out 'stage24.15.0-gameplay-scene-contract.txt'
if (Test-Path $sceneAudit) {
    $summaryLines.Add('--- static scene audit ---')
    $summaryLines.Add('stage24.15.0-gameplay-scene-contract.txt included in bundle')
    $summaryLines.Add('')
}

$summaryLines | Set-Content -Encoding UTF8 $summary

$include = New-Object System.Collections.Generic.List[string]
foreach ($p in @($logcat, $stdout, $stderr, $summary, $contextPresentation, $presentationLive, $presentationLua, $selectorMatrix, $slingshotLua, $slingshotRender, $scoreHudLua, $scoreLedger, $blockScoreShadow, $blockScoreRestored, $scoreHudRuntime, $debugDisplay, $floatingScores, $failureContract, $birdsLifecycle, $birdSettle, $rovioPhysicsRuntime, $terminalMenuRuntime, $hudRemainder, $gameplayHudRuntime, $pauseMenuRuntime, $pauseAudioAudit, $pauseResumeRuntime, $particleContract, $particleRuntime241, $particleVisible242, $audioLua250, $audioRuntime251, $audioPlayback252, $audioOutput253, $audioFidelity254Runtime, $audioRampOwner255, $audioMp3257, $audioClosure258Runtime, $trajectoryLua260, $trajectoryRuntime260, $trajectoryPuffLua261, $trajectoryPuffRuntime261, $trajectoryRuntime262, $birdRestLua270, $birdRestRuntime270, $menuUiRuntime280, $navigationRuntime280, $visibleMenu281, $startupLua281, $levelSelectionRuntime282, $menuRenderOwnership283, $overlayPlatformRuntime284, $overlayPlatformLua284, $menuBgPlatformRuntime285, $menuBgPlatformLua285, $startupBootRuntime290, $rgb565StartupRuntime291, $cutsceneRuntime300, $cutsceneLua300, $cutsceneDynamic301, $cutsceneRenderState301, $bounds440, $bounds441, $tutorial312, $ui313, $ui314, $ui314f, $ui315, $score315, $progress320, $pack321, $yellow340, $chapter341, $bomb350, $theme380, $mighty390, $savePersistence311, $profileManifest311, $savePersistence310, $savePersistenceLua310, $hudAlpha241)) {
    if (Test-Path $p) { $include.Add($p) }
}
foreach ($name in @('stage24.31.1-settings.lua','stage24.31.1-highscores.lua')) {
    $p = Join-Path $out $name
    if (Test-Path $p) { $include.Add($p) }
}
foreach ($name in @(
    'stage24.16.0-asset-profile-contract.txt',
    'stage24.16.0-armv7-presentation-contract.txt',
    'stage24.16.1-native-resolution-ownership.txt',
    'stage24.16.2-screen-global-source.txt',
    'stage24.16.3-egl-factory-callgraph.txt',
    'stage24.16.4-jni-dimension-provenance.txt',
    'stage24.18.0-slingshot-render-contract.txt',
    'stage24.19.0-gameplay-score-hud-contract.txt',
    'stage24.19.2-armv7-block-score-ownership.txt',
    'stage24.22.3-box2d-settle-contract.txt',
    'stage24.22.4-box2d-contact-bias-contract.txt',
    'stage24.22.5-body-fixture-contract.txt',
    'stage24.22.6-contact-material-mix-contract.txt',
    'stage24.22.7-linear-slop-position-contract.txt',
    'stage24.22.8-rovio-box2d-tolerances.txt',
    'stage24.23.4-pause-audio-native-contract.txt',
    'stage24.24.0-particle-native-contract.txt',
    'stage24.24.1-particle-emitter-limit-contract.txt',
    'stage24.25.0-audio-native-contract.txt',
    'stage24.25.1-audio-mixer-wav-contract.txt',
    'stage24.25.4-audio-fidelity-contract.txt',
    'stage24.25.5-mp3-decode-loop-contract.txt',
    'stage24.25.6-audioclipinstance-eof-loop-contract.txt',
    'stage24.25.8-audio-closure-contract.txt',
    'stage24.26.0-trajectory-native-contract.txt',
    'stage24.26.1-trajectory-renderer-puff-contract.txt',
    'stage24.26.2-trajectory-renderer-implementation-contract.txt',
    'stage24.27.0-bird-rest-native-contract.txt',
    'stage24.28.0-menu-ui-native-corpus-contract.txt',
    'stage24.28.1-startup-branding-asset-contract.txt',
    'stage24.28.2-level-selection-resource-contract.txt',
    'stage24.28.3-menu-render-ownership-contract.txt',
    'stage24.28.4-overlay-platform-boundary-contract.txt',
    'stage24.28.5-menu-bg-openurl-contract.txt',
    'stage24.29.0-startup-boot-contract.txt',
    'stage24.29.1-rgb565-splash-contract.txt',
    'stage24.30.0-cutscene-story-native-contract.txt',
    'stage24.30.1-cutscene-dynamic-renderstate-contract.txt',
    'stage24.31.0-save-persistence-native-contract.txt',
    'stage24.31.1-real-save-restart-contract.txt',
    'stage24.31.2-first-run-tutorial-restoration-contract.txt',
    'stage24.31.3-ui-microfidelity-contract.txt',
    'stage24.31.4-ui-seam-fidelity-contract.txt',
    'stage24.31.4a-original-egl-image-draw-contract.txt',
    'stage24.31.4b-original-texture-sampling-backing-contract.txt',
    'stage24.31.4c-original-egl-image-pot-backing-contract.txt',
    'stage24.31.4f-composited-presentation-contract.txt',
    'stage24.31.4f-composited-presentation-runtime.txt',
    'stage24.31.5-original-renderstate2d-contract.txt',
    'stage24.31.5b-renderstate2d-reconstruction-contract.txt',
    'stage24.31.5-score-passive-contract.txt',
    'stage24.31.5-menu-transform-runtime.txt',
    'stage24.31.5-score-passive-runtime.txt',
    'stage24.32.0-progression-expansion-contract.txt',
    'stage24.32.0-progression-runtime.txt',
    'stage24.32.1-pack1-multitouch-specialty-contract.txt',
    'stage24.32.1-pack1-multitouch-specialty-runtime.txt',
    'stage24.33.0-createcircle-lua-metadata-contract.txt',
    'stage24.34.0-pack1-yellow-boost-contract.txt',
    'stage24.34.0-pack1-yellow-boost-runtime.txt',
    'stage24.34.1-pack1-chapter1-closure-contract.txt',
    'stage24.34.1-pack1-chapter1-closure-runtime.txt',
    'stage24.35.0-pack2-bomb-contract.txt',
    'stage24.35.0-pack2-bomb-runtime.txt',
    'stage24.35.1-theme2-scene-metadata-contract.txt',
    'stage24.35.2-theme-ground-fill-contract.txt',
    'stage24.35.2-theme-ground-fill-runtime.txt',
    'stage24.36.0-pack2-white-contract.txt',
    'stage24.36.0-pack2-white-runtime.txt',
    'stage24.36.1-pack2-chapter2-closure-contract.txt',
    'stage24.36.1-pack2-chapter2-closure-runtime.txt',
    'stage24.37.0-renderstate-negative-scale-contract.txt',
    'stage24.37.0-renderstate-negative-scale-runtime.txt',
    'stage24.38.0-pack3-theme3-contract.txt',
    'stage24.38.0-pack3-theme3-runtime.txt',
    'stage24.38.1-pack3-chapter3-closure-contract.txt',
    'stage24.38.1-pack3-chapter3-closure-runtime.txt',
    'stage24.38.2-level-failed-menu-boot-regression-contract.txt',
    'stage24.38.2-level-failed-menu-boot-regression-runtime.txt',
    'stage24.39.0-mighty-hoax-theme4-contract.txt',
    'stage24.39.0-mighty-hoax-theme4-runtime.txt',
    'stage24.40.0-polygon-native-contract.txt',
    'stage24.40.0-polygon-native-runtime.txt',
    'stage24.40.1-mighty-hoax-4-10-contract.txt',
    'stage24.40.1-mighty-hoax-4-10-runtime.txt',
    'stage24.40.2-mighty-hoax-4-21-closure-contract.txt',
    'stage24.40.2-mighty-hoax-4-21-closure-runtime.txt',
    'stage24.41.0-checkforluafile-mighty-page2-contract.txt',
    'stage24.41.0-checkforluafile-mighty-page2-runtime.txt',
    'stage24.41.1-mighty-hoax-5-21-closure-contract.txt',
    'stage24.41.1-mighty-hoax-5-21-closure-runtime.txt',
    'stage24.42.0-danger-above-theme6-boomerang-contract.txt',
    'stage24.42.0-danger-above-theme6-boomerang-runtime.txt',
    'stage24.42.1-nonlegacy-bird-velocity-physics-audit-contract.txt',
    'stage24.42.1-nonlegacy-bird-velocity-physics-audit-runtime.txt',
    'stage24.43.0-joint-bounds-discovery-contract.txt',
    'stage24.43.0-joint-bounds-discovery-runtime.txt',
    'stage24.43.1-distance-joint-contract.txt',
    'stage24.43.1-distance-joint-runtime.txt',
    'stage24.44.0-box2d-maxtranslation-patch.txt',
    'stage24.44.0-bounds-lifecycle-ownership-contract.txt',
    'stage24.44.0-bounds-lifecycle-runtime.txt',
    'stage24.44.1-level-limit-update-consumer-contract.txt',
    'stage24.44.1-level-limit-runtime.txt',
    'stage24.44.2-level-limit-frozen-contract.txt',
    'stage24.44.2-level-limit-frozen-runtime.txt',
    'stage24.44.3-setgameon-android-contract.txt',
    'stage24.44.3-setgameon-android-runtime.txt',
    'stage24.45.0-danger-above-theme7-contract.txt',
    'stage24.45.0-danger-above-theme7-runtime.txt',
    'stage24.45.1-danger-above-theme8-contract.txt',
    'stage24.45.1-danger-above-theme8-runtime.txt',
    'stage24.46.0-big-setup-theme9-contract.txt',
    'stage24.46.0-big-setup-theme9-runtime.txt',
    'stage24.46.1-nonrepeat-background-contract.txt',
    'stage24.46.1-nonrepeat-background-runtime.txt',
    'stage24.46.2-big-setup-pack10-contract.txt',
    'stage24.46.2-big-setup-pack10-runtime.txt',
    'stage24.46.3-big-setup-pack11-contract.txt',
    'stage24.46.3-big-setup-pack11-runtime.txt',
    'stage24.47.0-golden-eggs-contract.txt',
    'stage24.47.0-golden-eggs-runtime.txt',
    'stage24.47.0a-golden-eggs-resource-root-contract.txt',
    'stage24.47.0a-golden-eggs-resource-root-runtime.txt',
    'stage24.47.1-rubber-physics-audit-contract.txt',
    'stage24.47.1-rubber-physics-audit-runtime.txt',
    'stage24.47.2-distance-joint-solver-native-audit.txt',
    'stage24.47.2-distance-joint-spring-audit-contract.txt',
    'stage24.47.2-distance-joint-spring-runtime.txt',
    'stage24.47.3-high-restitution-contact-solver-native-audit.txt',
    'stage24.47.3-high-restitution-contact-solver-audit-contract.txt',
    'stage24.47.3-high-restitution-contact-solver-runtime.txt',
    'stage24.47.4-rubber-warmstart-integration-native-audit.txt',
    'stage24.47.4-rubber-warmstart-integration-contract.txt',
    'stage24.47.4-rubber-warmstart-integration-runtime.txt',
    'stage24.47.5-fp-contraction-contract.txt',
    'stage24.47.5-fp-contraction-binary-audit.txt',
    'stage24.47.5-fp-contraction-order-runtime.txt',
    'stage24.47.6-native-jni-lifecycle-audit.txt',
    'stage24.47.6-android-lifecycle-contract.txt',
    'stage24.47.6-android-lifecycle-runtime.txt',
    'stage24.48.0-release-candidate-contract.txt',
    'stage24.48.0-apk-payload-audit.txt',
    'stage24.48.0-release-candidate-runtime.txt',
    'stage24.48.1-release-branding-contract.txt',
    'stage24.48.1-original-launcher-icon.txt',
    'stage24.48.1-apk-branding-audit.txt',
    'stage24.15.4-scene-dat-container.txt',
    'stage24.15.1-armv7-theme-native-contract.txt',
    'stage24.15.0-gameplay-scene-contract.txt',
    'stage24.14.5-original-mask-fidelity.txt',
    'stage24.14.2-armv7-maskedimage-full.txt',
    'stage24.14.1-armv7-maskedimage-render.txt'
)) {
    $p = Join-Path $out $name
    if (Test-Path $p) { $include.Add($p) }
}

# Stage24.31.5a tooling hotfix: a few runtime reports can be added both by
# their live-path variable and by the retained static/runtime filename list.
# Windows PowerShell Compress-Archive rejects duplicate path arguments, so
# canonicalize the bundle input once here instead of special-casing reports.
$uniqueInclude = @($include.ToArray() | Sort-Object -Unique)
Write-Host ("[stage24.31.5a] Diagnostic bundle input dedupe: {0} -> {1} unique paths" -f $include.Count, $uniqueInclude.Count)

if (Test-Path $bundle) { Remove-Item $bundle -Force }
Compress-Archive -Path $uniqueInclude -DestinationPath $bundle -CompressionLevel Optimal -Force

Write-Host ''
Write-Host '[stage24] Diagnostic bundle ready:'
Write-Host "  $bundle"
Write-Host '[stage24] Upload this ZIP to ChatGPT. No terminal paste needed.'
Write-Host ''

if ($Full) {
    Write-Host '--- stage24-summary.txt ---'
    Get-Content $summary | Write-Host
    Write-Host ''
    Write-Host 'Full raw logs remain inside the ZIP; they are intentionally not printed.'
}
