""""""
import os.path

import pytest

import src.dump_hls.release as r

BASE_DIR = os.path.dirname(__file__)


@pytest.mark.parametrize(
    ["versions", 'msg', 'no_error'],
    [
        ([
             '1.2.3',
             '1.2.3-alpha.0',
             '1.2.3-alpha.1',
             '1.2.3-beta.0',
             '1.2.3-beta.1',
         ], '', True),
        ([
             '1,2',
             '1.4',
             '01.32.5',
             'a.b.c'
         ], 'Main version part should be like `major.minor.patch`. Each part should be integer without leading 0.',
         False),
        (['1.2.3-al-al'], "There should at most be 1 `-` in the version name, but 2 are given.", False),
        (['1.2.3-al3'], "Prerelease part should be like `<pre_release_type>.<pre_release_number>`.", False),
        (['1.2.3-bd.3'], "Pre-release type could only be {'alpha', 'beta'}", False),
        (['1.2.3-alpha.b'], "Pre-release number should be an integer without leading 0.", False),
        (['1.2.3-alpha.05'], "Pre-release number should be an integer without leading 0.", False),
    ]
)
def test_validate_version(versions, msg, no_error):
    if no_error:
        for v in versions:
            r.validate_version(v)
    else:
        for v in versions:
            with pytest.raises(ValueError) as cm:
                r.validate_version(v)
            assert f"Invalid version: `{v}`.\n{msg}" == cm.value.args[0]
