import os
import unittest
import time
import json

from unittest import TestCase

from ..confluence import Confluence, ConfluenceResponseError, UPDATE_REPLACE, UPDATE_PREPEND


class TestConfluence(TestCase):
    _confluence = None  # type: Confluence
    _config = None  # type: dict
    _data_dir = os.path.join(os.path.dirname(__file__), 'data')

    @classmethod
    def setUpClass(cls):
        # load from config
        config_path = os.path.join(cls._data_dir, 'config.json')
        with open(config_path, 'r') as fs:
            cls._config = json.load(fs)

        cls._confluence = Confluence(cls._config['username'], cls._config['password'], cls._config['host'])

        try:
            cls._confluence.create_space(cls._config['test_space'], "Test Space", "Test Space Description")
        except ConfluenceResponseError as e:
            if e.status_code != 400:
                # we only pass the exception if this is not a 400 - 400 we're assumign means that the
                #   space already exists.
                raise e

    @classmethod
    def tearDownClass(cls):
        cls._confluence.delete_space(cls._config['test_space'])

    def test_content(self):
        # create content
        content_ob = self._confluence.create_content(
            space_key=self._config['test_space'],
            content_type="page",
            title="Test Parent Page",
            html_markup="<h1>This is a test page</h1>",
        )

        # update content with replace
        self._confluence.update_content(
            page_id=content_ob['id'],
            html_markup="<h1>This is an update</h1>",
            update_type=UPDATE_REPLACE
        )

        # update content with prepend
        self._confluence.update_content(
            page_id=content_ob['id'],
            html_markup="<div>prepended</div>",
            update_type=UPDATE_PREPEND
        )

        # create child page
        self._confluence.create_content(
            parent_content_id=content_ob['id'],
            space_key=self._config['test_space'],
            content_type="page",
            title="Test Child Page",
            wiki_markup="h1. This is a child page"
        )

        children = self._confluence.get_children(content_ob['id'])
        self.assertTrue('size' in children)
        self.assertTrue(children['size'] > 0)

        # delete content
        self._confluence.delete_content(page_id=content_ob['id'])

    def test_search(self):

        self._confluence.create_content(
            space_key=self._config['test_space'],
            content_type="page",
            title="Test Search with Squirrels",
            html_markup="<h1>This is a test for search that will look for squirrels</h1>",
        )

        # some period of time is required for the search to return recently created content.  Not ideal.
        time.sleep(5)

        # search for new content created
        search_results = self._confluence.search("title ~ \"squirrels\"")
        self.assertEqual(len(search_results['results']), 1)

    def test_attachments(self):
        # add attachment
        content_ob = self._confluence.create_content(
            space_key=self._config['test_space'],
            content_type="page",
            title="Test Attachments",
            html_markup="<h1>This is a test of attachments</h1>",
        )

        attach_path = os.path.join(self._data_dir, 'asterix.png')

        # initial creation
        attach_ob = self._confluence.add_content_attachment(attach_path, content_ob['id'])
        self.assertEqual(attach_ob['size'], 1)

        # get a single attachment
        attach_ob_get = self._confluence.get_attachment(attach_ob['results'][0]['id'])
        self.assertEqual(attach_ob['results'][0]['id'], attach_ob_get['id'])

        # try updating it now
        updated_ob = self._confluence.add_content_attachment(attach_path, content_ob['id'])
        self.assertEqual(updated_ob['id'], attach_ob['results'][0]['id'])

        # now get all attachments (there should still only be one)
        attach_ob_get_all = self._confluence.get_attachments(content_ob['id'])
        self.assertEqual(attach_ob_get_all['size'], 1)


if __name__ == '__main__':
    unittest.main()
