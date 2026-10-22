#!/usr/bin/env python3
"""Check development configuration without starting services or reading secrets."""

from pathlib import Path
import os
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text())
    for name, launcher in (
        ("node_repl", "mcp-node-repl"),
        ("1password", "mcp-1password"),
    ):
        server = config["mcp_servers"][name]
        script = ROOT / "scripts/dev" / launcher
        require(script.is_file() and os.access(script, os.X_OK),
                f"Missing executable launcher: {script}")
        expected = 'exec "$(git rev-parse --show-toplevel)/scripts/dev/' + launcher + '"'
        require(server["command"] == "sh" and server["args"] == ["-c", expected],
                f"{name} must launch from this checkout")
    require("webflow_hq" not in config["mcp_servers"], "HQ Webflow connection must stay in HQ")
    require(config["mcp_servers"]["1password"]["tools"]["authenticate"]["approval_mode"] == "approve",
            "Preserve the 1Password authentication approval policy")

    kata = tomllib.loads((ROOT / ".kata.toml").read_text())
    require(kata["project"]["name"] == "semantic-contracts-workshop", "Incorrect Kata project")
    require(os.access(ROOT / "scripts/dev/kata", os.X_OK), "Kata wrapper is not executable")

    docs = [ROOT / "AGENTS.md", ROOT / "docs/development-agent-setup.md"]
    docs.extend((ROOT / ".agents/references").glob("*.md"))
    for name in ("clarity", "1password-environments", "kata"):
        skill = ROOT / ".agents/skills" / name / "SKILL.md"
        text = skill.read_text()
        require(text.startswith("---\n"), f"Missing skill frontmatter: {name}")
        fields = text.split("---", 2)[1]
        require(re.search(r"^name: " + re.escape(name) + r"$", fields, re.M),
                f"Incorrect skill name: {name}")
        require(re.search(r"^description: .+", fields, re.M), f"Missing description: {name}")
        docs.append(skill)

    for doc in docs:
        require(doc.is_file(), f"Missing document: {doc}")
        for target in re.findall(r"\]\(([^\s)]+)\)", doc.read_text()):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            path = (doc.parent / target.split("#")[0]).resolve()
            require(path.is_relative_to(ROOT) and path.exists(),
                    f"Broken or nonportable link: {doc.relative_to(ROOT)} -> {target}")

    runtime = [ROOT / ".devcontainer.json", ROOT / "requirements.txt"]
    runtime.extend(ROOT.glob("docker-compose*.yml"))
    runtime.extend((ROOT / ".github/workflows").glob("*.yml"))
    runtime.extend((ROOT / "data_contract_components").rglob("*.py"))
    forbidden = (".agents/skills", "scripts/dev/", "WORKSHOP_NODE_REPL_BIN",
                 "WORKSHOP_1PASSWORD_MCP_BIN", "onthemarkdata/hq")
    for path in runtime:
        text = path.read_text()
        require(not any(marker in text for marker in forbidden),
                f"Developer-tool reference in participant/runtime file: {path.relative_to(ROOT)}")

    for directory in (ROOT / ".agents", ROOT / ".codex", ROOT / "scripts/dev"):
        for path in directory.rglob("*"):
            require(not path.is_symlink(), f"Nonportable symlink: {path}")
    print("PASS: config, skills, links, launchers, and participant configuration separation")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
