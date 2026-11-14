"""Checks for tools/roadmap_close.py (run: python3 tools/test_roadmap_close.py)."""
import pathlib
import tempfile
import unittest

from roadmap_close import PART, check, close_rows, main, note_rows, parse_ids, resolve

DOC = ("\ufeff# TODO\n\n| Row | Item |\n|---|---|\n| 54 | a |\n| 541 | b |\n"
       "| T5.Q24 | c |\n| 6.44 | d |\n| 35, 36 | e |\ntext 54 stays\r\n")


class ParseTests(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(parse_ids("Fixes it.\nCloses row 54\n"), [["54"]])
        self.assertEqual(parse_ids("closes rows 22, 27."), [["22", "27"]])
        self.assertEqual(parse_ids("- Closes row T5.Q24\nCloses row 6.44"), [["T5.Q24"], ["6.44"]])
        self.assertEqual(parse_ids("Closes rows 1 and 2"), [["1", "2"]])
        self.assertEqual(parse_ids("This closes row 5 mid-sentence"), [])
        self.assertEqual(parse_ids(None), [])

    def test_stops_at_first_non_id(self):
        self.assertEqual(parse_ids("Closes row 54 for the ruck"), [["54"]])
        self.assertEqual(parse_ids("Closes row 25 (see Id column)"), [["25"]])
        self.assertEqual(parse_ids("Closes row 5 (partly, see 12)"), [["5"]])
        self.assertEqual(parse_ids("Closes rows 22 and 27 except T5"), [["22", "27"]])
        self.assertEqual(parse_ids("Closes row Id"), [])


class CloseTests(unittest.TestCase):
    def test_exact_first_cell_only(self):
        new, closed = close_rows(DOC, ["54", "T5.Q24"])
        self.assertEqual(closed, ["54", "T5.Q24"])
        self.assertIn("| 541 | b |", new)
        self.assertIn("text 54 stays", new)
        self.assertNotIn("| 54 | a |", new)
        self.assertTrue(new.startswith("\ufeff# TODO\n"))

    def test_other_bytes_unchanged(self):
        new, _ = close_rows(DOC, ["6.44"])
        self.assertEqual(new, DOC.replace("| 6.44 | d |\n", ""))

    def test_combined_cell_only(self):
        doc = DOC + "| 35 | x |\n| 36 | y |\n"
        new, closed = close_rows(doc, resolve(doc, parse_ids("Closes rows 35, 36")))
        self.assertEqual(closed, ["35, 36"])
        self.assertIn("| 35 | x |", new)
        self.assertIn("| 36 | y |", new)

    def test_singles_without_combined_row(self):
        self.assertEqual(resolve(DOC, parse_ids("Closes rows 54, 6.44")), ["54", "6.44"])

    def test_header_never_closed(self):
        self.assertEqual(resolve(DOC, parse_ids("Closes row Row")), [])

    def test_no_match(self):
        self.assertEqual(close_rows(DOC, ["999"]), (DOC, []))

    def test_main_writes_and_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            todo, body = pathlib.Path(d, "TODO.md"), pathlib.Path(d, "body.txt")
            todo.write_bytes(DOC.encode("utf-8"))
            body.write_text("Closes row 54", encoding="utf-8")
            main(["--body-file", str(body), "--todo", str(todo), "--dry-run"])
            self.assertEqual(todo.read_bytes(), DOC.encode("utf-8"))
            main(["--body-file", str(body), "--todo", str(todo)])
            self.assertEqual(todo.read_bytes(), DOC.replace("| 54 | a |\n", "").encode("utf-8"))


class PartTests(unittest.TestCase):
    def test_part_forms(self):
        self.assertEqual(parse_ids("Part of row 142\n", PART), [["142"]])
        self.assertEqual(parse_ids("- part of rows 131, 132", PART), [["131", "132"]])
        self.assertEqual(parse_ids("Closes row 54", PART), [])

    def test_note_appends_to_what_cell(self):
        new, noted = note_rows(DOC, ["54"], "1600", "Legacy: the 2010 start.")
        self.assertEqual(noted, ["54"])
        self.assertIn("| 54 | a Merged #1600: Legacy: the 2010 start. |\n", new)
        self.assertIn("| 541 | b |", new)
        self.assertEqual(new.replace(" Merged #1600: Legacy: the 2010 start.", ""), DOC)

    def test_note_keeps_crlf(self):
        doc = "| 7 | x | y |\r\n"
        self.assertEqual(note_rows(doc, ["7"], "1", "T")[0], "| 7 | x Merged #1: T. | y |\r\n")

    def test_main_closes_and_notes(self):
        with tempfile.TemporaryDirectory() as d:
            todo, body = pathlib.Path(d, "TODO.md"), pathlib.Path(d, "body.txt")
            todo.write_bytes(DOC.encode("utf-8"))
            body.write_text("Closes row 54\nPart of row 6.44", encoding="utf-8")
            main(["--body-file", str(body), "--todo", str(todo), "--pr", "9", "--title", "Grounds"])
            out = todo.read_bytes().decode("utf-8")
            self.assertNotIn("| 54 | a |", out)
            self.assertIn("| 6.44 | d Merged #9: Grounds. |", out)


class CheckTests(unittest.TestCase):
    def test_needs_a_row(self):
        self.assertIsNotNone(check("Fixes the ruck.", DOC))
        self.assertIsNone(check("Closes row 54", DOC))
        self.assertIsNone(check("Part of row T5.Q24", DOC))
        self.assertIsNone(check("No row: CI retry for a flaky mirror", DOC))
        self.assertIsNotNone(check("No row:", DOC))

    def test_unknown_row_fails(self):
        self.assertIn("999", check("Part of row 999", DOC))
        self.assertIn("999", check("Closes rows 54, 999", DOC))


if __name__ == "__main__":
    unittest.main()
