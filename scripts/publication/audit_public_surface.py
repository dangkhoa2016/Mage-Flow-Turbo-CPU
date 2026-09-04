from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_MODEL_WEIGHT_EXTENSIONS = {".gguf", ".safetensors", ".ckpt", ".pt", ".pth", ".onnx", ".bin"}
_FORBIDDEN_INTERNAL_TERMS = re.compile(
    r"(?i)\b(phase[- ]?[0-9a-z]+|corrective|forensic|opencode|codex-reconstruction|reconstruction-plan)\b"
)

_POSITIVE_QUALIFICATION_CLAIMS = re.compile(
    r"(?i)(qualified-success|\*\*qualified\*\*|\bqualified integration\b|—\s*qualified\.|\(\s*qualified\s*\)|\bqualified backends\s*=|\bđã qualification\b|\btích hợp đã qualification\b)"
)

_README_REQUIRED = [
    "Mage-Flow-Turbo-Native-Inference",
    "stable-diffusion.cpp",
    "Q8_0",
    "Q4_K_M",
    "CPU",
    "CUDA",
    "Kaggle",
]
_V7_ACTIONS = {
    "actions/checkout",
    "actions/setup-python",
    "actions/upload-artifact",
    "actions/download-artifact",
    "actions/cache",
    "actions/setup-node",
}
# Private implementation/evidence dirs that are not part of the public product surface.
_PRIVATE_DIRS = {".git", "evidence"}


def _iter_public_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in _PRIVATE_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def audit(root: Path) -> list[str]:
    errors: list[str] = []

    core_root = root / "mageflow_native"
    if core_root.is_dir():
        text = "\n".join(
            p.read_text(encoding="utf-8", errors="ignore")
            for p in core_root.rglob("*.py")
        )
        if "/kaggle/input" in text or "/kaggle/working" in text:
            errors.append("core package contains hard-coded Kaggle path")

    for p in _iter_public_files(root):
        if p.suffix in _MODEL_WEIGHT_EXTENSIONS:
            errors.append(f"model weight file tracked: {p}")

    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        for needle in _README_REQUIRED:
            if needle not in text:
                errors.append(f"README missing required term: {needle}")
        if "Mage-Flow-Turbo-CPU" in text:
            errors.append("README still references old product identity Mage-Flow-Turbo-CPU")
    else:
        errors.append("README.md missing")

    provenance = root / "runtime" / "RUNTIME-PROVENANCE.json"
    if provenance.is_file():
        try:
            prov = json.loads(provenance.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"runtime provenance JSON invalid: {exc}")
        else:
            states = prov.get("qualification_state", {})
            qualified_backends = prov.get("qualified_backends", [])
            if not isinstance(states, dict):
                errors.append("runtime provenance qualification_state must be an object")
            else:
                pending = [name for name, status in states.items() if status != "qualified"]
                if pending and qualified_backends:
                    errors.append("qualified_backends must be empty while qualification_state contains pending targets")
                if pending:
                    claim_files = [root / "README.md", root / "README.vi.md", root / "CHANGELOG.md", root / "CHANGELOG.vi.md"]
                    docs_dir = root / "docs"
                    if docs_dir.is_dir():
                        claim_files.extend(sorted(docs_dir.glob("*.md")))
                    for claim_file in claim_files:
                        if not claim_file.is_file():
                            continue
                        text = claim_file.read_text(encoding="utf-8", errors="ignore")
                        match = _POSITIVE_QUALIFICATION_CLAIMS.search(text)
                        if match:
                            errors.append(
                                f"qualification claim contradicts pending evidence state in {claim_file.relative_to(root)}: {match.group(0)}"
                            )

    for p in _iter_public_files(root):
        if p.suffix not in (".md", ".py", ".yml", ".yaml", ".sh", ".json", ".txt", ".toml"):
            continue
        # The publication tooling itself legitimately names the internal terms it
        # must reject; exclude it from the self-scan.
        if p.is_relative_to(root / "scripts" / "publication"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = _FORBIDDEN_INTERNAL_TERMS.search(text)
        if m:
            errors.append(f"internal term in {p}: {m.group(0)}")

    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for wf in workflows.glob("*.yml"):
            text = wf.read_text(encoding="utf-8")
            for action in re.findall(r"uses:\s*(\S+)", text):
                action_name = action.split("@")[0]
                if action_name in _V7_ACTIONS:
                    tag = action.split("@")[-1]
                    if not tag.startswith("v7"):
                        errors.append(f"{wf.name} uses non-v7 action {action}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    errors = audit(Path(args.root))
    if errors:
        print("PUBLICATION_SURFACE_AUDIT=FAIL")
        for e in errors:
            print("  - " + e)
        return 1
    print("PUBLICATION_SURFACE_AUDIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
