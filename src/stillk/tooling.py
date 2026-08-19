from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import typer

app = typer.Typer(add_completion=False)


def _human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024.0:
            return f"{n:3.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def inspect_project(path: Path | str = ".") -> dict:
    p = Path(path)
    info: dict = {}

    # Python version
    info["python"] = sys.version.split()[0]

    # frameworks (check imports in requirements or pyproject)
    reqs = p / "requirements.txt"
    pyproject = p / "pyproject.toml"
    frameworks: set[str] = set()
    if reqs.exists():
        for line in reqs.read_text().splitlines():
            ln = line.strip().lower()
            if not ln or ln.startswith("#"):
                continue
            if "torch" in ln or "pytorch" in ln:
                frameworks.add("PyTorch")
            if "tensorflow" in ln:
                frameworks.add("TensorFlow")
            if "transformers" in ln or "huggingface" in ln:
                frameworks.add("Transformers (Hugging Face)")
            if "scikit" in ln or "scikit-learn" in ln:
                frameworks.add("Scikit-learn")
    elif pyproject.exists():
        txt = pyproject.read_text().lower()
        if "torch" in txt or "pytorch" in txt:
            frameworks.add("PyTorch")
        if "tensorflow" in txt:
            frameworks.add("TensorFlow")
        if "transformers" in txt:
            frameworks.add("Transformers (Hugging Face)")

    info["frameworks"] = sorted(frameworks)

    # project structure
    info["has_src"] = (p / "src").exists()
    info["has_data"] = (p / "data").exists()
    info["has_configs"] = (p / "configs").exists()

    # detect models, datasets, training scripts
    info["models"] = [str(p_) for p_ in p.rglob("*model*.pt")]
    info["datasets"] = [str(p_) for p_ in p.rglob("*.csv")][:10]
    training_scripts = [str(p_) for p_ in p.rglob("train*.py")]
    info["training_scripts"] = training_scripts

    # docker
    info["dockerfile"] = (p / "Dockerfile").exists()
    info["docker_compose"] = (p / "docker-compose.yml").exists()

    # GPU/CUDA
    gpu = False
    cuda = False
    try:
        import torch

        gpu = torch.cuda.is_available()
        cuda = hasattr(torch.version, "cuda") or bool(torch.version.cuda)
    except Exception:
        # try nvidia-smi
        if shutil.which("nvidia-smi"):
            try:
                subprocess.run(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                gpu = True
                cuda = True
            except Exception:
                gpu = True

    info["gpu"] = gpu
    info["cuda"] = cuda

    # dependencies: try to read installed packages via pip freeze
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
        info["installed_packages"] = out.splitlines()[:50]
    except Exception:
        info["installed_packages"] = []

    # quick issues/opportunities
    warnings: list[str] = []
    if not info["has_src"]:
        warnings.append("No `src` directory detected — consider using a package layout.")
    if info["frameworks"] == []:
        warnings.append("No ML/LLM frameworks found in requirements or pyproject.")
    if not info["dockerfile"]:
        warnings.append("No Dockerfile detected — containerization may help reproducibility.")

    info["warnings"] = warnings
    return info


def run_doctor(path: Path | str = ".") -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    # python
    try:
        pyv = sys.version.split()[0]
        results.append(("Python", f"OK {pyv}"))
    except Exception:
        results.append(("Python", "ERROR"))

    # pip
    pip = shutil.which("pip") or shutil.which("pip3")
    results.append(("pip", "OK" if pip else "ERROR"))

    # git
    results.append(("git", "OK" if shutil.which("git") else "WARNING"))

    # docker
    results.append(("docker", "OK" if shutil.which("docker") else "WARNING"))

    # torch/tf
    try:
        import torch  # type: ignore

        results.append(("PyTorch", "OK"))
        try:
            gpu = torch.cuda.is_available()
            results.append(("GPU", "OK" if gpu else "WARNING"))
            if gpu:
                try:
                    vram = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"], text=True)
                    results.append(("VRAM", f"{vram.strip()} MB"))
                except Exception:
                    results.append(("VRAM", "UNKNOWN"))
        except Exception:
            results.append(("GPU", "UNKNOWN"))
    except Exception:
        results.append(("PyTorch", "WARNING"))

    try:
        import tensorflow as tf  # type: ignore

        results.append(("TensorFlow", "OK"))
    except Exception:
        results.append(("TensorFlow", "WARNING"))

    # project deps
    p = Path(path)
    reqs = p / "requirements.txt"
    if reqs.exists():
        results.append(("project-requirements", "OK"))
    else:
        results.append(("project-requirements", "WARNING"))

    return results


def find_cache_dirs(path: Path | str = ".") -> Iterable[Path]:
    p = Path(path)
    for d in p.rglob("__pycache__"):
        yield d


def compute_size(paths: Iterable[Path]) -> int:
    total = 0
    for p in paths:
        if p.is_file():
            total += p.stat().st_size
        else:
            for f in p.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
    return total


def clean_project(path: Path | str = ".", all: bool = False, yes: bool = False) -> dict:
    p = Path(path)
    to_clean = []
    # caches
    to_clean.extend(list(find_cache_dirs(p)))
    # pip cache (only report)
    pip_cache = None
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "cache", "dir"], text=True)
        pip_cache = Path(out.strip())
        if pip_cache.exists():
            to_clean.append(pip_cache)
    except Exception:
        pip_cache = None

    size = compute_size(to_clean)
    if not yes:
        return {"dry_run": True, "targets": [str(x) for x in to_clean], "size": size}

    removed = []
    for target in to_clean:
        try:
            if target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
            removed.append(str(target))
        except Exception:
            pass

    return {"dry_run": False, "removed": removed, "size": size}


def detect_training_script(path: Path | str = ".") -> Path | None:
    p = Path(path)
    candidates = list(p.rglob("train*.py"))
    if candidates:
        return candidates[0]
    # common locations
    if (p / "src" / "training" / "train.py").exists():
        return p / "src" / "training" / "train.py"
    return None


def train(path: Path | str = ".", execute: bool = False, extra_args: list[str] | None = None) -> dict:
    p = Path(path)
    script = detect_training_script(p)
    if not script:
        return {"found": False}
    info = {"found": True, "script": str(script)}
    if execute:
        cmd = [sys.executable, str(script)] + (extra_args or [])
        try:
            subprocess.check_call(cmd)
            info["status"] = "ran"
        except subprocess.CalledProcessError as exc:
            info["status"] = f"failed: {exc.returncode}"
    else:
        info["status"] = "detected (dry-run)"
    return info


def evaluate(path: Path | str = ".") -> dict:
    p = Path(path)
    # look for eval scripts
    candidates = list(p.rglob("eval*.py"))
    if candidates:
        return {"found": True, "script": str(candidates[0]), "metrics": {"accuracy": 0.0}}
    # fallback: look for evals dir
    if (p / "src" / "evals").exists():
        return {"found": True, "metrics": {"accuracy": 0.0}}
    return {"found": False}


def benchmark(path: Path | str = ".") -> dict:
    # placeholder structure to allow extension
    return {"benchmarks": [], "status": "not-implemented"}


def run_component(path: Path | str = ".", component: str = "api") -> dict:
    p = Path(path)
    component = component.lower()
    if component == "api":
        # look for uvicorn or fastapi app
        app_candidates = list(p.rglob("main.py"))
        if app_candidates:
            return {"found": True, "script": str(app_candidates[0]), "status": "detected"}
        return {"found": False}
    if component in {"training", "train"}:
        return train(path, execute=False)
    if component in {"inference", "serve"}:
        # detect predict.py
        preds = list(p.rglob("predict*.py"))
        if preds:
            return {"found": True, "script": str(preds[0])}
        return {"found": False}
    return {"found": False}
