import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/architecture-advisor/SKILL.md"


def table_rows(text: str, header: str) -> list[list[str]]:
    body = text.split(header + "\n", 1)[1].splitlines()[1:]
    rows = []
    for line in body:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header.strip("|").split("|")):
            raise ValueError(f"Malformed table row: {line}")
        rows.append(cells)
    if not rows:
        raise ValueError(f"Empty table: {header}")
    return rows


def read_catalogue(text: str) -> tuple[
    dict[tuple[str, str], tuple[str, str]],
    dict[str, str],
    dict[str, int],
    dict[tuple[str, str], int | None],
]:
    tags = dict(re.findall(r"^- ([A-J])\).*\(`([a-z_]+)`\)$", text, re.M))
    points = {}
    for signal, value in table_rows(text, "| Signal | Points |"):
        question = re.search(r"Q[1-6]", signal)
        key = question[0] if question else "avoid"
        points[key] = int(re.match(r"[+−-]\d+", value)[0].replace("−", "-"))
    catalogue = {}
    thresholds = {}
    dimension = ""
    for group, name, fit, avoid, threshold in table_rows(
        text, "| Dimension | Candidate | Best-fit signals | Avoid when | Optional threshold |"
    ):
        dimension = group.strip("*") or dimension
        if (dimension, name) in catalogue:
            raise ValueError(f"Duplicate candidate: {dimension} / {name}")
        catalogue[dimension, name] = (fit, avoid)
        thresholds[dimension, name] = (
            None if threshold == "—" else int(re.fullmatch(r"(\d+)/6", threshold)[1])
        )
    return catalogue, tags, points, thresholds


def parse_signal(signal: str, tags: dict[str, str]) -> tuple[str, set[str], bool]:
    match = re.fullmatch(
        r"(Q[1-6]):(?:`([a-z_]+)`|([A-K])(?:-([A-K]))?)( not confirmed)?",
        signal,
    )
    if match is None:
        raise ValueError(f"Unsupported catalogue signal: {signal}")
    question, tag, start, end, absent = match.groups()
    if tag:
        if question != "Q6":
            raise ValueError(f"Tag outside Q6: {signal}")
        start = {value: key for key, value in tags.items()}[tag]
    if absent and question != "Q6":
        raise ValueError(f"Confirmation outside Q6: {signal}")
    if end and end < start:
        raise ValueError(f"Reversed range: {signal}")
    choices = {chr(code) for code in range(ord(start), ord(end or start) + 1)}
    return question, choices, bool(absent)


def matches(signal: str, answers: dict[str, str], tags: dict[str, str]) -> bool:
    question, choices, absent = parse_signal(signal, tags)
    selected = set(answers[question].split("/")) - {"-"}
    overlap = bool(choices & selected)
    return not overlap if absent else overlap


def score(
    candidate: tuple[str, str],
    answers: dict[str, str],
    tags: dict[str, str],
    points: dict[str, int],
) -> int:
    fit, avoid = candidate
    matched = set()
    if fit != "Default; no score required":
        for signal in fit.split(", "):
            if matches(signal, answers, tags):
                matched.add(parse_signal(signal, tags)[0])
    penalty = avoid != "No avoid condition" and any(
        all(matches(signal, answers, tags) for signal in condition.split(" + "))
        for condition in avoid.split(", ")
    )
    return sum(points[question] for question in matched) + points["avoid"] * penalty


class SkillContractTests(unittest.TestCase):
    def test_optional_thresholds_are_explicit_and_reachable(self):
        text = SKILL.read_text(encoding="utf-8")
        catalogue, tags, points, thresholds = read_catalogue(text)
        expected = {
            ("Domain model", "Screaming Architecture"): 2,
            ("Domain model", "DDD"): 3,
            ("Presentation pattern", "MVC / MVP / MVVM"): 2,
            ("Data and integration", "CQRS"): 2,
            ("Data and integration", "Event-Driven / EDA"): 3,
            ("Data and integration", "Pipeline / Pipes & Filters"): 1,
            ("Runtime model", "Serverless"): 2,
        }
        actual = {key: value for key, value in thresholds.items() if value is not None}
        self.assertEqual(actual, expected)
        for (dimension, name), (fit, _) in catalogue.items():
            threshold = thresholds[dimension, name]
            if threshold is None:
                continue
            questions = {parse_signal(signal, tags)[0] for signal in fit.split(", ")}
            upper_bound = sum(points[question] for question in questions)
            with self.subTest(dimension=dimension, candidate=name):
                self.assertGreaterEqual(
                    upper_bound,
                    threshold,
                    f"{name} can score at most {upper_bound}, but requires {threshold}; "
                    "the published rules can never select this candidate",
                )

    def test_reference_cases_match_hand_checked_scores(self):
        catalogue, tags, points, _ = read_catalogue(SKILL.read_text(encoding="utf-8"))
        cases = (ROOT / "tests/cases.md").read_text(encoding="utf-8")
        rows = table_rows(
            cases,
            "| Case | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Dimension | Candidate | Score | Reason |",
        )
        covered = set()
        names = set()
        for case, *values in rows:
            answers = dict(zip((f"Q{i}" for i in range(1, 7)), values[:6]))
            dimension, name, expected, reason = values[6:]
            with self.subTest(case=case):
                self.assertNotIn(case, names)
                names.add(case)
                covered.add((dimension, name))
                self.assertTrue(reason)
                self.assertEqual(
                    score(catalogue[dimension, name], answers, tags, points),
                    int(expected),
                )
        self.assertEqual(covered, set(catalogue), "Every candidate needs a reference case")

    def test_rubric_caps_match_its_point_budget(self):
        text = SKILL.read_text(encoding="utf-8")
        _, _, points, _ = read_catalogue(text)
        self.assertEqual(set(points), {"Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "avoid"})
        maximum = int(re.search(r"Maximum: (\d+) points", text)[1])
        self.assertEqual(sum(value for value in points.values() if value > 0), maximum)
        for signal, value in table_rows(text, "| Signal | Points |"):
            if "Q6" in signal or "Any answer" in signal:
                cap = re.search(r"cap: ([+−-]\d+) per pattern total", value)
                self.assertIsNotNone(cap, f"Missing total cap: {signal}")
                key = "Q6" if "Q6" in signal else "avoid"
                self.assertEqual(int(cap[1].replace("−", "-")), points[key])

    def test_catalogue_signals_reference_existing_quiz_choices(self):
        text = SKILL.read_text(encoding="utf-8")
        catalogue, tags, _, _ = read_catalogue(text)
        sections = re.split(r"^\*\*(Q[1-6]) —", text, flags=re.M)
        options = {
            question: set(re.findall(r"^- ([A-K])\)", body, re.M))
            for question, body in zip(sections[1::2], sections[2::2])
        }
        self.assertEqual(set(tags), options["Q6"] - {"K"})
        self.assertEqual(len(tags), len(set(tags.values())))
        for (dimension, name), conditions in catalogue.items():
            for expression in conditions:
                if expression in {"Default; no score required", "No avoid condition"}:
                    continue
                for signal in re.split(r", | \+ ", expression):
                    with self.subTest(dimension=dimension, candidate=name, signal=signal):
                        question, choices, _ = parse_signal(signal, tags)
                        self.assertTrue(choices <= options[question])

    def test_named_patterns_have_dependency_and_placement_rules(self):
        text = SKILL.read_text(encoding="utf-8")
        paths = set(re.findall(r"`(references/[^`]+\.md)`", text))
        self.assertTrue(paths, "No rule references found")
        for path in paths:
            self.assertTrue((SKILL.parent / path).is_file(), f"Missing reference: {path}")
        rules = (SKILL.parent / "references/enforceable-rules.md").read_text(encoding="utf-8")
        sections = re.split(r"^## (.+)\n", rules, flags=re.M)
        rules_by_name = dict(zip(sections[1::2], sections[2::2]))
        catalogue, _, _, _ = read_catalogue(text)
        for _, name in catalogue:
            if name.endswith("(default)"):
                continue
            with self.subTest(candidate=name):
                heading = "DDD (Domain-Driven Design)" if name == "DDD" else name
                self.assertIn(heading, rules_by_name)
                self.assertIn("**Dependency rules**", rules_by_name[heading])
                self.assertIn("**Placement rules**", rules_by_name[heading])

    def test_published_scoreboard_matches_its_answers(self):
        text = SKILL.read_text(encoding="utf-8")
        catalogue, tags, points, _ = read_catalogue(text)
        example = re.search(r"Example output for `([^`]+)`", text)[1]
        answers = dict(re.findall(r"(Q[1-6]):([A-K/]+)", example))
        maximum = int(re.search(r"Maximum: (\d+) points", text)[1])
        aliases = {
            "Single deployable": "Single deployable (default)",
            "Hexagonal": "Hexagonal / Ports & Adapters",
            "EDA": "Event-Driven / EDA",
            "Screaming": "Screaming Architecture",
            "MVC": "MVC / MVP / MVVM",
            "Conventional runtime": "Conventional runtime (default)",
        }
        rows = table_rows(text, "| Dimension | Winner | Score | Runner-up | Why |")
        self.assertEqual(len(rows), 6)
        for dimension, winner, rating, alternative, _ in rows:
            expected = [(winner, rating), alternative.rsplit(" (", 1)]
            for name, displayed_score in expected:
                if displayed_score == "—":
                    continue
                with self.subTest(dimension=dimension, candidate=name):
                    candidate = catalogue[dimension, aliases.get(name, name)]
                    fraction = re.match(r"(-?\d+)/(\d+)", displayed_score)
                    self.assertIsNotNone(fraction)
                    self.assertEqual(int(fraction[2]), maximum)
                    self.assertEqual(
                        score(candidate, answers, tags, points),
                        int(fraction[1]),
                    )
