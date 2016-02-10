# Introduction

A script to download your favourite mangas on mangapark.me and convert them to .pdf formats.

## Instructions

```
# Download chapter 20 for the manga Ajin Miura Tsuina
$ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ -chapter 20

# Download chapters 19 to 40 for the manga Ajin Miura Tsuina
$ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ -chapters 19 40
```

## Dependencies

- Python 3
- img2pdf
- BeautifulSoup4