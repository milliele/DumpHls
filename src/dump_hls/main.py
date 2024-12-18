import asyncio
import logging
import os.path
import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List
from urllib.parse import urlparse, urljoin

import aiohttp
import joblib
import requests
from tqdm import tqdm

__all__ = [
    'HlsLine',
    'HlsLineType',
    'StreamDumper'
]

TAG_PREFIX = 'EXT'
DOWNLOAD_BLOCK_SIZE = 1024

logger = logging.getLogger('DumpHls')


class HlsTag(Enum):
    EXTINF = 'EXTINF'


class HlsLineType(Enum):
    TAG = 0
    URI = 1
    COMMENT = 2
    BLANK = 3


@dataclass
class HlsLine:
    type: HlsLineType = HlsLineType.BLANK
    tag: str = ''
    attributes: dict = None
    value: str = ''

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

    @staticmethod
    def _parse_attributes(attr_str):
        def clear_quote(value):
            if value.startswith('"'):
                return value[1:-1]
            return value

        attrs = {}
        l, attr_name, in_quote = 0, None, False
        for r, c in enumerate(attr_str):
            if c == '=':
                attr_name = attr_str[l:r]
                l = r + 1
            elif c == ',' and not in_quote:
                attrs[attr_name] = clear_quote(attr_str[l:r])
                attr_name = None
                l = r + 1
            elif c == '"':
                in_quote = not in_quote
        else:
            val = clear_quote(attr_str[l:])
            if len(val) > 0:
                attrs[attr_name] = val
        return attrs

    @staticmethod
    def parse(line):
        line = line.strip()
        res = HlsLine()
        if line.startswith('#'):
            line = line[1:]
            parts = line.split(':', maxsplit=1)
            if parts[0].startswith(TAG_PREFIX):
                res.type = HlsLineType.TAG
                res.tag = parts[0]
                if len(parts) > 1:
                    res.attributes = HlsLine._parse_attributes(parts[1])
            else:
                res.type = HlsLineType.COMMENT
                res.value = line
        elif len(line) > 0:
            res.type = HlsLineType.URI
            res.value = line
        else:
            res.type = HlsLineType.BLANK
        return res


class DownloadMode(Enum):
    SEQUENTIAL = 0
    ASYNC = 1
    MULTIPROCESS = 2


class StreamDumper:
    def __init__(self, parent_dir):
        if not isinstance(parent_dir, pathlib.Path):
            parent_dir = pathlib.Path(parent_dir)
        self.parent_dir = parent_dir

        # state
        self.known_domain_names = set()

    def reset(self):
        self.known_domain_names = set()

    def get_fs_path(self, url: str) -> pathlib.Path:
        """

        Args:
            url: this should be an absolute path including the domain name

        Returns:

        """
        parsed = urlparse(url)
        return self.parent_dir.joinpath(parsed.netloc, parsed.path.strip('/'))

    def download(self, url, dest: pathlib.Path, *, show_progress=False):
        res = requests.get(url, stream=show_progress)
        res.raise_for_status()
        total_size = int(res.headers.get('content-length', 0))

        dest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        if show_progress:
            # TODO: fix multiple progress bar
            with open(dest, 'wb') as file, tqdm(
                    desc=str(dest.relative_to(self.parent_dir)),
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for data in res.iter_content(DOWNLOAD_BLOCK_SIZE):
                    bar.update(len(data))
                    file.write(data)
        else:
            dest.write_text(res.text)

    def download_file(self, url, *, update: bool = False, show_progress: bool = False) -> pathlib.Path:
        """Make sure the file is stored locally.

        Args:
            url: should be an absolute URL with the domain name
            update: if true, even when the file path has the content, the stream dumper will still download the file \
                    and update the local file.

        Returns:
            the path to the local file
        """
        fs_path = self.get_fs_path(url)
        if not fs_path.exists() or update:
            self.known_domain_names |= {urlparse(url).netloc}
            self.download(url, fs_path, show_progress=show_progress)
        assert fs_path.exists(), f"There should be a file under {fs_path.absolute()}"
        return fs_path

    @staticmethod
    def parse_playlist(payload: str, url: str) -> Dict[str, List[str]]:
        """Parse the playlist and get other files needed to be downloaded.

        Args:
            payload: the content of the playlist
            url: the url of this playlist

        Returns:
            Key ``playlists`` refers to all the playlist that needs parsing, and "files" refers to all the files \
            that need downloading.
        """
        lines = [HlsLine.parse(l) for l in payload.split('\n')]
        urls = []
        for line in lines:
            if line.type == HlsLineType.TAG:
                uri = line.attributes.get('URI', None)
                if uri is not None:
                    urls.append(uri)
            elif line.type == HlsLineType.URI:
                urls.append(line.value)

        playlists = set()
        files = set()
        for uri in urls:
            parsed = urlparse(uri)
            _, ext = os.path.splitext(parsed.path)
            if not (parsed.scheme in {'http', 'https'} or (parsed.netloc == '' and ext != '')): continue
            if parsed.netloc != '' and parsed.netloc != urlparse(url).netloc:
                logger.warning(f"Absolute URL under other domain name found: {uri}")
            full = urljoin(url, uri)
            if ext.lower() in {'.m3u8', '.m3u'}:
                playlists.add(full)
            else:
                files.add(full)
        logger.critical(f"{len(playlists)} playlists and {len(files)} files found.")
        return dict(playlists=list(sorted(playlists)), files=list(sorted(files)))

    async def download_and_parse_playlist_async(self, session: aiohttp.ClientSession, url: str, *,
                                                update: bool = False) -> Dict[str, List[str]]:
        """Make sure the file is stored locally.

        Args:
            session: the aiohttp session
            url: should be an absolute URL with the domain name
            update: if true, even when the file path has the content, the stream dumper will still download the file \
                    and update the local file.

        Returns:
            Key ``playlists`` refers to all the playlist that needs parsing, and "files" refers to all the files \
            that need downloading.
        """
        logger.critical(f"Downloading and Parsing: {url}")
        fs_path = self.get_fs_path(url)
        content = ''
        if not fs_path.exists() or update:
            self.known_domain_names |= {urlparse(url).netloc}
            async with session.get(url, ssl=False) as res:
                res.raise_for_status()
                content = await res.text()
                fs_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                fs_path.write_text(content)
        else:
            content = fs_path.read_text()
        return StreamDumper.parse_playlist(content, url)

    async def download_and_parse_playlists_async(self, urls, *, update=False):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                tasks.append(self.download_and_parse_playlist_async(session, url, update=update))
            return await asyncio.gather(*tasks)

    def download_and_parse_playlist(self, url, *, update=True):
        logger.critical(f'Downloading and Parsing: {url}')
        fs_path = self.download_file(url, update=update, show_progress=False)
        content = fs_path.read_text()
        return StreamDumper.parse_playlist(content, url)

    def download_and_parse_playlists(self, urls: List[str], *, update: bool = False, is_async: bool = False):
        if is_async:
            return asyncio.run(self.download_and_parse_playlists_async(urls, update=update))
        return [self.download_and_parse_playlist(url, update=update) for url in urls]

    def download_files(self, urls, *, update=False, n_proc=-1):
        joblib.Parallel(n_jobs=n_proc, verbose=1)(
            joblib.delayed(self.download_file)(url, update=update, show_progress=True) for url in urls)

    def dump(self, master_url, *, update=False, n_proc=-1):
        self.reset()

        files = set()

        # master
        media = self.download_and_parse_playlists([master_url], update=update, is_async=False)[0]
        files |= set(media['files'])

        # media
        segments = self.download_and_parse_playlists(media['playlists'], update=update)
        for segment in segments:
            files |= set(segment['files'])
            assert segment['playlists'] == [], "There should be no playlist found in the media playlist."
        self.download_files(files, update=update, n_proc=n_proc)
