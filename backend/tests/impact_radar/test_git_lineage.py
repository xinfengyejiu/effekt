# encoding: utf-8
"""变更影响雷达：URL 解析与噪声过滤单测（不依赖 DB / git）。"""
import unittest

from app.api.service.gitLineageService import GitLineageService


class TestGitLineageUrlParse(unittest.TestCase):

    def test_extract_commit_from_commit_url(self):
        url = 'https://git.example.com/group/proj/-/commit/1a3eb739be9e218b9e1b1796cd687b34324abcd'
        self.assertEqual(
            GitLineageService.extract_commit_id(url),
            '1a3eb739be9e218b9e1b1796cd687b34324abcd'
        )

    def test_extract_commit_from_mr_query(self):
        url = 'https://git.example.com/group/proj/-/merge_requests/2685/diffs?commit_id=1a3eb739be9e218b'
        self.assertEqual(GitLineageService.extract_commit_id(url), '1a3eb739be9e218b')
        self.assertEqual(GitLineageService.extract_mr_iid(url), '2685')

    def test_extract_repository_url(self):
        url = 'https://git.example.com/group/proj/-/commit/abc1234'
        self.assertEqual(
            GitLineageService.extract_repository_url(url),
            'https://git.example.com/group/proj.git'
        )

    def test_parse_git_url(self):
        data, err = GitLineageService.parse_git_url(
            'https://git.example.com/a/b/-/commit/abcdef1234567'
        )
        self.assertEqual(err, '')
        self.assertEqual(data['commit_id'], 'abcdef1234567')
        self.assertEqual(data['source_type'], 'git_url')
        self.assertTrue(data['repository_url'].endswith('.git'))


class TestNoiseAndContext(unittest.TestCase):

    def test_is_not_actual_code(self):
        self.assertTrue(GitLineageService.is_not_actual_code(''))
        self.assertTrue(GitLineageService.is_not_actual_code('// comment'))
        self.assertTrue(GitLineageService.is_not_actual_code('import os'))
        self.assertTrue(GitLineageService.is_not_actual_code('{'))
        self.assertFalse(GitLineageService.is_not_actual_code('return orderService.pay(id);'))

    def test_collect_deleted_rows(self):
        lines = [
            '@@ -1,3 +1,4 @@',
            '-return orderService.pay(id);',
            '+return orderService.pay(id, true);',
            ' import foo',
            '-// old comment',
        ]
        rows = GitLineageService.collect_search_rows(lines)
        contents = [r['modified_row'] for r in rows]
        self.assertIn('return orderService.pay(id);', contents)
        self.assertNotIn('old comment', contents)

    def test_find_context_for_addition(self):
        lines = [
            ' void foo() {',
            '+  int x = 1;',
            '+  int y = 2;',
            ' }',
        ]
        ctx = GitLineageService.find_context_for_addition(lines, 1)
        stripped = [GitLineageService.strip_diff_prefix(c) for c in ctx]
        self.assertTrue(any('void foo' in s for s in stripped))


class TestSplitDiff(unittest.TestCase):

    def test_split_by_file(self):
        text = '\n'.join([
            'commit abc',
            'diff --git a/a.java b/a.java',
            '--- a/a.java',
            '+++ b/a.java',
            '-old',
            '+new',
            'diff --git a/b.py b/b.py',
            '--- a/b.py',
            '+++ b/b.py',
            '+print(1)',
        ])
        files = GitLineageService.split_diff_by_file(text)
        self.assertIn('a.java', files)
        self.assertIn('b.py', files)


if __name__ == '__main__':
    unittest.main()
