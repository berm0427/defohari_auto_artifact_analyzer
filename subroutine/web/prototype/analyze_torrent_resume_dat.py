import bencode
import datetime


def analyze_resume_dat(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    decoded = bencode.decode(data)

    for torrent_hash, torrent_info in decoded.items():
        if isinstance(torrent_info, dict):
            print(f"Torrent Hash: {torrent_hash}")

            if 'caption' in torrent_info:
                caption = torrent_info['caption']
                if isinstance(caption, bytes):
                    caption = caption.decode('utf-8', errors='ignore')
                print(f"  Caption: {caption}")

            if 'path' in torrent_info:
                path = torrent_info['path']
                if isinstance(path, bytes):
                    path = path.decode('utf-8', errors='ignore')
                print(f"  Path: {path}")

            if 'added_on' in torrent_info:
                added_on = datetime.datetime.fromtimestamp(torrent_info['added_on'])
                print(f"  Added on: {added_on}")

            if 'completed_on' in torrent_info:
                if torrent_info['completed_on'] == 0:
                    print("  Completed on: Not completed")
                else:
                    completed_on = datetime.datetime.fromtimestamp(torrent_info['completed_on'])
                    print(f"  Completed on: {completed_on}")

            if 'downloaded' in torrent_info:
                print(f"  Downloaded: {torrent_info['downloaded']} bytes")

            if 'uploaded' in torrent_info:
                print(f"  Uploaded: {torrent_info['uploaded']} bytes")

            if 'created_torrent' in torrent_info:
                if torrent_info['created_torrent'] == 1:
                    print("  Created and Distributed")
                else:
                    print("  Downloaded")

            print()


if __name__ == "__main__":
    resume_dat_path = r"resume.dat"
    analyze_resume_dat(resume_dat_path)