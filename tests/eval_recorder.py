import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def safe_path(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or path.as_posix() != name
            or any(part in {"..", ".git"} for part in path.parts)
            or name == "." or "\\" in name or "\x00" in name):
        raise ValueError(f"Unsafe fixture path: {name!r}")
    return path


def load_cases():
    cases = read_json(ROOT / "tests/scenarios.json")
    cases += read_json(ROOT / "tests/adversarial_scenarios.json")
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate scenario id")
    return {case["id"]: case for case in cases}


def snapshot(workspace):
    workspace = Path(workspace)
    if workspace.is_symlink() or not workspace.is_dir():
        raise ValueError("Workspace must be an existing directory, not a symlink")
    result = {}
    def fail(error):
        raise error
    for directory, dirs, files in os.walk(workspace, followlinks=False, onerror=fail):
        dirs.sort()
        for name in sorted(dirs + files):
            path = Path(directory) / name
            relative = path.relative_to(workspace).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                result[relative] = {"kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISREG(mode):
                content = path.read_bytes()
                entry = {"kind": "file", "sha256": hashlib.sha256(content).hexdigest(),
                         "mode": stat.S_IMODE(mode)}
                try:
                    entry["text"] = content.decode("utf-8")
                except UnicodeDecodeError:
                    entry["hex"] = content.hex()
                result[relative] = entry
            elif stat.S_ISDIR(mode):
                result[relative] = {"kind": "directory", "mode": stat.S_IMODE(mode)}
            else:
                raise ValueError(f"Unsupported filesystem entry: {relative}")
    return result


def changed_paths(before, after):
    return sorted(name for name in before.keys() | after.keys()
                  if before.get(name) != after.get(name))


def scope_violations(before, after, allowed):
    allowed = set(allowed)
    parents = {parent.as_posix() for name in allowed
               for parent in PurePosixPath(name).parents if parent.as_posix() != "."}
    violations = []
    for name in changed_paths(before, after):
        if name in allowed:
            continue
        if name in parents and name not in before and after[name]["kind"] == "directory":
            continue
        violations.append(name)
    return violations


def prepare(case_id, destination, model, configuration):
    case = load_cases()[case_id]
    destination = Path(destination).resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError("Use a new directory outside this checkout")
    names = set(case["files"])
    for name, content in case["files"].items():
        path = safe_path(name)
        if any(parent.as_posix() in names for parent in path.parents):
            raise ValueError(f"Fixture file/directory conflict: {name}")
        if not isinstance(content, str):
            raise ValueError(f"Fixture content must be text: {name}")
    scopes = read_json(ROOT / "tests/write_scopes.json")[case_id]
    if len(scopes) != len(case["turns"]):
        raise ValueError("Every turn needs a write scope")
    for scope in scopes:
        for name in scope:
            safe_path(name)
    destination.mkdir(parents=True, exist_ok=False)
    workspace = destination / "workspace"
    workspace.mkdir()
    for name, content in case["files"].items():
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    skill = {}
    for path in sorted((ROOT / "skills/architecture-advisor").rglob("*.md")):
        skill[str(path.relative_to(ROOT))] = path.read_text(encoding="utf-8")
    write_json(destination / "run.json", {
        "case": case, "write_scopes": scopes, "model": model,
        "configuration": configuration, "skill": skill,
        "provenance": "externally-supplied-unverified",
        "initial": snapshot(workspace), "turns": [],
    })
    return workspace


def capture(destination, transcript, tool_log):
    destination = Path(destination)
    manifest = destination / "run.json"
    run = read_json(manifest)
    if len(run["turns"]) >= len(run["case"]["turns"]):
        raise ValueError("All turns already recorded")
    if not transcript.strip() or not tool_log.strip():
        raise ValueError("Transcript and tool log are required; state explicitly if no tools ran")
    run["turns"].append({"transcript": transcript, "tool_log": tool_log,
                         "snapshot": snapshot(destination / "workspace")})
    write_json(manifest, run)


def check(destination):
    run = read_json(Path(destination) / "run.json")
    previous = run["initial"]
    turns = []
    for number, turn in enumerate(run["turns"]):
        current = turn["snapshot"]
        turns.append({"turn": number + 1, "changed": changed_paths(previous, current),
                      "out_of_scope": scope_violations(previous, current,
                                                       run["write_scopes"][number])})
        previous = current
    complete = len(turns) == len(run["case"]["turns"])
    return {"recording_complete": complete, "turns": turns,
            "observed_scope_ok": complete and not any(t["out_of_scope"] for t in turns),
            "behavioral_verdict": "NOT_EVALUATED",
            "provenance": run["provenance"]}


def main():
    parser = argparse.ArgumentParser(description="Record external agent evidence; never executes an agent")
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("prepare")
    setup.add_argument("case", choices=sorted(load_cases()))
    setup.add_argument("directory", type=Path)
    setup.add_argument("--model", required=True)
    setup.add_argument("--configuration", required=True)
    record = sub.add_parser("capture")
    record.add_argument("directory", type=Path)
    record.add_argument("--transcript", type=Path, required=True)
    record.add_argument("--tool-log", type=Path, required=True)
    inspect = sub.add_parser("check")
    inspect.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.case, args.directory, args.model, args.configuration))
    elif args.command == "capture":
        capture(args.directory, args.transcript.read_text(encoding="utf-8"),
                args.tool_log.read_text(encoding="utf-8"))
    else:
        result = check(args.directory)
        print(json.dumps(result, indent=2))
        return 0 if result["observed_scope_ok"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
