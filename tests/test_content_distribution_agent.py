import unittest
import tempfile
import os
from agents.content_distribution_agent import Post, load_content, _choose_channel

class TestContentDistributionAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, "w") as f:
            f.write("Test content")

    def tearDown(self):
        os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def test_load_content(self):
        posts = load_content(self.test_file)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].text, "Test content")

    def test_choose_channel(self):
        services = {
            "Gmail": True,
            "GoogleBusiness": True,
            "YouTube": False,
            "Calendar": False
        }
        post = Post(text="Test content", media=[])
        channel = _choose_channel(services, post)
        self.assertEqual(channel, "GoogleBusiness")

if __name__ == "__main__":
    unittest.main()
