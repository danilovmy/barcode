# Create your views here.
from django.http import HttpResponse
from django.conf import settings

from base64 import b64encode
from reportlab.graphics.shapes import Rect, Drawing
from reportlab.graphics import renderSVG, renderPM
from reportlab.graphics.barcode import eanbc, qr
from reportlab.lib.colors import HexColor
from django import forms
from django.views.generic import FormView
from django.core.validators import RegexValidator, MinValueValidator

ColorValidator = RegexValidator(regex=r'^0x[0-9A-Fa-f]{6}$|^0x[0-9A-Fa-f]{8}$', message = "Color must be valid hex color or color and alpha in 0xRRGGBB or 0xRRGGBBDD format.")
PositiveValidator = MinValueValidator(0, message="Height and width must be numbers greater than zero.")


class BarcodeSettingsForm(forms.Form):
    CONTENT_TYPES = {'png':'image/png', 'svg': 'image/svg+xml'}
    IMAGES = {'png':'PNG', 'svg': 'SVG'}
    DEFAULT_WIDGET = qr.QrCodeWidget
    CODE_TYPES = {
        'ean8':eanbc.Ean8BarcodeWidget,
        'ean5':eanbc.Ean5BarcodeWidget,
        'ean13':eanbc.Ean13BarcodeWidget,
        'qrcode': DEFAULT_WIDGET,
    }

    code = forms.CharField(max_length=1000, required=False, initial='1234567', help_text='barcode type like EAN8 etc.') # request.GET.get('code', '')
    image_type = forms.ChoiceField(choices=tuple(IMAGES.items()), required=False, initial='svg', error_messages= {"invalid_choice": f"Image type must be either {'or'.join(IMAGES)}."}, help_text='Image type')  # request.GET.get('image_type', 'png').lower()
    code_type = forms.ChoiceField(choices=tuple(CODE_TYPES.items()), required=False, initial='qrcode', help_text='Type of barcode')  # request.GET.get('image_type', 'png').lower()
    foreground = forms.CharField(max_length=8, required=False, initial='0x000000', validators=[ColorValidator], help_text='Foreground color')  # request.GET.get('foreground', '000000')
    background = forms.CharField(max_length=8, required=False, initial='0xffffff', validators=[ColorValidator], help_text='Background color')  # request.GET.get('background', 'ffffff')
    height = forms.FloatField(required=False, help_text='Height', initial=1, validators=[PositiveValidator])  # float(request.GET.get('height', 25.4))/25.4
    width = forms.FloatField(required=False, help_text='Width', initial=1, validators=[PositiveValidator])  # float(request.GET.get('width', 25.4))/25.4

    def _post_clean(self):
        cleaner = f'clean_{self.cleaned_data["code_type"]}'
        if hasattr(self, cleaner):
            self.cleaned_data['code'] = getattr(self, cleaner)()

    @property
    def image_content_type(self):
        if hasattr(self, 'cleaned_data') and self.cleaned_data:
            return self.CONTENT_TYPES[self.cleaned_data['image_type']]

    @property
    def image(self):
        if hasattr(self, 'cleaned_data') and self.cleaned_data:
            return getattr(self, f'generate_{self.cleaned_data["image_type"].lower()}', None)(**self.cleaned_data)
        return 'generator_error'

    def get_image(self):
        if self.cleaned_data['image_type'] == 'svg':
            return self.image
        breakpoint()
        data = b64encode(self.image.tobytes().decode("latin-1").encode("utf-8")).decode("utf-8")
        return 'data:image/png;base64,{}'.format(data)

    def clean_code_type(self):
        code_type = self.cleaned_data.get('code_type') or self['code_type'].initial
        self.cleaned_data['widget'] = self.CODE_TYPES.get(code_type) or self.DEFAULT_WIDGET
        return code_type

    def clean_image_type(self):
        return self.cleaned_data.get('image_type') or self['image_type'].initial

    def clean_ean(self):
        code = self.cleaned_data.get('code') or self['code'].initial or ''
        return ''.join(bit for bit in code if bit in '0123456789')

    clean_ean5 = clean_ean13 = clean_ean8 = clean_ean

    def get_widget(self, *args, widget=DEFAULT_WIDGET, code='12345', width=None, height=None, foreground=None, **kwargs):
        data = {'barBorder': 1} if hasattr(widget, 'barBorder') else {'quiet': 1}
        if height:
            data['barHeight'] = height
        if width:
            data['barWidth'] = width
        if foreground:
            data['barFillColor'] = HexColor(foreground)
        return widget(code, **data)

    def get_shape(self, *args, background=None, **kwargs):
        widget = self.get_widget(*args, **kwargs)
        if background:
            background = Rect(0,0,self.width, self.height, fillColor=HexColor(background), strokeColor=HexColor(background))
        return Drawing(int(getattr(widget,'width', None) or widget.barWidth), widget.barHeight, widget, background=background or None)

    def generate_svg(self, *args, **kwargs):
        return renderSVG.drawToString(self.get_shape(*args, **kwargs), showBoundary=False)

    def generate_png(self, *args, **kwargs):
        return renderPM.drawToString(self.get_shape(*args, **kwargs), 'PNG', showBoundary=False)


class BarcodeGeneratorView(FormView):
    message = "Error generating barcode: {}"
    form_class = BarcodeSettingsForm
    template_name = 'doc_generator/barcode.html'

    def form_valid(self, form):
        if settings.DEBUG and self.request.GET.get('debug'):
            return super().form_invalid(form)
        return HttpResponse(form.image, content_type=form.image_content_type)

    def form_invalid(self, form):
        raise Exception(f"Error generating barcode. {form.errors}")

    def get(self, request, *args, **kwargs):
        request.POST = request.GET
        request.method = 'POST'
        return self.post(request, *args, **kwargs)
