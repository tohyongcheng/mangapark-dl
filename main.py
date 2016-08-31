"""
Mangapark-DL: Downloads manga and converts to PDF for the site www.mangapark.com

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


def parse_url_to_manga_info(url):
    """
    Extracts the title of a manga from an URL.
    :param url: a string that denotes the URL
    :return: the title of a manga
    """

    url = re.sub('http://', '', url)
    url = re.sub('mangapark.me/manga/', '', url)
    title = url.split("/")[0]
    return title


def parse_url_to_chapter_info(url):
    """
    Extract manga info from the URL, namely: ()
    :param url: a string that denotes the URL
    :return: 4-tuple containing the manga's title, version, chapter and url
    """

    url = re.sub("http://", '', url)
    url = re.sub("mangapark.me", '', url)
    url = re.sub("/manga/", '', url)

    if len(url.split("/")) == 3:
        title, version, chapter = url.split("/")
    elif len(url.split("/")) == 4:
        title, _, version, chapter = url.split("/")
    else:
        raise ValueError("Couldn't parse URL")

    return title, version, chapter, url


def ensure_directory_exist(directory):
    """
    Creates a directory, if it doesn't exist yet.
    :param directory: directory file path
    :return: None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_image(path):
    """
    Reads an image from the specified source.
    :param path: file path of the image
    :return: raw image data in byte[]
    """

    if path == '-':
        raw_data = sys.stdin.buffer.read()
    else:
        try:
            with open(path, "rb") as im:
                raw_data = im.read()
        except IsADirectoryError:
            raise argparse.ArgumentTypeError(
                "\"%s\" is a directory" % path)
        except PermissionError:
            raise argparse.ArgumentTypeError(
                "\"%s\" permission denied" % path)
        except FileNotFoundError:
            raise argparse.ArgumentTypeError(
                "\"%s\" does not exist" % path)

    if len(raw_data) == 0:
        raise argparse.ArgumentTypeError("\"%s\" is empty" % path)

    return raw_data


def convert_to_pdf(os_dir, chapter, file_names):
    """
    Converts a collection of images to PDF format
    :param os_dir: Directory to save PDF in.
    :param chapter: Title of the PDF.
    :param file_names: Images to construct the PDF from.
    :return:
    """

    print("Converting chapter %s to pdf..." % chapter)

    pdf_bytes = None

    try:
        pdf_bytes = img2pdf.convert(*[download_image(path) for path in file_names])
    except img2pdf.PdfTooLargeError:
        # Sometimes the images are registered as having a dpi of 1.
        # Because PDF has a limitation of 200 inches max per side, a
        # special layout_fun has to be used, as to prevent an exception.
        # default manga size 5"x7"

        layout_fun = img2pdf.get_layout_fun(pagesize=(None, img2pdf.in_to_pt(7)),
                                            imgsize=None, border=None,
                                            fit=img2pdf.FitMode.into,
                                            auto_orient=False)
        pdf_bytes = img2pdf.convert(*[download_image(path) for path in file_names],
                                    layout_fun=layout_fun)

    file = open("%s/%s.pdf" % (os_dir, chapter), "wb")
    file.write(pdf_bytes)
    print("Conversion completed!")


def download_chapter(url, height):
    """
    Downloads the chapter specified by the url into your file directory
    :param url: string denoting the url
    :param height: int denoting the height of the image you want to download in
    :return: None.

    """

    title, _, chapter, os_dir = parse_url_to_chapter_info(url)
    ensure_directory_exist(os_dir)
    try:
        page = urllib.request.urlopen(url)
    except ValueError:
        page = urllib.request.urlopen("http://mangapark.me" + url)

    soup = BeautifulSoup(page, "html.parser")
    imgs_wrappers = soup.find_all("a", {"class": "img-link"})
    file_names = []
    for i in imgs_wrappers:
        img_url = strip_parameters_from_url(i.img['src'])
        filename = img_url.split('/')[-1]
        print("Downloading %s %s %s..." % (title, chapter, filename))
        dir_filename = os_dir + "/" + os.path.basename(img_url)
        urllib.request.urlretrieve(img_url, dir_filename)
        new_dir_filename = resize(dir_filename, height)
        file_names.append(new_dir_filename)

    convert_to_pdf(os_dir, chapter, file_names)


def strip_parameters_from_url(url):
    """
    Parses the URL and strips away the parameters
    :param url: string URL with parameters
    :return: string URL without parameters
    """
    return re.sub(r'\?.*', '', url)


def resize(filename, height=None):
    """
    Resize the image to a certain proportion by height
    :param filename: string path of file to the image
    :param height: int
    :return: new filename of the image
    """
    if height is None:
        return filename
    print("Resizing %s to %spx height..." % (filename, height))
    with open(filename, 'r+b') as f:
        with Image.open(f) as image:
            cover = resizeimage.resize_height(image, height)
            new_filename = filename + '.res'
            cover.save(new_filename, image.format)
    return new_filename


def download_manga(url, chapter=None, min_max=None, height=None):
    """
    Downloads the chapters of a manga
    :param url: string url of the manga
    :param chapter: int chapter to download. if no chapter is specified, the min_max parameter is used.
    :param min_max: the inclusive range of chapters to download, e.g [1,10] -> chapters 1 to 10
    :param height: The height to witch resize all images (keeping the aspect ratio)
    :return: None
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
        chapter_no = float(parse_url_to_chapter_info(chapter_url)[2][1:])

        if chapter and chapter_no == chapter:
            download_chapter(chapter_url, height)
            break
        elif min_max and min_max[0] <= chapter_no <= min_max[1]:
            download_chapter(chapter_url, height)


def main():
    """
    Downloads manga specified in command line based on the following arguments:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--manga-url', help="The url of the mangapark manga to download")
    parser.add_argument('-s', '--size', '--height', type=int,
                        help='Height to resize images to (it will keep the aspect ratio)')
    parser.add_argument('-c', '--chapter', help="The chapter number that you specifically want to download")
    parser.add_argument('-cs', '--chapters', nargs=2, help="An inclusive range of chapters you want to download")

    args = parser.parse_args()
    print(args)

    if args.manga_url is None:
        print("Please specify the URL of the manga on mangapark.me")
        return

    elif args.chapters is not None:
        assert isinstance(args.chapters, list)
        download_manga(args.manga_url, min_max=[float(x) for x in args.chapters], height=args.size)

    elif args.chapter is not None:
        download_manga(args.manga_url, chapter=int(args.chapter), height=args.size)


if __name__ == "__main__":
    main()
