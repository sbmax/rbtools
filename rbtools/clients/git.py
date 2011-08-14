import sys

from rbtools.clients import SCMClient, RepositoryInfo
from rbtools.clients.svn import SVNClient, SVNRepositoryInfo
from rbtools.utils.checks import check_install
from rbtools.utils.process import die, execute


class GitClient(SCMClient):
    """
    A wrapper around git that fetches repository information and generates
    compatible diffs. This will attempt to generate a diff suitable for the
    remote repository, whether git, SVN or Perforce.
    """
    def __init__(self, **kwargs):
        super(GitClient, self).__init__(**kwargs)
        # Store the 'correct' way to invoke git, just plain old 'git' by
        # default.
        self.git = 'git'
    def get_repository_info(self):
        if not check_install('git --help'):
            # CreateProcess (launched via subprocess, used by check_install)
            # does not automatically append .cmd for things it finds in PATH.
            # If we're on Windows, and this works, save it for further use.
            if (sys.platform.startswith('win') and
                check_install('git.cmd --help')):
                self.git = 'git.cmd'
            else:
                return None
        git_dir = execute([self.git, "rev-parse", "--git-dir"],
                          ignore_errors=True).rstrip("\n")
        self.bare = execute([self.git, "config",
                             "core.bare"]).strip() == 'true'
        if not self.bare:
            os.chdir(os.path.dirname(os.path.abspath(git_dir)))
        self.head_ref = execute([self.git, 'symbolic-ref', '-q',
                                 'HEAD']).strip()
        # what it is. We'll try SVN first, but only if there's a .git/svn
        # directory. Otherwise, it may attempt to create one and scan
        # revisions, which can be slow.
        git_svn_dir = os.path.join(git_dir, 'svn')
        if os.path.isdir(git_svn_dir) and len(os.listdir(git_svn_dir)) > 0:
            data = execute([self.git, "svn", "info"], ignore_errors=True)
            m = re.search(r'^Repository Root: (.+)$', data, re.M)
                path = m.group(1)
                m = re.search(r'^URL: (.+)$', data, re.M)
                    base_path = m.group(1)[len(path):] or "/"
                    m = re.search(r'^Repository UUID: (.+)$', data, re.M)

                    if m:
                        uuid = m.group(1)
                        self.type = "svn"

                        # Get SVN tracking branch
                        if self._options.parent_branch:
                            self.upstream_branch = self._options.parent_branch
                        else:
                            data = execute([self.git, "svn", "rebase", "-n"],
                                           ignore_errors=True)
                            m = re.search(r'^Remote Branch:\s*(.+)$', data,
                                          re.M)

                            if m:
                                self.upstream_branch = m.group(1)
                            else:
                                sys.stderr.write('Failed to determine SVN '
                                                 'tracking branch. Defaulting'
                                                 'to "master"\n')
                                self.upstream_branch = 'master'

                        return SVNRepositoryInfo(path=path,
                                                 base_path=base_path,
                                                 uuid=uuid,
                                                 supports_parent_diffs=True)
            else:
                # Versions of git-svn before 1.5.4 don't (appear to) support
                # 'git svn info'.  If we fail because of an older git install,
                # here, figure out what version of git is installed and give
                # the user a hint about what to do next.
                version = execute([self.git, "svn", "--version"],
                                  ignore_errors=True)
                version_parts = re.search('version (\d+)\.(\d+)\.(\d+)',
                                          version)
                svn_remote = execute([self.git, "config", "--get",
                                      "svn-remote.svn.url"],
                                      ignore_errors=True)

                if (version_parts and
                    not self.is_valid_version((int(version_parts.group(1)),
                                               int(version_parts.group(2)),
                                               int(version_parts.group(3))),
                                              (1, 5, 4)) and
                    svn_remote):
                    die("Your installation of git-svn must be upgraded to "
                        "version 1.5.4 or later")
        merge = execute([self.git, 'config', '--get',
        remote = execute([self.git, 'config', '--get',
        url = None
        if self._options.repository_url:
            url = self._options.repository_url
        else:
            self.upstream_branch, origin_url = \
                self.get_origin(self.upstream_branch, True)

            if not origin_url or origin_url.startswith("fatal:"):
                self.upstream_branch, origin_url = self.get_origin()
            url = origin_url.rstrip('/')
        # Central bare repositories don't have origin URLs.
        # We return git_dir instead and hope for the best.
        url = origin_url.rstrip('/')
        if not url:
            url = os.path.abspath(git_dir)

            # There is no remote, so skip this part of upstream_branch.
            self.upstream_branch = self.upstream_branch.split('/')[-1]
        if url:
            return RepositoryInfo(path=url, base_path='',
        upstream_branch = (self._options.tracking or
                           default_upstream_branch or
                           'origin/master')
        origin_url = execute([self.git, "config", "--get",
                              "remote.%s.url" % upstream_remote],
                              ignore_errors=True).rstrip("\n")
        return (upstream_branch, origin_url)
        return ((actual[0] > expected[0]) or
                (actual[0] == expected[0] and actual[1] > expected[1]) or
                (actual[0] == expected[0] and actual[1] == expected[1] and
                 actual[2] >= expected[2]))
        server_url = super(GitClient, self).scan_for_server(repository_info)

        url = execute([self.git, "config", "--get", "reviewboard.url"],
                      ignore_errors=True).strip()
        if url:
            return url
            prop = SVNClient().scan_for_server_property(repository_info)
    def diff(self, args):
        """
        parent_branch = self._options.parent_branch

        self.merge_base = execute([self.git, "merge-base",
                                   self.upstream_branch,
                                   self.head_ref]).strip()

        if parent_branch:
            diff_lines = self.make_diff(parent_branch)
            parent_diff_lines = self.make_diff(self.merge_base, parent_branch)
        else:
            diff_lines = self.make_diff(self.merge_base, self.head_ref)
            parent_diff_lines = None
        if self._options.guess_summary and not self._options.summary:
            self._options.summary = execute([self.git, "log",
                                             "--pretty=format:%s",
                                             "HEAD^.."],
                                            ignore_errors=True).strip()
        if self._options.guess_description and not self._options.description:
            self._options.description = execute(
                [self.git, "log", "--pretty=format:%s%n%n%b",
                 (parent_branch or self.merge_base) + ".."],
                ignore_errors=True).strip()
        if commit:
            rev_range = "%s..%s" % (ancestor, commit)
        else:
            rev_range = ancestor
            diff_lines = execute([self.git, "diff", "--no-color",
                                  "--no-prefix", "--no-ext-diff", "-r", "-u",
                                  rev_range],
                                 split_lines=True)
            return execute([self.git, "diff", "--no-color", "--full-index",
                            "--no-ext-diff", rev_range])
        """
        rev = execute([self.git, "svn", "find-rev", parent_branch]).strip()
                # added/changed.

        # Make a parent diff to the first of the revisions so that we
        # never end up with broken patches:
        self.merge_base = execute([self.git, "merge-base",
                                   self.upstream_branch,
                                   self.head_ref]).strip()

            # Check if parent contains the first revision and make a
            # parent diff if not:
            pdiff_required = execute([self.git, "branch", "-r",
                                      "--contains", revision_range])
            parent_diff_lines = None

            if not pdiff_required:
                parent_diff_lines = self.make_diff(self.merge_base,
                                                   revision_range)

            if self._options.guess_summary and not self._options.summary:
                self._options.summary = execute(
                    [self.git, "log", "--pretty=format:%s",
                     revision_range + ".."],
                    ignore_errors=True).strip()

            if (self._options.guess_description and
                not self._options.description):
                self._options.description = execute(
                    [self.git, "log", "--pretty=format:%s%n%n%b",
                     revision_range + ".."],
                    ignore_errors=True).strip()

            return (self.make_diff(revision_range), parent_diff_lines)
            # Check if parent contains the first revision and make a
            # parent diff if not:
            pdiff_required = execute([self.git, "branch", "-r",
                                      "--contains", r1])
            parent_diff_lines = None

            if not pdiff_required:
                parent_diff_lines = self.make_diff(self.merge_base, r1)

            if self._options.guess_summary and not self._options.summary:
                self._options.summary = execute(
                    [self.git, "log",
                     "--pretty=format:%s", "%s..%s" % (r1, r2)],
                    ignore_errors=True).strip()

            if (self._options.guess_description and
                not self._options.description):
                self._options.description = execute(
                    [self.git, "log", "--pretty=format:%s%n%n%b",
                     "%s..%s" % (r1, r2)],
                    ignore_errors=True).strip()

            return (self.make_diff(r1, r2), parent_diff_lines)