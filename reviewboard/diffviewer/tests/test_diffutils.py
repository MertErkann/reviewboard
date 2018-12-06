from __future__ import print_function, unicode_literals
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from kgb import SpyAgency
    get_original_file,
    get_original_file_from_repo,
    get_revision_str,
    get_sorted_filediffs,
    _PATCH_GARBAGE_INPUT,
from reviewboard.diffviewer.errors import PatchError
from reviewboard.diffviewer.models import DiffCommit, FileDiff
from reviewboard.scmtools.errors import FileNotFoundError
from reviewboard.scmtools.models import Repository
class BaseFileDiffAncestorTests(SpyAgency, TestCase):
    """A base test case that creates a FileDiff history."""

    fixtures = ['test_scmtools']

    _COMMITS = [
        {
            'parent': (
                b'diff --git a/bar b/bar\n'
                b'index e69de29..5716ca5 100644\n'
                b'--- a/bar\n'
                b'+++ b/bar\n'
                b'@@ -0,0 +1 @@\n'
                b'+bar\n'
            ),
            'diff': (
                b'diff --git a/foo b/foo\n'
                b'new file mode 100644\n'
                b'index 0000000..e69de29\n'

                b'diff --git a/bar b/bar\n'
                b'index 5716ca5..8e739cc 100644\n'
                b'--- a/bar\n'
                b'+++ b/bar\n'
                b'@@ -1 +1 @@\n'
                b'-bar\n'
                b'+bar bar bar\n'
            ),
        },
        {
            'parent': (
                b'diff --git a/baz b/baz\n'
                b'new file mode 100644\n'
                b'index 0000000..7601807\n'
                b'--- /dev/null\n'
                b'+++ b/baz\n'
                b'@@ -0,0 +1 @@\n'
                b'+baz\n'
            ),
            'diff': (
                b'diff --git a/foo b/foo\n'
                b'index e69de29..257cc56 100644\n'
                b'--- a/foo\n'
                b'+++ b/foo\n'
                b'@@ -0,0 +1 @@\n'
                b'+foo\n'

                b'diff --git a/bar b/bar\n'
                b'deleted file mode 100644\n'
                b'index 8e739cc..0000000\n'
                b'--- a/bar\n'
                b'+++ /dev/null\n'
                b'@@ -1 +0,0 @@\n'
                b'-bar -bar -bar\n'

                b'diff --git a/baz b/baz\n'
                b'index 7601807..280beb2 100644\n'
                b'--- a/baz\n'
                b'+++ b/baz\n'
                b'@@ -1 +1 @@\n'
                b'-baz\n'
                b'+baz baz baz\n'
            ),
        },
        {
            'parent': (
                b'diff --git a/corge b/corge\n'
                b'new file mode 100644\n'
                b'index 0000000..e69de29\n'
            ),
            'diff': (
                b'diff --git a/foo b/qux\n'
                b'index 257cc56..03b37a0 100644\n'
                b'--- a/foo\n'
                b'+++ b/qux\n'
                b'@@ -1 +1 @@\n'
                b'-foo\n'
                b'+foo bar baz qux\n'

                b'diff --git a/bar b/bar\n'
                b'new file mode 100644\n'
                b'index 0000000..5716ca5\n'
                b'--- /dev/null\n'
                b'+++ b/bar\n'
                b'@@ -0,0 +1 @@\n'
                b'+bar\n'

                b'diff --git a/corge b/corge\n'
                b'index e69de29..f248ba3 100644\n'
                b'--- a/corge\n'
                b'+++ b/corge\n'
                b'@@ -0,0 +1 @@\n'
                b'+corge\n'
            ),
        },
        {
            'parent': None,
            'diff': (
                b'diff --git a/bar b/quux\n'
                b'index 5716ca5..e69de29 100644\n'
                b'--- a/bar\n'
                b'+++ b/quux\n'
                b'@@ -1 +0,0 @@\n'
                b'-bar\n'
            ),
        },
    ]

    _CUMULATIVE_DIFF = {
        'parent': b''.join(
            parent_diff
            for parent_diff in (
                entry['parent']
                for entry in _COMMITS
            )
            if parent_diff is not None
        ),
        'diff': (
            b'diff --git a/qux b/qux\n'
            b'new file mode 100644\n'
            b'index 000000..03b37a0\n'
            b'--- /dev/null\n'
            b'+++ /b/qux\n'
            b'@@ -0,0 +1 @@\n'
            b'foo bar baz qux\n'

            b'diff --git a/bar b/quux\n'
            b'index 5716ca5..e69de29 100644\n'
            b'--- a/bar\n'
            b'+++ b/quux\n'
            b'@@ -1 +0,0 @@\n'
            b'-bar\n'

            b'diff --git a/baz b/baz\n'
            b'index 7601807..280beb2 100644\n'
            b'--- a/baz\n'
            b'+++ b/baz\n'
            b'@@ -1 +1 @@\n'
            b'-baz\n'
            b'+baz baz baz\n'

            b'diff --git a/corge b/corge\n'
            b'index e69de29..f248ba3 100644\n'
            b'--- a/corge\n'
            b'+++ b/corge\n'
            b'@@ -0,0 +1 @@\n'
            b'+corge\n'
        ),
    }

    _FILES = {
        ('bar', 'e69de29'): b'',
    }

    # A mapping of filediff details to the details of its ancestors in
    # (compliment, minimal) form.
    _HISTORY = {
        (1, 'foo', 'PRE-CREATION', 'foo', 'e69de29'): ([], []),
        (1, 'bar', 'e69de29', 'bar', '8e739cc'): ([], []),
        (2, 'foo', 'e69de29', 'foo', '257cc56'): (
            [],
            [
                (1, 'foo', 'PRE-CREATION', 'foo', 'e69de29'),
            ],
        ),
        (2, 'bar', '8e739cc', 'bar', '0000000'): (
            [],
            [
                (1, 'bar', 'e69de29', 'bar', '8e739cc'),
            ],
        ),
        (2, 'baz', 'PRE-CREATION', 'baz', '280beb2'): ([], []),
        (3, 'foo', '257cc56', 'qux', '03b37a0'): (
            [],
            [
                (1, 'foo', 'PRE-CREATION', 'foo', 'e69de29'),
                (2, 'foo', 'e69de29', 'foo', '257cc56'),
            ],
        ),
        (3, 'bar', 'PRE-CREATION', 'bar', '5716ca5'): (
            [
                (1, 'bar', 'e69de29', 'bar', '8e739cc'),
                (2, 'bar', '8e739cc', 'bar', '0000000'),
            ],
            [],
        ),
        (3, 'corge', 'PRE-CREATION', 'corge', 'f248ba3'): ([], []),
        (4, 'bar', '5716ca5', 'quux', 'e69de29'): (
            [
                (1, 'bar', 'e69de29', 'bar', '8e739cc'),
                (2, 'bar', '8e739cc', 'bar', '0000000'),
            ],
            [
                (3, 'bar', 'PRE-CREATION', 'bar', '5716ca5'),
            ],
        ),
    }

    def set_up_filediffs(self):
        """Create a set of commits with history."""
        def get_file(repo, path, revision, base_commit_id=None, request=None):
            if repo == self.repository:
                try:
                    return self._FILES[(path, revision)]
                except KeyError:
                    raise FileNotFoundError(path, revision,
                                            base_commit_id=base_commit_id)

            raise FileNotFoundError(path, revision,
                                    base_commit_id=base_commit_id)

        self.repository = self.create_repository(tool_name='Git')

        self.spy_on(Repository.get_file, call_fake=get_file)
        self.spy_on(Repository.get_file_exists,
                    call_fake=lambda *args, **kwargs: True)

        self.diffset = self.create_diffset(repository=self.repository)

        for i, diff in enumerate(self._COMMITS, 1):
            commit_id = 'r%d' % i
            parent_id = 'r%d' % (i - 1)

            self.create_diffcommit(
                diffset=self.diffset,
                repository=self.repository,
                commit_id=commit_id,
                parent_id=parent_id,
                diff_contents=diff['diff'],
                parent_diff_contents=diff['parent'])

        self.filediffs = list(FileDiff.objects.all())
        self.diffset.finalize_commit_series(
            cumulative_diff=self._CUMULATIVE_DIFF['diff'],
            parent_diff=self._CUMULATIVE_DIFF['parent'],
            validation_info=None,
            validate=False,
            save=True)

        # This was only necessary so that we could side step diff validation
        # during creation.
        Repository.get_file_exists.unspy()

    def get_filediffs_by_details(self):
        """Return a mapping of FileDiff details to the FileDiffs.

        Returns:
            dict:
            A mapping of FileDiff details to FileDiffs.
        """
        return {
            (
                filediff.commit_id,
                filediff.source_file,
                filediff.source_revision,
                filediff.dest_file,
                filediff.dest_detail,
            ): filediff
            for filediff in self.filediffs
        }


class GetDiffFilesTests(BaseFileDiffAncestorTests):
    fixtures = [
        'test_users',
    ] + BaseFileDiffAncestorTests.fixtures

    def test_get_diff_files_history(self):
        """Testing get_diff_files for a diffset with history"""
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        result = get_diff_files(diffset=self.diffset)

        self.assertEqual(len(result), len(self.diffset.cumulative_files))

        self.assertEqual(
            [diff_file['filediff'].pk for diff_file in result],
            [
                filediff.pk
                for filediff in get_sorted_filediffs(
                    self.diffset.cumulative_files)
            ])

        for diff_file in result:
            filediff = diff_file['filediff']
            print('Current filediff is: ', filediff)

            self.assertIsNone(diff_file['base_filediff'])

    def test_with_diff_files_history_query_count(self):
        """Testing get_diff_files query count for a diffset with history"""
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        with self.assertNumQueries(3):
            get_diff_files(diffset=self.diffset)

    def test_get_diff_files_history_query_count_ancestors_precomputed(self):
        """Testing get_diff_files query count for a whole diffset with history
        when ancestors have been computed
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        for filediff in self.filediffs:
            filediff.get_ancestors(minimal=False, filediffs=self.filediffs)

        with self.assertNumQueries(3):
            get_diff_files(diffset=self.diffset)

    def test_get_diff_files_query_count_filediff(self):
        """Testing get_diff_files for a single FileDiff with history"""
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        by_details = self.get_filediffs_by_details()
        filediff = by_details[(
            3, 'foo', '257cc56', 'qux', '03b37a0',
        )]

        with self.assertNumQueries(4):
            files = get_diff_files(diffset=self.diffset,
                                   filediff=filediff)

        self.assertEqual(len(files), 1)
        f = files[0]

        self.assertEqual(f['filediff'], filediff)
        self.assertIsNone(f['base_filediff'])

    def test_get_diff_files_query_count_filediff_ancestors_precomupted(self):
        """Testing get_diff_files query count for a single FileDiff with
        history when ancestors are precomputed
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        by_details = self.get_filediffs_by_details()

        for f in self.filediffs:
            f.get_ancestors(minimal=False, filediffs=self.filediffs)

        filediff = by_details[(
            3, 'foo', '257cc56', 'qux', '03b37a0',
        )]

        with self.assertNumQueries(1):
            files = get_diff_files(diffset=self.diffset,
                                   filediff=filediff)

        self.assertEqual(len(files), 1)
        f = files[0]

        self.assertEqual(f['filediff'], filediff)
        self.assertIsNone(f['base_filediff'])

    def test_get_diff_files_with_history_base_commit(self):
        """Testing get_diff_files for a whole diffset with history with a
        specified base commit ID
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        with self.assertNumQueries(len(self.filediffs) + 2):
            files = get_diff_files(diffset=self.diffset,
                                   base_commit=DiffCommit.objects.get(pk=2))

        expected_results = self._get_filediff_base_mapping_from_details(
            self.get_filediffs_by_details(),
            [
                (
                    (4, 'bar', '5716ca5', 'quux', 'e69de29'),
                    (2, 'bar', '8e739cc', 'bar', '0000000'),
                ),
                (
                    (3, 'corge', 'PRE-CREATION', 'corge', 'f248ba3'),
                    None,
                ),
                (
                    (3, 'foo', '257cc56', 'qux', '03b37a0'),
                    (2, 'foo', 'e69de29', 'foo', '257cc56'),
                ),
            ])

        results = {
            f['filediff']: f['base_filediff']
            for f in files
        }

        self.assertEqual(results, expected_results)

    def test_get_diff_files_with_history_base_commit_as_latest(self):
        """Testing get_diff_files for a whole diffset with history with a
        specified base commit as the latest commit
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        files = get_diff_files(diffset=self.diffset,
                               base_commit=DiffCommit.objects.get(pk=4))

        self.assertEqual(files, [])

    def test_get_diff_files_with_history_tip_commit(self):
        """Testing get_diff_files for a whole diffset with history with a
        specified tip commit
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        with self.assertNumQueries(3 + len(self.filediffs)):
            files = get_diff_files(diffset=self.diffset,
                                   tip_commit=DiffCommit.objects.get(pk=3))

        expected_results = self._get_filediff_base_mapping_from_details(
            self.get_filediffs_by_details(),
            [
                (
                    (3, 'foo', '257cc56', 'qux', '03b37a0'),
                    None,
                ),
                (
                    (2, 'baz', 'PRE-CREATION', 'baz', '280beb2'),
                    None,
                ),
                (
                    (3, 'corge', 'PRE-CREATION', 'corge', 'f248ba3'),
                    None,
                ),
                (
                    (3, 'bar', 'PRE-CREATION', 'bar', '5716ca5'),
                    None,
                ),
            ])

        results = {
            f['filediff']: f['base_filediff']
            for f in files
        }

        self.assertEqual(results, expected_results)

    def test_get_diff_files_with_history_tip_commit_precomputed(self):
        """Testing get_diff_files for a whole diffset with history with a
        specified tip commit when ancestors have been precomputed
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        for f in self.filediffs:
            f.get_ancestors(minimal=False, filediffs=self.filediffs)

        with self.assertNumQueries(4):
            files = get_diff_files(diffset=self.diffset,
                                   tip_commit=DiffCommit.objects.get(pk=3))

        expected_results = self._get_filediff_base_mapping_from_details(
            self.get_filediffs_by_details(),
            [
                (
                    (3, 'foo', '257cc56', 'qux', '03b37a0'),
                    None,
                ),
                (
                    (2, 'baz', 'PRE-CREATION', 'baz', '280beb2'),
                    None,
                ),
                (
                    (3, 'corge', 'PRE-CREATION', 'corge', 'f248ba3'),
                    None,
                ),
                (
                    (3, 'bar', 'PRE-CREATION', 'bar', '5716ca5'),
                    None,
                ),
            ])

        results = {
            f['filediff']: f['base_filediff']
            for f in files
        }

        self.assertEqual(results, expected_results)

    def test_get_diff_files_with_history_base_tip(self):
        """Testing get_diff_files for a whole diffset with history with a
        specified base and tip commit
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        with self.assertNumQueries(2 + len(self.filediffs)):
            files = get_diff_files(diffset=self.diffset,
                                   base_commit=DiffCommit.objects.get(pk=2),
                                   tip_commit=DiffCommit.objects.get(pk=3))

        expected_results = self._get_filediff_base_mapping_from_details(
            self.get_filediffs_by_details(),
            [
                (
                    (3, 'foo', '257cc56', 'qux', '03b37a0'),
                    (2, 'foo', 'e69de29', 'foo', '257cc56'),
                ),
                (
                    (3, 'corge', 'PRE-CREATION', 'corge', 'f248ba3'),
                    None,
                ),
                (
                    (3, 'bar', 'PRE-CREATION', 'bar', '5716ca5'),
                    (2, 'bar', '8e739cc', 'bar', '0000000'),
                ),
            ])

        results = {
            f['filediff']: f['base_filediff']
            for f in files
        }

        self.assertEqual(results, expected_results)

    def test_get_diff_files_with_history_base_tip_ancestors_precomputed(self):
        """Testing get_diff_files for a whole diffset with history with a
        specified base and tip commit when ancestors are precomputed
        """
        self.set_up_filediffs()

        review_request = self.create_review_request(repository=self.repository,
                                                    create_with_history=True)
        review_request.diffset_history.diffsets = [self.diffset]

        for f in self.filediffs:
            f.get_ancestors(minimal=False, filediffs=self.filediffs)

        with self.assertNumQueries(4):
            files = get_diff_files(diffset=self.diffset,
                                   base_commit=DiffCommit.objects.get(pk=2),
                                   tip_commit=DiffCommit.objects.get(pk=3))

        expected_results = self._get_filediff_base_mapping_from_details(
            self.get_filediffs_by_details(),
            [

                (
                    (3, 'foo', '257cc56', 'qux', '03b37a0'),
                    (2, 'foo', 'e69de29', 'foo', '257cc56'),
                ),
                (
                    (3, 'corge', 'PRE-CREATION', 'corge', 'f248ba3'),
                    None,
                ),
                (
                    (3, 'bar', 'PRE-CREATION', 'bar', '5716ca5'),
                    (2, 'bar', '8e739cc', 'bar', '0000000'),
                ),
            ])

        results = {
            f['filediff']: f['base_filediff']
            for f in files
        }

        self.assertEqual(results, expected_results)

    def _get_filediff_base_mapping_from_details(self, by_details, details):
        """Return a mapping from FileDiffs to base FileDiffs from the details.

        Args:
            by_details (dict):
                A mapping of FileDiff details to FileDiffs, as returned from
                :py:meth:`BaseFileDiffAncestorTests.get_filediffs_by_details`.

            details (list):
                A list of the details in the form of:

                .. code-block:: python

                   [
                       (filediff_1_details, parent_1_details),
                       (filediff_2_details, parent_2_details),
                   ]

                where each set of details is either ``None`` or a 5-tuple of:

                - :py:attr`FileDiff.commit_id`
                - :py:attr`FileDiff.source_file`
                - :py:attr`FileDiff.source_revision`
                - :py:attr`FileDiff.dest_file`
                - :py:attr`FileDiff.dest_detail`

        Returns:
            dict:
            A mapping of the FileDiffs to their base FileDiffs (or ``None`` if
            there is no base FileDiff).
        """
        return {
            by_details[filediff_details]:
                by_details.get(base_filediff_details)
            for filediff_details, base_filediff_details in details
        }


class GetOriginalFileTests(BaseFileDiffAncestorTests):
    """Unit tests for get_original_file."""

    def setUp(self):
        super(GetOriginalFileTests, self).setUp()

        self.set_up_filediffs()

        self.spy_on(get_original_file_from_repo)

        self.request = RequestFactory().get('/')
        self.request._local_site_name = None
        self.request.user = AnonymousUser()

    def test_created_in_first_parent(self):
        """Test get_original_file with a file created in the parent diff of the
        first commit
        """
        filediff = FileDiff.objects.get(dest_file='bar', dest_detail='8e739cc',
                                        commit_id=1)

        self.assertEqual(get_original_file(filediff, self.request, ['ascii']),
                         b'bar\n')
        self.assertTrue(get_original_file_from_repo.called_with(
            filediff, self.request, ['ascii']))

    def test_created_in_subsequent_parent(self):
        """Test get_original_file with a file created in the parent diff of a
        subsequent commit
        """
        filediff = FileDiff.objects.get(dest_file='baz', dest_detail='280beb2',
                                        commit_id=2)

        self.assertEqual(get_original_file(filediff, self.request, ['ascii']),
                         b'baz\n')

        self.assertTrue(get_original_file_from_repo.called)

    def test_created_previously_deleted(self):
        """Testing get_original_file with a file created and previously deleted
        """
        filediff = FileDiff.objects.get(dest_file='bar', dest_detail='5716ca5',
                                        commit_id=3)

        self.assertEqual(get_original_file(filediff, self.request, ['ascii']),
                         b'')

        self.assertFalse(get_original_file_from_repo.called)

    def test_renamed(self):
        """Test get_original_file with a renamed file"""
        filediff = FileDiff.objects.get(dest_file='qux', dest_detail='03b37a0',
                                        commit_id=3)

        self.assertEqual(get_original_file(filediff, self.request, ['ascii']),
                         b'foo\n')

        self.assertFalse(get_original_file_from_repo.called)

    def test_empty_parent_diff_old_patch(self):
        """Testing get_original_file with an empty parent diff with patch(1)
        that does not accept empty diffs
        """
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash',
                            'diffset',
                            'diffset__repository',
                            'diffset__repository__tool')
            .get(dest_file='corge',
                 dest_detail='f248ba3',
                 commit_id=3)
        )

        # FileDiff creation will set the _IS_PARENT_EMPTY flag.
        del filediff.extra_data[FileDiff._IS_PARENT_EMPTY_KEY]
        filediff.save(update_fields=('extra_data',))

        # Older versions of patch will choke on an empty patch with a "garbage
        # input" error, but newer versions will handle it just fine. We stub
        # out patch here to always fail so we can test for the case of an older
        # version of patch without requiring it to be installed.
        def _patch(diff, orig_file, filename, request=None):
            raise PatchError(
                filename,
                _PATCH_GARBAGE_INPUT,
                orig_file,
                'tmp123-new',
                b'',
                None)

        self.spy_on(patch, call_fake=_patch)

        # One query for each of the following:
        # - saving the RawFileDiffData in RawFileDiffData.recompute_line_counts
        # - saving the FileDiff in FileDiff.is_parent_diff_empty
        with self.assertNumQueries(2):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,
                encoding_list=['ascii'])

        self.assertEqual(orig, b'')

        # Refresh the object from the database with the parent diff attached
        # and then verify that re-calculating the original file does not cause
        # additional queries.
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash')
            .get(pk=filediff.pk)
        )

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,
                encoding_list=['ascii'])

    def test_empty_parent_diff_new_patch(self):
        """Testing get_original_file with an empty parent diff with patch(1)
        that does accept empty diffs
        """
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash',
                            'diffset',
                            'diffset__repository',
                            'diffset__repository__tool')
            .get(dest_file='corge',
                 dest_detail='f248ba3',
                 commit_id=3)
        )

        # FileDiff creation will set the _IS_PARENT_EMPTY flag.
        del filediff.extra_data[FileDiff._IS_PARENT_EMPTY_KEY]
        filediff.save(update_fields=('extra_data',))

        # Newer versions of patch will allow empty patches. We stub out patch
        # here to always fail so we can test for the case of a newer version
        # of patch without requiring it to be installed.
        def _patch(diff, orig_file, filename, request=None):
            # This is the only call to patch() that should be made.
            self.assertEqual(diff,
                             b'diff --git a/corge b/corge\n'
                             b'new file mode 100644\n'
                             b'index 0000000..e69de29\n')
            return orig_file

        self.spy_on(patch, call_fake=_patch)

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,
                encoding_list=['ascii'])

        self.assertEqual(orig, b'')

        # Refresh the object from the database with the parent diff attached
        # and then verify that re-calculating the original file does not cause
        # additional queries.
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash')
            .get(pk=filediff.pk)
        )

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,
                encoding_list=['ascii'])

    def test_empty_parent_diff_precomputed(self):
        """Testing get_original_file with an empty parent diff for which the
        result has been pre-computed
        """
        filediff = (
            FileDiff.objects
            .select_related('parent_diff_hash',
                            'diffset',
                            'diffset__repository',
                            'diffset__repository__tool')
            .get(dest_file='corge',
                 dest_detail='f248ba3',
                 commit_id=3)
        )

        with self.assertNumQueries(0):
            orig = get_original_file(
                filediff=filediff,
                request=self.request,
                encoding_list=['ascii'])

        self.assertEqual(orig, b'')