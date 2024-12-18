import os.path

from src.dump_hls.main import StreamDumper

BASE_DIR = os.path.dirname(__file__)

if __name__ == '__main__':
    url = 'https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_adv_example_hevc/master.m3u8'
    d = StreamDumper(os.path.join(BASE_DIR, '../tests/output_data/server'))
    d.dump(url)
