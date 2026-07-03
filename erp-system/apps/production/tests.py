from django.test import TestCase
from .models import ProductCategory

class ProductCategoryModelTest(TestCase):

    def setUp(self):
        ProductCategory.objects.create(name="Electronics")
        ProductCategory.objects.create(name="Furniture")

    def test_product_category_creation(self):
        category = ProductCategory.objects.get(name="Electronics")
        self.assertEqual(category.name, "Electronics")

    def test_product_category_list(self):
        categories = ProductCategory.objects.all()
        self.assertEqual(categories.count(), 2)

    def test_product_category_update(self):
        category = ProductCategory.objects.get(name="Electronics")
        category.name = "Updated Electronics"
        category.save()
        updated_category = ProductCategory.objects.get(id=category.id)
        self.assertEqual(updated_category.name, "Updated Electronics")

    def test_product_category_delete(self):
        category = ProductCategory.objects.get(name="Furniture")
        category.delete()
        with self.assertRaises(ProductCategory.DoesNotExist):
            ProductCategory.objects.get(name="Furniture")