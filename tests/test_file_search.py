import tempfile
import unittest
from pathlib import Path

from aidesktop.file_search import list_local_files, search_local_files


class LocalFileSearchTests(unittest.TestCase):
    def test_finds_only_real_user_files_and_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            docs = home / "Documents"
            docs.mkdir()
            projects = docs / "Projects"
            projects.mkdir()
            (projects / "Mutsu Design Notes.pdf").write_text("private contents")
            (docs / ".passwords").write_text("secret")
            hidden = docs / ".hidden"
            hidden.mkdir()
            (hidden / "nothing.txt").write_text("hidden")
            (docs / "outsidelink").symlink_to(home)
            catalog = list_local_files(home=home)
            names = {item.name for item in catalog}
            self.assertIn("Projects", names)
            self.assertIn("Mutsu Design Notes.pdf", names)
            self.assertNotIn(".passwords", names)
            self.assertNotIn("outsidelink", names)
            self.assertNotIn("nothing.txt", names)
            found = search_local_files("mutsu", catalog)
            self.assertEqual([item.name for item in found], ["Mutsu Design Notes.pdf"])
            self.assertIn("Documents/Projects", found[0].subtitle)

    def test_empty_or_one_character_queries_do_not_show_private_file_index(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "Downloads").mkdir()
            (home / "Downloads" / "memo.txt").write_text("irrelevant")
            catalog = list_local_files(home=home)
            self.assertEqual(search_local_files("", catalog), [])
            self.assertEqual(search_local_files("m", catalog), [])
            self.assertEqual(search_local_files("memo", catalog)[0].name, "memo.txt")

    def test_scan_has_hard_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "Documents").mkdir()
            for index in range(100):
                (home / "Documents" / f"file-{index:03}.txt").write_text("")
            catalog = list_local_files(home=home, max_visited=12)
            self.assertLessEqual(len(catalog), 12)

    def test_does_not_read_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "Pictures").mkdir()
            (home / "Pictures" / "sample.jpg").write_bytes(b"private binary content")
            catalog = list_local_files(home=home)
            self.assertEqual(search_local_files("private", catalog), [])
            self.assertEqual(search_local_files("sample", catalog)[0].name, "sample.jpg")


if __name__ == "__main__":
    unittest.main()
