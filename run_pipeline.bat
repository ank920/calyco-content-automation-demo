@echo off
REM ----------------------------
REM run_pipeline.bat (Windows)
REM Single-click pipeline for Calyco demo (uses python -m modules)
REM ----------------------------

echo -------------------------------------------------------
echo Activating venv...
echo -------------------------------------------------------
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: venv not found at venv\Scripts\activate.bat
    echo Create/activate your venv first: python -m venv venv
    pause
    exit /b 1
)

REM Load .env file (if present) into environment variables
if exist .env (
    echo Loading .env...
    for /f "usebackq tokens=1* delims==" %%A in (".env") do (
        if not "%%A"=="" (
            set "%%A=%%B"
        )
    )
) else (
    echo No .env file found (ok if you run in manual mode).
)

REM Default mode (can be overridden by .env)
if "%CONTENT_MODE%"=="" set CONTENT_MODE=api
if "%CONTENT_PROVIDER%"=="" set CONTENT_PROVIDER=GROQ

echo CONTENT_MODE=%CONTENT_MODE%
echo CONTENT_PROVIDER=%CONTENT_PROVIDER%
echo.

REM ----------------------------
echo -----------------------------------
echo 1) PyTrends scraper (programmatic trends)
echo -----------------------------------
python -m scrapers.trends_pytrends
if errorlevel 1 goto :err

echo -----------------------------------
echo 2) Selenium Trends snapshot (proof of Selenium scraper)
echo -----------------------------------
python -m scrapers.trends_selenium
if errorlevel 1 goto :err

echo -----------------------------------
echo 3) Competitor scraper (sites)
echo -----------------------------------
python -m scrapers.competitor_scraper
if errorlevel 1 goto :err

echo -----------------------------------
echo 4) Social scraper (public social pages)
echo -----------------------------------
python -m scrapers.social_scraper
if errorlevel 1 goto :err

echo -----------------------------------
echo 5) Download competitor creatives (images)
echo -----------------------------------
python -m scripts.download_competitor_images
if errorlevel 1 goto :err

echo -----------------------------------
echo 6) Generate placeholder images (if image API not used)
echo -----------------------------------
python -m scripts.generate_placeholder_images
if errorlevel 1 goto :err

echo -----------------------------------
echo 7) Ensure prompts exist for reproducibility
echo -----------------------------------
python -m scripts.write_prompts
if errorlevel 1 goto :err

echo -----------------------------------
echo 8) Build unified context.json
echo -----------------------------------
python -m pipeline.process_data
if errorlevel 1 goto :err

echo -----------------------------------
echo 9) Generate content (LLM/API or manual postprocess)
echo -----------------------------------
REM generate_content will read CONTENT_MODE from env (.env or set above)
python -m pipeline.generate_content
if errorlevel 1 goto :err

echo -----------------------------------
echo 10) Validate outputs (brand rules)
echo -----------------------------------
python -m pipeline.rules
if errorlevel 1 goto :err

echo -----------------------------------
echo 11) Write run summary (pipeline.run_summary)
echo -----------------------------------
python -m pipeline.run_summary
if errorlevel 1 goto :err

echo -----------------------------------
echo Pipeline finished. All outputs are in the outputs\ folder.
echo Please check outputs\blog, outputs\mdx, outputs\social, outputs\ads, outputs\seo, outputs\llm_results, outputs\competitors
echo.
pause
exit /b 0

:err
echo.
echo !!! Pipeline failed at the previous step. Check console output above.
echo The run_summary (if written) and validation_report will be in outputs\logs\
pause
exit /b 2
