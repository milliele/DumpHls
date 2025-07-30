"""
This module contains all the information related to the current release of the
library including descriptions, version number, authors and contact
information.
"""
import sys

# module information
name = 'dump_hls'

# author information.
# Used by __init__, doc and setup
author = 'milliele'
author_email = 'milliele@qq.com'
maintainer = 'milliele'
maintainer_email = 'milliele@qq.com'

description_short = 'A python package to dump any HLS stream as it is'

# URL
url = 'https://github.com/milliele/DumpHls'

# ======================= gitRelease information =============================
version = '1.0.1'
"""Version information, used by __init__, doc, setup and gitRelease"""
release_name = f"v{version}"
"""The release title"""
release_body = """
1. v1.0.0 is incorrect on PyPI, upload a new version to fix the issue.
""".strip()
"""The release body"""
is_draft = False
"""Is this github release a draft"""
is_prerelease = False
"""Is this github release a prerelease"""


# ============================================================================

def validate_version(version):
    try:
        parts = version.split('-')
        main = parts[0]
        # validate main version
        try:
            major, minor, patch = main.split('.')
            assert ".".join(map(str, map(int, [major, minor, patch]))) == main
        except Exception as e:
            raise ValueError('Main version part should be like `major.minor.patch`. '
                             'Each part should be integer without leading 0.')
        # validate prerelease
        if len(parts) > 1:
            assert len(parts) == 2, ("There should at most be 1 `-` in the version name, "
                                     f"but {len(parts) - 1} are given.")
            try:
                pre_l, pre_n = parts[1].split('.')
            except Exception as e:
                raise ValueError('Prerelease part should be like `<pre_release_type>.<pre_release_number>`.')
            assert pre_l in {'alpha', 'beta'}, "Pre-release type could only be {'alpha', 'beta'}"
            assert pre_n.isdigit() and str(int(pre_n)) == pre_n, \
                "Pre-release number should be an integer without leading 0."
    except Exception as e:
        raise ValueError(f'Invalid version: `{version}`.\n'
                         f'{e}')


validate_version(version)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        attr_name = sys.argv[1]
        if attr_name in globals():
            print(globals()[attr_name])
