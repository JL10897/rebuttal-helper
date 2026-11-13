"""Tests for the page builders and checks, on the toy example. Run: python3 -m unittest discover -s tests"""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_labels  # noqa: E402
from points import PointsError, load_points  # noqa: E402


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)


def page_data(path, name="DATA"):
    return json.loads(re.search(rf"const {name} = (.*?);\n", Path(path).read_text(encoding="utf-8"), re.S).group(1))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.spec = json.loads((EX / "points_example.json").read_text(encoding="utf-8"))
        self.finals = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (EX / "final_dump" / "final").glob("*.json")}

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self, spec):
        p = self.dir / "points.json"
        p.write_text(json.dumps(spec), encoding="utf-8")
        return p

    def write_dump(self, finals):
        d = self.dir / "dump"
        (d / "final").mkdir(parents=True, exist_ok=True)
        for k, v in finals.items():
            (d / "final" / f"{k}.json").write_text(json.dumps(v), encoding="utf-8")
        return d


class PointsValidation(Base):
    def test_example_loads_with_derived_ids(self):
        _, items = load_points(EX / "points_example.json", EX / "reviews_example.txt")
        self.assertEqual([i["id"] for i in items][:3], ["general", "ab12-open", "ab12-1"])

    def test_altered_quote_is_rejected_so_quotes_stay_verbatim(self):
        spec = copy.deepcopy(self.spec)
        spec["reviewers"][0]["points"][0]["quotes"][0]["text"] += " (paraphrased)"
        with self.assertRaisesRegex(PointsError, "not verbatim"):
            load_points(self.write_spec(spec), EX / "reviews_example.txt")

    def test_unknown_key_is_rejected_so_typos_do_not_pass_silently(self):
        spec = copy.deepcopy(self.spec)
        spec["reviewers"][0]["points"][0]["paraphase"] = "typo"
        with self.assertRaisesRegex(PointsError, "unknown keys"):
            load_points(self.write_spec(spec))

    def test_point_left_out_of_every_comment_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec["comments"][1]["ids"].remove("ab12-3")
        with self.assertRaisesRegex(PointsError, "not placed"):
            load_points(self.write_spec(spec))

    def test_comment_mixing_reviewers_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec["comments"][1]["ids"].append("cd34-open")
        spec["comments"][2]["ids"].remove("cd34-open")
        with self.assertRaisesRegex(PointsError, "one reviewer"):
            load_points(self.write_spec(spec))

    def test_reviewer_name_with_underscore_is_rejected_because_draft_names_split_on_it(self):
        spec = copy.deepcopy(self.spec)
        spec["reviewers"][0]["name"] = "Ab_12"
        with self.assertRaisesRegex(PointsError, "letters/digits/-"):
            load_points(self.write_spec(spec))


class ComparePage(Base):
    def build(self, drafts):
        out = self.dir / "compare.html"
        r = run("build_compare_page.py", EX / "points_example.json", EX / "reviews_example.txt",
                ROOT / "style" / "author_style.example.md", out, "--drafts", drafts)
        return r, out

    def test_only_latest_round_is_shown(self):
        r, out = self.build(EX / "drafts")
        self.assertEqual(r.returncode, 0, r.stderr)
        item = next(i for i in page_data(out)["items"] if i["id"] == "ab12-2")
        self.assertEqual([d["model"] for d in item["drafts"]], ["Model A", "Model B"])
        self.assertTrue(item["drafts"][0]["reply"].startswith("Good question."))
        self.assertNotIn("round", item)

    def test_badly_named_draft_file_stops_the_build(self):
        d = self.dir / "drafts"
        d.mkdir()
        (d / "ab12-2_model-a.json").write_text("{}", encoding="utf-8")
        r, out = self.build(d)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not a draft file name", r.stderr)
        self.assertFalse(out.exists())


class SubmitPage(Base):
    def build(self, spec=None, finals=None):
        out = self.dir / "submit.html"
        r = run("build_submit_page.py", self.write_spec(spec or self.spec), self.write_dump(finals or self.finals), out)
        return r, out

    def test_assembly_headings_separators_and_enum_fix(self):
        r, out = self.build()
        self.assertEqual(r.returncode, 0, r.stderr)
        data = page_data(out)
        self.assertEqual([c["subject"] for c in data],
                         ["General Response to All Reviewers", "Response to Reviewer Ab12", "Response to Reviewer Cd34"])
        cd = data[2]["text"]
        self.assertIn("\n\n---\n\n**Point 1. With only 12 participants", cd)
        self.assertIn("agreement is high;\n\n(ii) the disagreements", cd)
        self.assertIn("Cd34·1", page_data(out, "META")["changes"][0])

    def test_chinese_character_stops_and_writes_no_page(self):
        finals = copy.deepcopy(self.finals)
        finals["ab12-2"]["text"] += " 待补"
        r, out = self.build(finals=finals)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Chinese or full-width", r.stderr)
        self.assertFalse(out.exists())

    def test_placeholder_stops(self):
        finals = copy.deepcopy(self.finals)
        finals["ab12-3"]["text"] = "[TBD: seed results]"
        r, _ = self.build(finals=finals)
        self.assertIn("placeholder", r.stderr)

    def test_comment_over_limit_stops(self):
        spec = copy.deepcopy(self.spec)
        spec["char_limit"] = 500
        r, out = self.build(spec=spec)
        self.assertIn("over the 500 limit", r.stderr)
        self.assertFalse(out.exists())

    def test_without_comments_prints_a_grouping_within_the_limit_and_stops(self):
        spec = copy.deepcopy(self.spec)
        del spec["comments"]
        spec["char_limit"] = 600
        r, out = self.build(spec=spec)
        self.assertNotEqual(r.returncode, 0)
        groups = json.loads(r.stdout)["comments"]
        self.assertEqual(groups[0]["ids"], ["general"])
        self.assertEqual(sum(len(g["ids"]) for g in groups), 8)
        self.assertGreater(len([g for g in groups if g["ids"][0].startswith("ab12")]), 1)
        self.assertFalse(out.exists())

    def test_missing_closing_line_and_citation_without_references_are_reported(self):
        finals = copy.deepcopy(self.finals)
        finals["cd34-2"]["text"] = "We have fixed these typos, following Smith et al. (2020)."
        r, out = self.build(finals=finals)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Closing line: the last comment to Cd34", r.stdout)
        self.assertIn("References: Cd34·2 cite other works", r.stdout)
        self.assertIn("[Cd34·2] We have fixed these typos", r.stdout)

    def test_diff_tool_finds_a_changed_final(self):
        r, a = self.build()
        b = self.dir / "fresh.html"
        b.write_text(a.read_text(encoding="utf-8"), encoding="utf-8")
        self.assertEqual(run("diff_submit_pages.py", a, b).returncode, 0)
        finals = copy.deepcopy(self.finals)
        finals["ab12-2"]["text"] += " Edited."
        run("build_submit_page.py", self.write_spec(self.spec), self.write_dump(finals), b)
        r = run("diff_submit_pages.py", a, b)
        self.assertEqual(r.returncode, 1)
        self.assertIn("DIFFERENT", r.stdout)


class Labels(unittest.TestCase):
    AUX = (r"\newlabel{tab:main}{{2}{8}{Main results.\relax }{table.caption.24}{}}" "\n"
           r"\newlabel{app:review}{{B.3}{25}{Evidence and {Human} Review}{subsection.B.3}{}}" "\n"
           r"\newlabel{fig:overview}{{2}{4}{Overview}{figure.caption.4}{}}" "\n")

    def test_labels_resolve_by_kind_and_ranges_expand(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.aux").write_text(self.AUX, encoding="utf-8")
            labels = check_labels.read_labels(Path(tmp))
        self.assertEqual(check_labels.expand("2, 15–16"), ["2", "15", "16"])
        self.assertEqual([l["key"] for l in labels if check_labels.matches("Table", "2", l)], ["tab:main"])
        self.assertEqual([l["key"] for l in labels if check_labels.matches("Figure", "2", l)], ["fig:overview"])
        self.assertEqual([l["key"] for l in labels if check_labels.matches("Appendix", "B.3", l)], ["app:review"])
        self.assertEqual([l for l in labels if check_labels.matches("Appendix", "B.4", l)], [])

    def test_citations_are_found_in_reply_text(self):
        text = "see Tables 2, 15–16; Appendix F.4) and Figure 3."
        found = [(check_labels.KIND[m[1].lower()], check_labels.expand(m[2])) for m in check_labels.CITE.finditer(text)]
        self.assertEqual(found, [("Table", ["2", "15", "16"]), ("Appendix", ["F.4"]), ("Figure", ["3"])])


if __name__ == "__main__":
    unittest.main()
