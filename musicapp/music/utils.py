from django.utils.html import format_html


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


def image_preview_list(obj):
    """Returns a smaller image preview (50x50)"""
    return get_image_preview(obj, 50)


def image_preview_detail(obj):
    """Returns a larger image preview (500x500)"""
    return get_image_preview(obj, 500)
