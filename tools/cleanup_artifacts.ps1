# cleanup_artifacts.ps1
# TestFlowManager 项目清理脚本
# 清理构建产物、IDE 文件和过时代码

$ErrorActionPreference = "Continue"

Write-Host "=== TestFlowManager 项目清理 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 从 git 跟踪中移除目录
Write-Host "[1/7] 从 Git 跟踪中移除构建产物..." -ForegroundColor Yellow
$tracked_dirs = @('build', 'dist', 'logs', '.idea', '.ipynb_checkpoints')
foreach ($dir in $tracked_dirs) {
    if (Test-Path $dir) {
        Write-Host "  处理: $dir" 
        git rm -r --cached $dir 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ 已从 Git 跟踪移除" -ForegroundColor Green
        } else {
            Write-Host "    ℹ 可能未被跟踪或已移除" -ForegroundColor Gray
        }
    }
}

# 2. 删除构建产物
Write-Host "`n[2/7] 删除构建产物..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "  ✓ 已删除: build/" -ForegroundColor Green
}

if (Test-Path "dist") {
    $exe_files = Get-ChildItem "dist" -Filter "*.exe" -ErrorAction SilentlyContinue
    foreach ($file in $exe_files) {
        Remove-Item $file.FullName -Force
        Write-Host "  ✓ 已删除: dist/$($file.Name)" -ForegroundColor Green
    }
    
    $dirs_to_remove = @('Backup', 'Projects', 'Temp', 'Template', 'config', 'logs', 'resources')
    foreach ($dir_name in $dirs_to_remove) {
        $full_path = Join-Path "dist" $dir_name
        if (Test-Path $full_path) {
            Remove-Item -Recurse -Force $full_path
            Write-Host "  ✓ 已删除: dist/$dir_name" -ForegroundColor Green
        }
    }
    
    @('start.bat', 'README.txt') | ForEach-Object {
        $file = Join-Path "dist" $_
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "  ✓ 已删除: dist/$_" -ForegroundColor Green
        }
    }
}

# 3. 删除 IDE 配置
Write-Host "`n[3/7] 删除 IDE 配置..." -ForegroundColor Yellow
if (Test-Path ".idea") {
    Remove-Item -Recurse -Force ".idea"
    Write-Host "  ✓ 已删除: .idea/" -ForegroundColor Green
}

# 4. 删除日志和缓存
Write-Host "`n[4/7] 删除日志和缓存..." -ForegroundColor Yellow

$pycache_count = 0
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Recurse -Force $_.FullName
    $pycache_count++
}
Write-Host "  ✓ 已清理 $pycache_count 个 __pycache__ 目录" -ForegroundColor Green

$pyc_count = 0
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Force $_.FullName
    $pyc_count++
}
Write-Host "  ✓ 已清理 $pyc_count 个 .pyc 文件" -ForegroundColor Green

@('logs\testflow.log', 'tests\testflow.log') | ForEach-Object {
    if (Test-Path $_) {
        Remove-Item $_ -Force
        Write-Host "  ✓ 已删除: $_" -ForegroundColor Green
    }
}

if (Test-Path ".ipynb_checkpoints") {
    Remove-Item -Recurse -Force ".ipynb_checkpoints"
    Write-Host "  ✓ 已删除: .ipynb_checkpoints/" -ForegroundColor Green
}

# 5. 归档过时测试和工具
Write-Host "`n[5/7] 归档过时文件..." -ForegroundColor Yellow

$archive_dir = "tests\archive"
if (-not (Test-Path $archive_dir)) {
    New-Item -ItemType Directory -Path $archive_dir | Out-Null
}

$old_tests = @('test_simple.py', 'wordform.py')
foreach ($file in $old_tests) {
    $src = "tests\$file"
    if (Test-Path $src) {
        Move-Item $src "$archive_dir\$file" -Force
        Write-Host "  ✓ 已归档: tests/$file -> tests/archive/" -ForegroundColor Green
    }
}

$tools_archive = "tools\archive"
if (-not (Test-Path $tools_archive)) {
    New-Item -ItemType Directory -Path $tools_archive | Out-Null
}

$old_tools = @('measure_startup.py', 'simple_startup_test.py')
foreach ($file in $old_tools) {
    $src = "tools\$file"
    if (Test-Path $src) {
        Move-Item $src "$tools_archive\$file" -Force
        Write-Host "  ✓ 已归档: tools/$file -> tools/archive/" -ForegroundColor Green
    }
}

# 6. 更新 Git 跟踪
Write-Host "`n[6/7] 更新 Git 跟踪..." -ForegroundColor Yellow

git rm tests/test_simple.py tests/wordform.py tools/measure_startup.py tools/simple_startup_test.py 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 已从 Git 移除过时文件" -ForegroundColor Green
}

git add tests/archive/ tools/archive/ 2>$null
Write-Host "  ✓ 已添加归档文件到 Git" -ForegroundColor Green

# 7. 最终状态
Write-Host "`n[7/7] 清理完成!" -ForegroundColor Green
Write-Host ""
Write-Host "=== 清理总结 ===" -ForegroundColor Cyan
Write-Host "✓ 构建产物已清理 (build/, dist/*.exe)" -ForegroundColor White
Write-Host "✓ IDE 配置已删除 (.idea/)" -ForegroundColor White
Write-Host "✓ Python 缓存已清理 (__pycache__, *.pyc)" -ForegroundColor White
Write-Host "✓ 日志文件已删除" -ForegroundColor White
Write-Host "✓ 过时文件已归档到 tests/archive/ 和 tools/archive/" -ForegroundColor White
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 运行 'git status' 查看变更" -ForegroundColor White
Write-Host "  2. 确认无误后提交: git commit -m 'chore: clean build artifacts and archive obsolete files'" -ForegroundColor White
Write-Host "  3. 运行 guard tests 验证: .\tools\run_phase14_guard_regression.ps1" -ForegroundColor White
Write-Host ""
