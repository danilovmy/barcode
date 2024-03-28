from django.http import HttpResponse
from io import BytesIO
from PIL import Image
import treepoem
import re


def is_valid_color(color_value):
    rgb_pattern = re.compile(r'^[0-9A-Fa-f]{6}$')
    cmyk_pattern = re.compile(r'^[0-9A-Fa-f]{8}$')
    return bool(rgb_pattern.match(color_value) or cmyk_pattern.match(color_value))


def generate_barcode(request):
    code = request.GET.get('code', '')
    image_type = request.GET.get('image_type', 'png').lower()
    foreground_color = request.GET.get('foreground', '000000')
    background_color = request.GET.get('background', 'ffffff')

    if not is_valid_color(foreground_color) or not is_valid_color(background_color):
        return HttpResponse("Foreground and background colors must be valid hex RRGGBB or CCMMYYKK values.", status=400)

    if image_type not in ['png', 'svg']:
        return HttpResponse("Image type must be either 'png' or 'svg'.", status=400)

    try:
        height = float(request.GET.get('height', 25.4))/25.4
        width = float(request.GET.get('width', 25.4))/25.4
        if height <= 0 or width <= 0:
            return HttpResponse("Height and width must be numbers greater than zero.", status=400)
    except ValueError:
        return HttpResponse("Height and width must be valid numbers.", status=400)

    try:
        image = treepoem.generate_barcode(barcode_type='ean8', data=code,
                                          options={"includetext": True, "height": height, "width": width, "scale": 2,
                                                   "barcolor": foreground_color, "textcolor": foreground_color,
                                                   "backgroundcolor": background_color})
        if image_type == 'png':
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)  # Rewind the buffer
            return HttpResponse(buffer.getvalue(), content_type='image/png')
        elif image_type == 'svg':
            buffer.seek(0)  # Reset buffer position
            image = Image.open(buffer)
            # Treepoem generates SVG as a byte string
            return HttpResponse(image, content_type='image/svg+xml')
    except Exception as e:
        return HttpResponse(f"Error generating barcode: {e}", status=500)

