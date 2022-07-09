# mhgui-downloader
Yet another Python manhuagui downloader.

# Sample Usage
```bash
python main.py --url=<manga_url>
```

this will download the all the corresponding manga series to CWD.

# Arguments
 - `--url` - URL to specific manga series on manhuagui
 - `--delay` - Delay seconds before downloading next page
 - `--dry` - Just parse meta info, will not download pages
 - `--output` - Output folder, the default is `.`
 - `--num_max_retry` - Upper bound of retry while downloading page. Default is 10, value <= 0 behaves as same as 1.

# Todo
 - Proxy support