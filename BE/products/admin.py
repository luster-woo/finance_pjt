from django.contrib import admin
from .models import FinancialProduct
from .models import FinancialProductOption

admin.site.register(FinancialProduct)
admin.site.register(FinancialProductOption)