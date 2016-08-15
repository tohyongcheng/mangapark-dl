"""Mangapark downloader.

Example:
    Download chapter 20 for the manga Ajin Miura Tsuina

        $ python3 main.py -m http://mangapark.me/manga/ajin-miura-tsuina/ -chapter 20
"""
import re
import os
import sys
import argparse
import urllib.request
import img2pdf
from bs4 import BeautifulSoup
from PIL import Image
from resizeimage import resizeimage

def parse_url_to_manga_info(url: str) -> str:
    """Extracts the title of a manga from an URL.
    """
    url = re.sub('http://', '', url)
    url = re.sub('mangapark.me/manga/', '', url)
    title = url.split("/")[0]
    return title


def parse_url_to_chapter_info(url: str) -> (str, str, str, str):
    """Extract manga info from the URL.

    Returns:
        4-tuple containing the mangas title, version, chapter and url
    """
    url = re.sub("http://", '', url)
    url = re.sub("mangapark.me", '', url)
    url = re.sub("/manga/", '', url)

    # compensate for mangapark's different url formatting schemes
    title, version, chapter = None, None, None
    if len(url.split("/")) == 3:
        title, version, chapter = url.split("/")
    elif len(url.split("/")):
        title, _, version, chapter = url.split("/")
    else:
        raise ValueError("Couldn't parse URL")

    return title, version, chapter, url


def ensure_directory_exist(directory: str) -> None:
    """Creates a directory, if it doesn't exist yet."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def input_images(path: str) -> bytes:
    """Reads an image from the specified source.

    Args:
        path: The path of the image.

    Returns:
        The raw image data.
    """
    if path == '-':
        rawdata = sys.stdin.buffer.read()
    else:
        try:
            with open(path, "rb") as im:
                rawdata = im.read()
        except IsADirectoryError:
            raise argparse.ArgumentTypeError(
                "\"%s\" is a directory" % path)
        except PermissionError:
            raise argparse.ArgumentTypeError(
                "\"%s\" permission denied" % path)
        except FileNotFoundError:
            raise argparse.ArgumentTypeError(
                "\"%s\" does not exist" % path)
    if len(rawdata) == 0:
        raise argparse.ArgumentTypeError("\"%s\" is empty" % path)
    return rawdata


def convert_to_pdf(os_dir: str, chapter: str, filenames: list) -> None:
    """Converts images to a PDF.

    Args:
        os_dir: Directory to save PDF in.
        chapter: Title of the PDF.
        filenames: Images to construct the PDF from.
    """
    print("Converting chapter %s to pdf..." % chapter)

    pdf_bytes = None
    try:
        pdf_bytes = img2pdf.convert(*[input_images(path) for path in filenames])
    except img2pdf.PdfTooLargeError:
        # Sometimes the images are registered as having a dpi of 1.
        # Because PDF has a limitation of 200 iches max per side, a
        # special layout_fun has to be used, as to prevent an exception.

        # default manga size 5"x7"
        layout_fun = img2pdf.get_layout_fun(pagesize=(None, img2pdf.in_to_pt(7)),
                                            imgsize=None, border=None,
                                            fit=img2pdf.FitMode.into,
                                            auto_orient=False)
        pdf_bytes = img2pdf.convert(*[input_images(path) for path in filenames],
                                    layout_fun=layout_fun)

    file = open("%s/%s.pdf" % (os_dir, chapter), "wb")
    file.write(pdf_bytes)
    print("Conversion completed!")


def download_chapter(url: str, height: int) -> None:
    """Downloads the chapter specified by the url."""
    title, _, chapter, os_dir = parse_url_to_chapter_info(url)
    ensure_directory_exist(os_dir)
    try:
        page = urllib.request.urlopen(url)
    except ValueError:
        page = urllib.request.urlopen("http://mangapark.me" + url)

    soup = BeautifulSoup(page, "html.parser")
    imgs_wrappers = soup.find_all("a", {"class": "img-link"})
    filenames = []
    for i in imgs_wrappers:
        img_url = i.img['src']
        filename = img_url.split('/')[-1]
        print("Downloading %s %s %s..." % (title, chapter, filename))
        dir_filename = os_dir + "/" + os.path.basename(img_url)
        urllib.request.urlretrieve(img_url, dir_filename)
        new_dir_filename = resize(dir_filename, height)
        filenames.append(new_dir_filename)

    convert_to_pdf(os_dir, chapter, filenames)

def resize(filename: str, height: int) -> str:
    if height == None:
        return filename
    print("Resizing %s to %spx height..." % (filename, height))
    with open(filename, 'r+b') as f:
        with Image.open(f) as image:
            cover = resizeimage.resize_height(image, height)
            new_filename = filename + '.res';
            cover.save(new_filename, image.format)
    return new_filename

def download_manga(url: str, chapter: int=None, min_max: (int, int)=None, height: int=None) -> None:
    """Downloads chapters of a manga.

    Args:
        url: The URL of the manga.
        chapter: The chapter to download.  If no chapter is specified, the
            min_max parameter will be used.
        min_max: The range of chapters to download.
        height: The height to witch resize all images (keeping the aspect ratio)
    """
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, "html.parser")

    streams = soup.find_all("div", {"class": "stream"})
    stream_lens = []
    for stream in streams:
        chapters = stream.find_all("li")
        stream_lens += [len(chapters)]

    max_stream_len = max(stream_lens)
    max_idx = stream_lens.index(max_stream_len)
    best_stream = streams[max_idx]

    chapters = best_stream.find_all("li")
    for c in chapters[::-1]:
        chapter_url = c.em.find_all("a")[-1]['href']
        chapter_no = float(parse_url_to_chapter_info(chapter_url)[2][1: ])
        if chapter and chapter_no == chapter:
            download_chapter(chapter_url, height)
            break
        if min_max and chapter_no >= min_max[0] and chapter_no <= min_max[1]:
            download_chapter(chapter_url, height)
            continue


def main():
    """Downloads manga specified in command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--manga-url')
    parser.add_argument('-s', '--size', '--height', type=int, help='Height to resize images to (it will keet the aspect ratio)')
    parser.add_argument('-c', '--chapter')
    parser.add_argument('-cs', '--chapters', nargs=2)

    args = parser.parse_args()
    print(args)
    if args.manga_url is None:
        print("Please specify the URL of the manga on mangapark.me")
        return
    elif args.chapters != None:
        assert isinstance(args.chapters, list)
        download_manga(args.manga_url, min_max=[float(x) for x in args.chapters], height=args.size)
    elif args.chapter != None:
        download_manga(args.manga_url, chapter=int(args.chapter), height=args.size)


if __name__ == "__main__":
    main()
