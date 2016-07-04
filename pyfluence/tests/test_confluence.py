import unittest
import time

from unittest import TestCase

import pyfluence.confluence as co

TEST_SPACE = "TEST"


class TestConfluence(TestCase):

    def setUp(self):
        self.confluence = co.Confluence("admin","admin","http://localhost:1990/confluence")
        self.confluence.create_space(TEST_SPACE,"Test Space","Test Space Description")

    def tearDown(self):
        self.confluence.delete_space(TEST_SPACE)

    def test_content(self):
        # create content
        content_ob = self.confluence.create_content(
            space_key=TEST_SPACE,
            type="page",
            title="Test Parent Page",
            html_markup="<h1>This is a test page</h1>",
        )

        # update content with replace
        self.confluence.update_content(
            id=content_ob['id'],
            html_markup="<h1>This is an update</h1>",
            update_type=co.UPDATE_REPLACE
        )

        # update content with prepend
        self.confluence.update_content(
            id=content_ob['id'],
            html_markup="<div>prepended</div>",
            update_type=co.UPDATE_PREPEND
        )

        # create child page
        self.confluence.create_content(
            parent_content_id=content_ob['id'],
            space_key=TEST_SPACE,
            type="page",
            title="Test Child Page",
            wiki_markup="h1. This is a child page"
        )

    def test_search(self):

        self.confluence.create_content(
            space_key=TEST_SPACE,
            type="page",
            title="Test Search with Squirrels",
            html_markup="<h1>This is a test for search that will look for squirrels</h1>",
        )

        time.sleep(1)

        # search for new content created
        search_results = self.confluence.search("title ~ \"squirrels\"")
        self.assertEqual(len(search_results['results']),1)

    def test_attachments(self):
        # add attachment
        pass

if __name__ == '__main__':
    unittest.main()