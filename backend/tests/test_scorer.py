"""Run with:  python -m unittest discover -s tests   (from the backend folder)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import parser, scorer, skills  # noqa: E402

JD = ("We need a developer with Python, Flask, React and MySQL experience to build REST APIs. "
      "Git and Docker are a plus. Good communication skills required for our agile team.")

STRONG = """Priya Nair
priya@example.com | +91 98765 43210
Skills
Python, Flask, React, MySQL, REST APIs, Git, Docker, Communication
Projects
Built a Flask and React app with MySQL and REST APIs, deployed with Docker.
Education
B.Tech Computer Science
Experience
Intern building APIs with Python and Git in an agile team for 6 months.
""" + "Worked on many web features and wrote clean, tested code. " * 15

WEAK = """Sam Roy
sam@example.com
Skills
AutoCAD, Excel
Experience
Maintenance assistant in a workshop.
""" + "Handled equipment inspection and safety checks daily. " * 10


class SkillTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertIn("Java", skills.extract_skills("Experienced in Java and Spring Boot"))
        self.assertNotIn("Java", skills.extract_skills("Experienced in JavaScript only"))
        self.assertIn("C++", skills.extract_skills("Wrote C++ services"))
        self.assertIn("Node.js", skills.extract_skills("Backend with Node.js"))

    def test_implied(self):
        self.assertTrue(skills.has_skill("Worked with MySQL daily", "SQL"))

    def test_normalize(self):
        self.assertEqual(skills.normalize_skill_list(["react", "Node", "react", "Kubernetes ", ""]),
                         ["React", "Node.js", "Kubernetes"])


class ParserTests(unittest.TestCase):
    def test_fields(self):
        self.assertEqual(parser.find_email(STRONG), "priya@example.com")
        self.assertTrue(parser.find_phone(STRONG))
        self.assertEqual(parser.find_name(STRONG), "Priya Nair")
        self.assertIn("projects", parser.find_sections(STRONG))


class ScorerTests(unittest.TestCase):
    def test_ranking_order(self):
        strong = scorer.analyze(JD, [], STRONG, "a.txt")
        weak = scorer.analyze(JD, [], WEAK, "b.txt")
        self.assertGreater(strong["score"], weak["score"])
        self.assertIn("Flask", strong["matched"])
        self.assertIn("Flask", weak["missing"])
        self.assertGreaterEqual(strong["score"], 55)
        self.assertLess(weak["score"], 35)

    def test_score_bounds(self):
        r = scorer.analyze(JD, [], STRONG, "a.txt")
        self.assertTrue(0 <= r["score"] <= 100)


if __name__ == "__main__":
    unittest.main()
