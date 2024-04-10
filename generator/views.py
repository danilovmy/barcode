from django.http import HttpResponse
from io import BytesIO
import treepoem
import barcode
from barcode.writer import SVGWriter
from django import forms
from django.views.generic import FormView
from django.core.validators import RegexValidator, MinValueValidator

ColorValidator = RegexValidator(regex=r'^[0-9A-Fa-f]{6}$|^[0-9A-Fa-f]{8}$', message = "Color must be valid hex RRGGBB or CCMMYYKK values.")
PositiveValidator = MinValueValidator(0, message="Height and width must be numbers greater than zero.")

class BarcodeSettingsForm(forms.Form):
    IMAGES = {'png':'PNG', 'svg': 'SVG'}
    CODE_TYPES = {'ean8': 'EAN8', 'ean13':'EAN13'}
    code = forms.CharField(max_length=1000, required=False, initial='1234567', help_text='barcode type like EAN8 etc.') # request.GET.get('code', '')
    image_type = forms.ChoiceField(choices=tuple(IMAGES.items()), required=False, initial='png', error_messages= {"invalid_choice": f"Image type must be either {'or'.join(IMAGES)}."}, help_text='Image type')  # request.GET.get('image_type', 'png').lower()
    code_type = forms.ChoiceField(choices=tuple(CODE_TYPES.items()), required=False, initial='ean8', help_text='Type of barcode')  # request.GET.get('image_type', 'png').lower()
    foreground = forms.CharField(max_length=8, required=False, initial='000000', validators=[ColorValidator], help_text='Foreground color')  # request.GET.get('foreground', '000000')
    background = forms.CharField(max_length=8, required=False, initial='ffffff', validators=[ColorValidator], help_text='Background color')  # request.GET.get('background', 'ffffff')
    height = forms.FloatField(required=False, help_text='Height', initial=25.4, validators=[PositiveValidator])  # float(request.GET.get('height', 25.4))/25.4
    width = forms.FloatField(required=False, help_text='Width', initial=25.4, validators=[PositiveValidator])  # float(request.GET.get('width', 25.4))/25.4


    def clean(self):
        data = super().clean()
        return {field.name: data.get(field.name) or field.initial for field in self}

    def _post_clean(self):
        cleaner = f'clean_{self.cleaned_data['code_type']}'
        if hasattr(self, cleaner):
            self.cleaned_data['code'] = getattr(self, cleaner)()

    def clean_ean8(self):
        return f'00000000{self.cleaned_data.get('code') or self["code"].initial or ""}'[-7:]


class BarcodeGeneratorView(FormView):
    message = "Error generating barcode: {}"
    form_class = BarcodeSettingsForm
    initial = {'code':'1234567', 'image_type':'png', 'code_type':'ean8', 'foreground':'000000', 'background':'ffffff', 'height':25.4, 'width':25.4}

    def form_valid(self, form):
        data = form.cleaned_data
        if data['image_type'] == 'png':
            return HttpResponse( self.generate_PNG(**data), content_type='image/png')
        elif data['image_type'] == 'svg':
            return HttpResponse(self.generate_SVG(**data), content_type='image/svg+xml')
        return self.form_invalid(form)

    def form_invalid(self, form):
        raise Exception(f"Error generating barcode. {form.errors}")

    def generate_SVG(self, *args, **kwargs):
        foreground_color = kwargs['foreground']
        background_color = kwargs['background']
        code_type = kwargs['code_type']
        code = kwargs['code']
        barcode_class = barcode.get_barcode_class(code_type)
        barcode_obj = barcode_class(code, writer=SVGWriter())
        return barcode_obj.render({'foreground': f'#{foreground_color}', 'background': f'#{background_color}', 'write_text': True, })

    def generate_PNG(self, *args, **kwargs):
        foreground_color = kwargs['foreground']
        background_color = kwargs['background']
        height = kwargs['height']
        width = kwargs['width']
        code_type = kwargs['code_type']
        code = kwargs['code']
        image = treepoem.generate_barcode(barcode_type=code_type, data=code, options={"includetext": True, "height": 0.33 * height / 25.4, "width": width / 25.4, "scale": 2, "barcolor": foreground_color, "textcolor": foreground_color, "backgroundcolor": background_color})
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()

    def get(self, request, *args, **kwargs):
        request.POST = request.GET
        request.method = 'POST'
        return self.post(request, *args, **kwargs)