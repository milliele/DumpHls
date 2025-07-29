import os.path
import pathlib
import shutil

import pytest

from src.dump_hls.main import *

BASE_DIR = os.path.dirname(__file__)


class TestHlsLine:
    def test_dummy(self):
        # just for coverage
        HlsLine(HlsLineType.TAG, '1', dict(b=1), value='123')

    @pytest.mark.parametrize('line,type,tag,value,attributes', [
        ('#EXTM3U', HlsLineType.TAG, 'EXTM3U', '', None),
        ('#EXT-X-PROGRAM-DATE-TIME:2023-03-14T18:00:02.628Z', HlsLineType.TAG, 'EXT-X-PROGRAM-DATE-TIME', '',
         {None: '2023-03-14T18:00:02.628Z'}),
        ('#EXTINF:5.005,', HlsLineType.TAG, 'EXTINF', '', {None: '5.005'}),
        ('#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac-64k",DEFAULT=YES,URI="audio-1-64K/64_slide.m3u8"', HlsLineType.TAG,
         'EXT-X-MEDIA', '', {
             'TYPE': 'AUDIO',
             'GROUP-ID': 'aac-64k',
             'DEFAULT': 'YES',
             'URI': 'audio-1-64K/64_slide.m3u8',
         }),
        ('cmaf-cenc-ctr-3500K/3500_slide.m3u8 ', HlsLineType.URI, '', 'cmaf-cenc-ctr-3500K/3500_slide.m3u8', None),
        ('#  12312konfsap', HlsLineType.COMMENT, '', '  12312konfsap', None),
        ('     ', HlsLineType.BLANK, '', '', None),
    ])
    def test_create(self, line, type, tag, value, attributes):
        ans = HlsLine.parse(line)
        assert ans.tag == tag
        assert ans.type == type
        assert ans.value == value
        if attributes is None:
            attributes = {}
        assert ans.attributes == attributes


class TestStreamDumper:
    @pytest.fixture
    def dumper(self):
        path = os.path.join(BASE_DIR, '../output_data/server')
        yield StreamDumper(path)
        shutil.rmtree(path)

    def test_constructor(self):
        # str
        a = StreamDumper(BASE_DIR)
        assert isinstance(a.parent_dir, pathlib.Path)
        assert os.path.abspath(BASE_DIR) == str(a.parent_dir.resolve())

        # path
        a = StreamDumper(pathlib.Path('123/355'))
        assert isinstance(a.parent_dir, pathlib.Path)
        assert '123/355' == str(a.parent_dir)

    def test_reset(self):
        a = StreamDumper('a')
        assert 0 == len(a.known_domain_names)
        a.known_domain_names = 212123
        with pytest.raises(TypeError):
            d = len(a.known_domain_names)
        a.reset()
        assert 0 == len(a.known_domain_names)

    def test_get_fs_path(self):
        url = 'http://example.com/a/b/c/d.mp4?a=text&q2=text2&q3=text3&q2=text4'
        d = StreamDumper('abc')
        ans = pathlib.Path('abc/example.com/a/b/c/d.mp4').resolve()
        assert ans == d.get_fs_path(url).resolve()

    def test_download_file(self, dumper):
        url = 'https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_adv_example_hevc/master.m3u8'
        fs_path = dumper.download_file(url, update=False)
        ans_local_path = os.path.join(BASE_DIR,
                                      '../output_data/server/devstreaming-cdn.apple.com/videos/streaming/examples'
                                      '/bipbop_adv_example_hevc/master.m3u8')
        assert os.path.abspath(ans_local_path) == str(fs_path.resolve())
        assert 'devstreaming-cdn.apple.com' in dumper.known_domain_names

        mtime = os.path.getmtime(str(fs_path))
        fs_path2 = dumper.download_file(url, update=False)
        assert fs_path == fs_path2
        assert os.path.getmtime(str(fs_path)) == mtime

        # update
        fs_path2 = dumper.download_file(url, update=True)
        assert fs_path == fs_path2
        assert os.path.getmtime(str(fs_path)) > mtime

    @pytest.mark.parametrize("payload, url, expected", [
        (
                "#EXTM3U\n#EXTINF:10,\nhttp://example.com/segment1.ts\n#EXTINF:10,\nhttp://example.com/segment2.ts\n",
                "http://example.com/playlist.m3u8",
                {
                    "playlists": [],
                    "files": ["http://example.com/segment1.ts", "http://example.com/segment2.ts"]
                }
        ),
        (
                "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\nhttp://example.com/low.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2560000\nhttp://example.com/mid.m3u8\n",
                "http://example.com/master.m3u8",
                {
                    "playlists": ["http://example.com/low.m3u8", "http://example.com/mid.m3u8"],
                    "files": []
                }
        ),
        (
                "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\nhttp://example.com/low.m3u8\n#EXTINF:10,\nhttp://example.com/segment1.ts\n",
                "http://example.com/playlist.m3u8",
                {
                    "playlists": ["http://example.com/low.m3u8"],
                    "files": ["http://example.com/segment1.ts"]
                }
        ),
        (
                "#EXTM3U\n#EXTINF:10,\ninvalid_url\n#EXTINF:10,\nhttp://example.com/segment2.ts\n",
                "http://example.com/playlist.m3u8",
                {
                    "playlists": [],
                    "files": ["http://example.com/segment2.ts"]
                }
        ),
    ], ids=[
        "valid_playlist",
        "nested_playlists",
        "mixed_content",
        "invalid_urls"
    ])
    def test_parse_playlist(self, payload, url, expected):
        result = StreamDumper.parse_playlist(payload, url)
        assert result == expected
