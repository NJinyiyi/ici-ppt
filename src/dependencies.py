from __future__ import annotations

import importlib.util
import os
import site
import subprocess
import sys


def ensure_dependencies(renderer: str = "auto", pptx_mode: str = "image", auto_install: bool = True, source_pdf: bool = False) -> None:
    """Install runtime dependencies into the current Python environment when missing."""
    if os.environ.get("ICI_PPT_AUTO_INSTALL", "").lower() in {"0", "false", "no"}:
        auto_install = False

    required_packages = {"pptx": "python-pptx"}
    if source_pdf:
        required_packages["pypdf"] = "pypdf"
    if pptx_mode in {"image", "hybrid"}:
        required_packages["PIL"] = "Pillow"
    if pptx_mode in {"image", "hybrid"} and renderer != "pil":
        required_packages["playwright"] = "playwright"

    missing = [pip_name for module, pip_name in required_packages.items() if importlib.util.find_spec(module) is None]
    if missing:
        if not auto_install:
            raise RuntimeError(
                "Missing dependencies: "
                + ", ".join(missing)
                + ". Install them with: python3 -m pip install --user "
                + " ".join(missing)
            )
        install_python_packages(missing)

    if pptx_mode in {"image", "hybrid"} and renderer != "pil":
        ensure_playwright_chromium(auto_install=auto_install)


def install_python_packages(packages: list[str]) -> None:
    print(f"ici-ppt: installing missing Python packages: {', '.join(packages)}")
    cmd = [sys.executable, "-m", "pip", "install", "--user", *packages]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        refresh_import_paths()
        return

    # Some Python installations reject --user. Fall back to the active environment.
    fallback = [sys.executable, "-m", "pip", "install", *packages]
    result = subprocess.run(fallback)
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to install Python dependencies. Run manually: "
            + sys.executable
            + " -m pip install "
            + " ".join(packages)
        )
    refresh_import_paths()


def refresh_import_paths() -> None:
    import importlib

    for path in {site.getusersitepackages(), *site.getsitepackages()}:
        if path and path not in sys.path:
            sys.path.append(path)
    importlib.invalidate_caches()


def ensure_playwright_chromium(auto_install: bool = True) -> None:
    try:
        import playwright  # noqa: F401
    except Exception as exc:
        raise RuntimeError("Playwright is not importable after installation.") from exc

    if not auto_install:
        return

    print("ici-ppt: ensuring Playwright Chromium is installed")
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to install Playwright Chromium. Run manually: "
            + sys.executable
            + " -m playwright install chromium"
        )
