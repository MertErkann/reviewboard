from django.utils import six
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                         self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                    self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
                                  self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
        diff_file = SimpleUploadedFile('diff',
                                       self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
        diff_file = SimpleUploadedFile('diff',
                                       self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
        self.assertEqual(filediff.diff, self.DEFAULT_GIT_FILEDIFF_DATA_DIFF)
        self.assertEqual(f.source_revision, revisions[0].decode('utf-8'))
        self.assertEqual(f.dest_detail, revisions[1].decode('utf-8'))
        self.assertEqual(f.source_revision, revisions[0].decode('utf-8'))
        self.assertEqual(f.dest_detail, revisions[2].decode('utf-8'))
        self.diff = SimpleUploadedFile('diff',
                                       self.DEFAULT_GIT_FILEDIFF_DATA_DIFF,
        validation_info = self._base64_json({
        })
        validation_info = self._base64_json({
        })
        validation_info = self._base64_json({
        })
        validation_info = self._base64_json({
        })
        validation_info = base64.b64encode(b'Not valid json.')

        # Python 2 and 3 differ in the error contents you'll get when
        # attempting to load non-JSON data.
        if six.PY3:
            expected_error = 'Expecting value: line 1 column 1 (char 0)'
        else:
            expected_error = 'No JSON object could be decoded'

                'Could not parse validation info "%s": %s'
                % (validation_info.decode('utf-8'), expected_error),
            b'index %s..%s 100644\n'
        validation_info = self._base64_json({
        })
        validation_info = self._base64_json({
        })
            with self.siteconfig_settings({'diffviewer_max_diff_size': 1},
                                          reload_settings=False):

    def _base64_json(self, data):
        """Return a Base64-encoded JSON payload.

        Args:
            data (object):
                The data to encode to JSON.

        Returns:
            bytes:
            The Base64-encoded JSON payload.
        """
        return base64.b64encode(json.dumps(data).encode('utf-8'))