import argparse
import os
import time
from mhgui_downloader.extractor import MHGMetaFetcher, InvalidResponse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, required=True, help='URL to specific series comic book on Manhuagui')
    parser.add_argument('--delay', type=float, required=False, default=1, help='Delay seconds before downloading next page')
    parser.add_argument('--dry', action='store_true', help='Just parse meta info, will not download pages')
    parser.add_argument('--output', type=str, default='.', help='Output folder, the default is .')
    parser.add_argument('--num_max_retry', type=int, default=10, help='Upper bound of retry while downloading page')
    args = parser.parse_args()
    output_folder = args.output

    if not os.path.exists(output_folder):
        print(f'{output_folder} does not exist')
        return
    elif not os.path.isdir(output_folder):
        print(f'{output_folder} is not a folder')
        return

    if args.delay < 0.5:
        print(f'delay with {args.delay} seconds is too short')
        return
        
    fetcher = MHGMetaFetcher(args.url)

    for i, _ in enumerate(fetcher.volumes):
        vol_info = fetcher.get_volume_infos(i)
        vol_name = vol_info['cname']
        folder = os.path.join(output_folder, vol_name)

        if not os.path.exists(folder):
            os.mkdir(folder)

        num_pages = len(vol_info['files'])
        print(f'{num_pages} pages to be downloaded for {vol_name}')

        for j, p_name in enumerate(vol_info['files']):
            ext = p_name.split('.')[-1]
            page_path = os.path.join(folder, f'{j:04}.{ext}')
            print(f'Downloading {vol_name} page {j} to {page_path}')

            if os.path.exists(page_path) and os.path.isfile(page_path):
                print(f'{page_path} already exists, skip')
                continue

            if not args.dry:
                for _ in range(max(args.num_max_retry, 1)):
                    try:
                        content = fetcher.get_volume_page_content(i, j)
                        with open(page_path, 'wb') as f:
                            f.write(content)
                        break
                    except InvalidResponse:
                        print(f'Encounter error while downloading volume {i} page {j}, retry now')
                        time.sleep(1)
                    except:
                        print(f'Encounter unknown error while processing volume {i} page {j}, retry now')
                        time.sleep(1)
                else:
                    print(f'Unable to download volume {i} page {j}')

            time.sleep(args.delay)

if __name__ == '__main__':
    main()
