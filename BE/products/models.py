from django.db import models


class FinancialProduct(models.Model):
    fin_prdt_cd = models.CharField(
        max_length=255,
        unique=True
    )

    bank_code = models.CharField(max_length=50)

    product_type = models.CharField(max_length=50)

    bank_name = models.CharField(max_length=255)

    product_name = models.CharField(max_length=255)

    join_way = models.TextField(blank=True)

    target_user = models.CharField(
        max_length=255,
        blank=True
    )

    description = models.TextField(blank=True)

    special_condition = models.TextField(blank=True, help_text='최고금리 우대 조건')

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


class FinancialProductOption(models.Model):
    product = models.ForeignKey(
        FinancialProduct,
        on_delete=models.CASCADE
    )

    save_trm = models.IntegerField()

    interest_rate = models.FloatField(
        null=True,
        blank=True
    )

    max_interest_rate = models.FloatField(
        null=True,
        blank=True
    )