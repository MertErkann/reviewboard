import requests
                                repository.encoding, local_site_name)
    def parse_diff_revision(self, file_str, revision_str, moved):
        elif revision != PRE_CREATION and not moved and revision != '':
            # Moved files with no changes has no revision,
            # so don't validate those.
        # Parse the extended header to save the new file, deleted file,
        # mode change, file move, and index.
        elif self._is_moved_file(linenum):
            file_info.data += self.lines[linenum] + "\n"
            file_info.data += self.lines[linenum + 1] + "\n"
            file_info.data += self.lines[linenum + 2] + "\n"
            linenum += 3
            file_info.moved = True
    def _is_moved_file(self, linenum):
        return (self.lines[linenum].startswith("similarity index") and
                self.lines[linenum + 1].startswith("rename from") and
                self.lines[linenum + 2].startswith("rename to"))

                 encoding='', local_site_name=None):
        self.encoding = encoding
        logging.info('Fetching file from %s' % url)

        auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        if self.encoding:
            response.encoding = self.encoding
        return response.text
                # We want to make sure we can access the file successfully,
                # without any HTTP errors. A successful access means the file
                # exists. The contents themselves are meaningless, so ignore
                # them. If we do successfully get the file without triggering
                # any sort of exception, then the file exists.
                self._get_file(url)

                return True