@echo off
echo Cleaning outputs folder...

REM ========= DELETE SIMPLE SUBFOLDERS CONTENT =========
for %%d in (
    "ads"
    "blog"
    "mdx"
    "seo"
    "social"
    "llm_results"
    "logs"
    "prompts"
    "images"
) do (
    if exist outputs\%%d (
        echo Clearing outputs\%%d ...
        del /q outputs\%%d\* 2>nul
        for /d %%x in ("outputs\%%d\*") do rmdir /s /q "%%~x"
    )
)

REM ========= DELETE EVERYTHING INSIDE competitors =========
echo Clearing outputs\competitors ...
if exist outputs\competitors (
    for /d %%x in ("outputs\competitors\*") do (
        echo Deleting folder: %%x
        rmdir /s /q "%%x"
    )
    del /q outputs\competitors\* 2>nul
)

REM ========= DELETE TOP LEVEL JSON FILES =========
del /q outputs\context.json 2>nul
del /q outputs\trends.json 2>nul

echo Done!
pause
