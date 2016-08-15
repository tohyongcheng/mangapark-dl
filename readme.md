# Introduction

A script to download your favourite mangas on mangapark.me and convert them to .pdf formats.

## Instructions

```
# Download chapter 20 for the manga Ajin Miura Tsuina 
$ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ -chapter 20 --size 1000

# Download chapters 19 to 40 for the manga Ajin Miura Tsuina
$ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ -chapters 19 40 --size 1000
```

You can add the argument `--size` to both ways of downloading, to change the height of the downloaded images.
_Sometimes the `img2pdf` will fail due to the size of the original downloaded images. I recommend `--size 1000`_

## Dependencies

- Python 3
- img2pdf
- BeautifulSoup4
- python-resize-image
