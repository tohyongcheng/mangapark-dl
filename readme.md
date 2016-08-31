# Introduction

A script to download your favourite mangas on mangapark.me and convert them to `.pdf` formats.

## Instructions

```
# Download chapter 20 for the manga Ajin Miura Tsuina 
$ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ --chapter 20 --size 1000

# Download chapters 19 to 22 for the manga Ajin Miura Tsuina very small
$ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ --chapters 19 22 --size 300
```

`--size` is optional on both ways of downloading. Without it, it will not resize.
_Sometimes the `img2pdf` will fail due to the size of the original downloaded images. I recommend `--size 1000`_

## System Dependencies

- Python 3


## TODOs
[] Create a python plugin to easily download manga
[] Create tests
[] Enable Python 2 Support
[] Enable support to place in Dropbox
[] Continue download from where it is left off?


