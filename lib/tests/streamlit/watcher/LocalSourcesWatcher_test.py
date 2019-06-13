# Copyright 2019 Streamlit Inc. All rights reserved.

"""streamlit.LocalSourcesWatcher unit test."""

import os
import sys
import unittest

from mock import patch

from streamlit.watcher import LocalSourcesWatcher
from streamlit.Report import Report


class FileIsInFolderTest(unittest.TestCase):

    def test_file_in_folder(self):
        ret = LocalSourcesWatcher._file_is_in_folder('/a/b/c/foo.py', '/a/b/c/')
        self.assertTrue(ret)

    def test_file_not_in_folder(self):
        ret = LocalSourcesWatcher._file_is_in_folder('/a/b/c/foo.py', '/d/e/f/')
        self.assertFalse(ret)

    def test_rel_file_not_in_folder(self):
        ret = LocalSourcesWatcher._file_is_in_folder('foo.py', '/d/e/f/')
        self.assertFalse(ret)


if sys.version_info[0] == 2:
    import test_data.dummy_module1 as DUMMY_MODULE_1
    import test_data.dummy_module2 as DUMMY_MODULE_2
else:
    import tests.streamlit.watcher.test_data.dummy_module1 as DUMMY_MODULE_1
    import tests.streamlit.watcher.test_data.dummy_module2 as DUMMY_MODULE_2

REPORT_PATH = os.path.join(
        os.path.dirname(__file__), 'test_data/not_a_real_script.py')
REPORT = Report(REPORT_PATH, [])
CALLBACK = lambda x: x

DUMMY_MODULE_1_FILE = os.path.abspath(DUMMY_MODULE_1.__file__)
DUMMY_MODULE_2_FILE = os.path.abspath(DUMMY_MODULE_2.__file__)

class LocalSourcesWatcherTest(unittest.TestCase):
    def setUp(self):
        try:
            del sys.modules[DUMMY_MODULE_1.__name__]
        except:
            pass

        try:
            del sys.modules[DUMMY_MODULE_2.__name__]
        except:
            pass

        try:
            del sys.modules['DUMMY_MODULE_1']
        except:
            pass

        try:
            del sys.modules['DUMMY_MODULE_2']
        except:
            pass

    @patch('streamlit.watcher.LocalSourcesWatcher.FileWatcher')
    def test_just_script(self, fob):
        lso = LocalSourcesWatcher.LocalSourcesWatcher(REPORT, CALLBACK)

        fob.assert_called_once()
        args = fob.call_args.args
        self.assertEqual(args[0], REPORT_PATH)
        method_type = type(self.test_just_script)
        self.assertEqual(type(args[1]), method_type)

        fob.reset_mock()
        lso.update_watched_modules()
        lso.update_watched_modules()
        lso.update_watched_modules()
        lso.update_watched_modules()

        self.assertEqual(fob.call_count, 1)  # __init__.py

    @patch('streamlit.watcher.LocalSourcesWatcher.FileWatcher')
    def test_script_and_2_modules_at_once(self, fob):
        lso = LocalSourcesWatcher.LocalSourcesWatcher(REPORT, CALLBACK)

        fob.assert_called_once()

        sys.modules['DUMMY_MODULE_1'] = DUMMY_MODULE_1
        sys.modules['DUMMY_MODULE_2'] = DUMMY_MODULE_2

        fob.reset_mock()
        lso.update_watched_modules()

        self.assertEqual(fob.call_count, 3)  # dummy modules and __init__.py

        method_type = type(self.test_just_script)

        call_args_list = sort_args_list(fob.call_args_list)

        args = call_args_list[0].args
        self.assertTrue('__init__.py' in args[0])
        args = call_args_list[1].args
        self.assertEqual(args[0], DUMMY_MODULE_1_FILE)
        self.assertEqual(type(args[1]), method_type)
        args = call_args_list[2].args
        self.assertEqual(args[0], DUMMY_MODULE_2_FILE)
        self.assertEqual(type(args[1]), method_type)

        fob.reset_mock()
        lso.update_watched_modules()

        self.assertEqual(fob.call_count, 0)

    @patch('streamlit.watcher.LocalSourcesWatcher.FileWatcher')
    def test_script_and_2_modules_in_series(self, fob):
        lso = LocalSourcesWatcher.LocalSourcesWatcher(REPORT, CALLBACK)

        fob.assert_called_once()

        sys.modules['DUMMY_MODULE_1'] = DUMMY_MODULE_1
        fob.reset_mock()

        lso.update_watched_modules()

        self.assertEqual(fob.call_count, 2)  # dummy module and __init__.py

        method_type = type(self.test_just_script)

        call_args_list = sort_args_list(fob.call_args_list)

        args = call_args_list[0].args
        self.assertTrue('__init__.py' in args[0])

        args = call_args_list[1].args
        self.assertEqual(args[0], DUMMY_MODULE_1_FILE)
        self.assertEqual(type(args[1]), method_type)

        sys.modules['DUMMY_MODULE_2'] = DUMMY_MODULE_2
        fob.reset_mock()
        lso.update_watched_modules()

        args = fob.call_args.args
        self.assertEqual(args[0], DUMMY_MODULE_2_FILE)
        self.assertEqual(type(args[1]), method_type)

        fob.assert_called_once()


def sort_args_list(args_list):
    return sorted(args_list, key=lambda args: args[0])