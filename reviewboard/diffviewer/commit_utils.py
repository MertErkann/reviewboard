"""Utilities for dealing with DiffCommits."""

from __future__ import unicode_literals

import base64
import json
from itertools import chain

from django.utils.encoding import force_bytes
from django.utils.six.moves import zip

from reviewboard.scmtools.core import PRE_CREATION, UNKNOWN


def get_file_exists_in_history(validation_info, repository, parent_id, path,
                               revision, base_commit_id=None, request=None):
    """Return whether or not the file exists, given the validation information.

    Args:
        validation_info (dict):
            Validation metadata generated by the
            :py:class:`~reviewboard.webapi.resources.validate_diffcommit.
            ValidateDiffCommitResource`.

        repository (reviewboard.scmtools.models.Repository):
            The repository.

        parent_id (unicode):
            The parent commit ID of the commit currently being processed.

        path (unicode):
            The file path.

        revision (unicode):
            The revision of the file to retrieve.

        base_commit_id (unicode, optional):
            The base commit ID of the commit series.

        request (django.http.HttpRequest):
            The HTTP request from the client.

    Returns:
        bool:
        Whether or not the file exists.
    """
    while parent_id in validation_info:
        entry = validation_info[parent_id]
        tree = entry['tree']

        if revision == UNKNOWN:
            for removed_info in tree['removed']:
                if removed_info['filename'] == path:
                    return False

        for added_info in chain(tree['added'], tree['modified']):
            if (added_info['filename'] == path and
                (revision == UNKNOWN or
                 added_info['revision'] == revision)):
                return True

        parent_id = entry['parent_id']

    # We did not find an entry in our validation info, so we need to fall back
    # to checking the repository.
    return repository.get_file_exists(path, revision,
                                      base_commit_id=base_commit_id,
                                      request=request)


def exclude_ancestor_filediffs(to_filter, all_filediffs=None):
    """Exclude all ancestor FileDiffs from the given list and return the rest.

    A :pyclass:`~reviewboard.diffviewer.models.filediff.FileDiff` is considered
    an ancestor of another if it occurs in a previous commit and modifies the
    same file.

    As a result, only the most recent (commit-wise) FileDiffs that modify a
    given file will be included in the result.

    Args:
        to_filter (list of reviewboard.diffviewer.models.filediff.FileDiff):
            The FileDiffs to filter.

        all_filediffs (list of reviewboard.diffviewer.models.filediff.FileDiff,
                       optional):
            The list of all FileDiffs in the :py:class:`~reviewboard.
            diffviewer.models.diffset.DiffSet>`.

            If not provided, it is assumed that ``to_filter`` is a list of all
            FileDiffs in the :py:class:`~reviewboard.diffviewer.models.
            diffset.DiffSet>`.

    Returns:
        list of reviewboard.diffviewer.models.filediff.FileDiff:
        The FileDiffs that are not ancestors of other FileDiffs.
    """
    if all_filediffs is None:
        all_filediffs = to_filter

    ancestor_pks = {
        ancestor.pk
        for filediff in to_filter
        for ancestor in filediff.get_ancestors(minimal=False,
                                               filediffs=all_filediffs)
    }

    return [
        filediff
        for filediff in to_filter
        if filediff.pk not in ancestor_pks
    ]


def deserialize_validation_info(raw):
    """Deserialize the raw validation info.

    Args:
        raw (unicode or bytes):
            The raw validation info from the client.

    Returns:
        dict:
        The deserialized validation info.

    Raises:
        ValueError:
            Either the data could not be base64-decoded or the resulting JSON
            was of an invalid format (i.e., it was not a dictionary).

        TypeError:
            The base64-decoded data could not be interpreted as JSON.
    """
    value = json.loads(base64.b64decode(force_bytes(raw)).decode('utf-8'))

    if not isinstance(value, dict):
        raise ValueError('Invalid format.')

    return value


def serialize_validation_info(info):
    """Serialize the given validation info into a raw format.

    Args:
        info (dict):
            The dictionary of validation info.

    Returns:
        unicode:
        The base64-encoded JSON of the validation info.
    """
    data = json.dumps(info).encode('utf-8')

    return base64.b64encode(data).decode('utf-8')


def update_validation_info(validation_info, commit_id, parent_id, filediffs):
    """Update the validation info with a new commit.

    Args:
        validation_info (dict):
            The dictionary of validation info. This will be modified in-place.

            This is a mapping of commit IDs to their metadata. Each metadata
            dictionary contains the following keys:

            ``parent_id``:
                The commit ID of the parent commit.

            ``tree``:
                A dictionary of the added, removed, and modified files in this
                commit.

        commit_id (unicode):
            The commit ID of the commit whose metadata is being added to the
            dictionary.

            This must not already be present in ``validation_info``.

        parent_id (unicode):
            The commit ID of the parent commit.

            This must be present in ``validation_info`` *unless* this is the
            first commit being added (i.e., ``validation_info`` is empty).

        filediffs (list of reviewboard.diffviewer.models.filediff.FileDiff):
            The parsed FileDiffs from :py:func:`~reviewboard.diffviewer.
            filediff_creator.create_filediffs`.

    Returns:
        dict:
        The dictionary of validation info.
    """
    from reviewboard.diffviewer.models import FileDiff

    assert validation_info == {} or parent_id in validation_info
    assert commit_id not in validation_info

    added = []
    removed = []
    modified = []

    for f in filediffs:
        if f.status in (FileDiff.DELETED, FileDiff.MOVED):
            removed.append({
                'filename': f.source_file,
                'revision': f.source_revision,
            })

        if (f.status in (FileDiff.COPIED, FileDiff.MOVED) or
            (f.status == FileDiff.MODIFIED and
             f.source_revision == PRE_CREATION)):
            added.append({
                'filename': f.dest_file,
                'revision': f.dest_detail,
            })
        elif f.status == FileDiff.MODIFIED:
            modified.append({
                'filename': f.dest_file,
                'revision': f.dest_detail,
            })

    validation_info[commit_id] = {
        'parent_id': parent_id,
        'tree': {
            'added': added,
            'modified': modified,
            'removed': removed,
        },
    }

    return validation_info


class CommitHistoryDiffEntry(object):
    """An entry in a commit history diff."""

    COMMIT_ADDED = 'added'
    COMMIT_REMOVED = 'removed'
    COMMIT_MODIFIED = 'modified'
    COMMIT_UNMODIFIED = 'unmodified'

    entry_types = (
        COMMIT_ADDED,
        COMMIT_REMOVED,
        COMMIT_MODIFIED,
        COMMIT_UNMODIFIED,
    )

    def __init__(self, entry_type, old_commit=None, new_commit=None):
        """Initialize the CommitHistoryDiffEntry object.

        Args:
            entry_type (unicode):
                The commit type. This must be one of the values in
                :py:attr:`entry_types`.

            old_commit (reviewboard.diffviewer.models.diffcommit.DiffCommit,
                        optional):
                The old commit. This is required if the commit type is one of:

                * :py:data:`COMMIT_REMOVED`
                * :py:data:`COMMIT_MODIFIED`
                * :py:data:`COMMIT_UNMODIFIED`

            new_commit (reviewboard.diffviewer.models.diffcommit.DiffCommit,
                        optional):
                The new commit. This is required if the commit type is one of:

                * :py:data:`COMMIT_ADDED`
                * :py:data:`COMMIT_MODIFIED`
                * :py:data:`COMMIT_UNMODIFIED`

        Raises:
            ValueError:
                The value of ``entry_type`` was invalid or the wrong commits
                were specified.
        """
        if entry_type not in self.entry_types:
            raise ValueError('Invalid entry_type: "%s"' % entry_type)

        if not old_commit and entry_type != self.COMMIT_ADDED:
            raise ValueError('old_commit required for given commit type.')

        if not new_commit and entry_type != self.COMMIT_REMOVED:
            raise ValueError('new_commit required for given commit type')

        self.entry_type = entry_type
        self.old_commit = old_commit
        self.new_commit = new_commit

    def serialize(self):
        """Serialize the entry to a dictionary.

        Returns:
            dict:
            A dictionary of the serialized information.
        """
        result = {
            'entry_type': self.entry_type,
        }

        if self.new_commit:
            result['new_commit_id'] = self.new_commit.pk

        if self.old_commit:
            result['old_commit_id'] = self.old_commit.pk

        return result

    def __eq__(self, other):
        """Compare two entries for equality.

        Two entries are equal if and only if their attributes match.

        Args:
            other (CommitHistoryDiffEntry):
                The entry to compare against.

        Returns:
            bool:
            Whether or not this entry and the other entry are equal.
        """
        return (self.entry_type == other.entry_type,
                self.old_commit == other.old_commit,
                self.new_commit == other.new_commit)

    def __ne__(self, other):
        """Compare two entries for inequality.

        Two entries are not equal if and only if any of their attributes don't
        match.

        Args:
            other (CommitHistoryDiffEntry):
                The entry to compare against.

        Returns:
            bool:
            Whether or not this entry and the other entry are not equal.
        """
        return not self == other

    def __repr__(self):
        """Return a string representation of the entry.

        Returns:
            unicode:
            A string representation of the entry.
        """
        return (
            '<CommitHistoryDiffEntry(entry_type=%s, '
            'old_commit=%s, new_commit=%s)>'
            % (self.entry_type, self.old_commit, self.new_commit)
        )


def diff_histories(old_history, new_history):
    """Yield the entries in the diff between the old and new histories.

    Args:
        old_history (list of reviewboard.diffviewer.models.diffcommit.
                     DiffCommit):
            The list of commits from a previous
            :py:class:`~reviewboard.diffviewer.models.diffset.DiffSet`.

        new_history (list of reviewboard.diffviewer.models.diffcommit.
                     DiffCommit):
            The list of commits from the new
            :py:class:`~reviewboard.diffviewer.models.diffset.DiffSet`.

    Yields:
        CommitHistoryDiffEntry:
        The history entries.
    """
    i = 0

    # This is not quite the same as ``enumerate(...)`` because if we run out
    # of history, ``i`` will not be incremented.

    for old_commit, new_commit in zip(old_history, new_history):
        if old_commit.commit_id != new_commit.commit_id:
            break

        yield CommitHistoryDiffEntry(
            entry_type=CommitHistoryDiffEntry.COMMIT_UNMODIFIED,
            old_commit=old_commit,
            new_commit=new_commit)

        i += 1

    for old_commit in old_history[i:]:
        yield CommitHistoryDiffEntry(
            entry_type=CommitHistoryDiffEntry.COMMIT_REMOVED,
            old_commit=old_commit)

    for new_commit in new_history[i:]:
        yield CommitHistoryDiffEntry(
            entry_type=CommitHistoryDiffEntry.COMMIT_ADDED,
            new_commit=new_commit)


def get_base_and_tip_commits(base_commit_id, tip_commit_id, diffset=None,
                             commits=None):
    """Return the base and tip commits specified.

    Args:
        base_commit_id (int):
            The primary key of the requested base commit. This may be ``None``,
            in which case a base commit will not be looked up or returned.

        tip_commit_id (int):
            The primary key of the requested tip commit. This may be ``None``,
            in which case a tip commit will not be looked up or returned.

        diffset (reviewboard.diffviewer.models.diffset.DiffSet, optional):
            The diffset that the commits belong to.

            This argument is only required if ``commits`` is ``None``.

        commits (list of reviewboard.diffviewer.models.diffcommit.DiffCommit,
                 optional):
            A pre-fetched list of commits to use instead of querying the
            database.

            If this argument is not provided, ``diffset`` must be provided to
            limit the database query to that DiffSet's commits.

    Returns:
        tuple:
        A 2-tuple of the following:

        * The requested base commit (:py:class:`~reviewboard.diffviewer.models.
          diffcommit.DiffCommit`).
        * The requested tip commit (:py:class:`~reviewboard.diffviewer.models.
          diffcommit.DiffCommit`).

        If either the base or tip commit are not requested or they cannot be
        found, then their corresponding entry in the tuple will be ``None``.
    """
    if commits is None:
        if diffset is None:
            raise ValueError(
                'get_base_and_tip_commits() requires either diffset or '
                'commits to be provided.')

        commit_ids = []

        if base_commit_id is not None:
            commit_ids.append(base_commit_id)

        if tip_commit_id is not None:
            commit_ids.append(tip_commit_id)

        if commit_ids:
            commits = list(diffset.commits.filter(pk__in=commit_ids))

    if not commits:
        return None, None

    base_commit = None
    tip_commit = None

    if base_commit_id is not None or tip_commit_id is not None:
        for commit in commits:
            if base_commit_id == commit.pk:
                base_commit = commit

            if tip_commit_id == commit.pk:
                tip_commit = commit

    return base_commit, tip_commit
