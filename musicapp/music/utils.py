from django.utils.html import format_html
import datetime

def get_image_preview(obj, size):
    """
    Returns an HTML image tag for an object's image.

    Parameters:
    obj (Model instance): The Django model instance that contains the image.
    size (int): The width and height of the preview image in pixels.

    Returns:
    str: An HTML string containing an <img> tag for rendering in Django Admin.
    """
    return format_html(
        '<img src="{}" width="{}" height="{}" style="border-radius: 5px;" />',
        obj.get_image(), size, size
    )


def parse_release_date(value):
        if len(value) == 4:
            value = f"{value}-01-01"

        return datetime.datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()


def milliseconds_to_timedelta(milliseconds: int) -> datetime.timedelta:
    return datetime.timedelta(milliseconds=milliseconds)
