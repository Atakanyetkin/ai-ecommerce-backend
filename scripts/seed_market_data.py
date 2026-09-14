import os
import sys

# Ensure root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import crud
from app.db.database import SessionLocal
from app.models.product import UnitType
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate


def seed_market_data():
    db = SessionLocal()
    print("🌱 Seeding Sanal Market Grocery Categories & Products...")

    try:
        # 1. Categories
        categories_data = [
            {"name": "Meyve & Sebze", "description": "Taze meyve ve sebzeler", "display_order": 1},
            {"name": "Et & Tavuk", "description": "Taze taze et ve kümes hayvanları", "display_order": 2},
            {"name": "Temel Gıda", "description": "Pirinç, bakliyat, un, yağ ve besinler", "display_order": 3},
            {"name": "Süt & Kahvaltılık", "description": "Süt, peynir, yoğurt, yumurta", "display_order": 4},
            {"name": "İçecekler", "description": "Su, maden suyu, çay, kahve ve meyve suları", "display_order": 5},
        ]

        created_categories = {}
        for cat_in in categories_data:
            cat = crud.get_category_by_slug(db, crud.slugify(cat_in["name"]))
            if not cat:
                cat = crud.create_category(
                    db,
                    CategoryCreate(
                        name=cat_in["name"],
                        description=cat_in["description"],
                        display_order=cat_in["display_order"],
                    ),
                )
                print(f"  ✅ Created Category: {cat.name}")
            created_categories[cat.name] = cat

        # 2. Products
        products_data = [
            # Meyve & Sebze
            {
                "name": "Salkım Domates",
                "description": "Antalya seralarından taze salkım domates",
                "category": "Meyve & Sebze",
                "price": 39.90,
                "discount_price": 34.90,
                "unit": UnitType.KG,
                "unit_amount": 1.0,
                "stock_quantity": 150.0,
                "sku": "GROC-DOM-001",
                "is_organic": True,
                "origin": "Antalya",
            },
            {
                "name": "Çarliston Biber",
                "description": "Taze ve çıtır çarliston biber",
                "category": "Meyve & Sebze",
                "price": 44.50,
                "unit": UnitType.KG,
                "unit_amount": 1.0,
                "stock_quantity": 80.0,
                "sku": "GROC-BIB-001",
                "is_organic": False,
                "origin": "Mersin",
            },
            {
                "name": "Çengelköy Salatalık",
                "description": "Kütür kütür Çengelköy salatalık",
                "category": "Meyve & Sebze",
                "price": 29.90,
                "unit": UnitType.KG,
                "unit_amount": 1.0,
                "stock_quantity": 100.0,
                "sku": "GROC-SAL-001",
                "is_organic": True,
                "origin": "İstanbul",
            },
            # Et & Tavuk
            {
                "name": "Dana Az Yağlı Kıyma",
                "description": "%100 Dana eti az yağlı çekilmiş kıyma",
                "category": "Et & Tavuk",
                "price": 420.00,
                "discount_price": 389.00,
                "unit": UnitType.KG,
                "unit_amount": 1.0,
                "stock_quantity": 50.0,
                "sku": "GROC-ET-KIY-01",
                "is_organic": False,
                "origin": "Balıkesir",
            },
            {
                "name": "Dana Kuşbaşı",
                "description": "Yumuşak dana tranç kuşbaşı et",
                "category": "Et & Tavuk",
                "price": 460.00,
                "unit": UnitType.KG,
                "unit_amount": 1.0,
                "stock_quantity": 40.0,
                "sku": "GROC-ET-KUS-01",
                "is_organic": False,
                "origin": "Balıkesir",
            },
            {
                "name": "Tavuk Göğsü Bonfile",
                "description": "Taze soslu/sossuz tavuk göğsü bonfile",
                "category": "Et & Tavuk",
                "price": 185.00,
                "unit": UnitType.KG,
                "unit_amount": 1.0,
                "stock_quantity": 75.0,
                "sku": "GROC-TAV-GOG-01",
                "is_organic": False,
                "origin": "Sakarya",
            },
            # Temel Gıda
            {
                "name": "Gönen Baldo Pirinç 1kg",
                "description": "Pilavlık Gönen baldo pirinç",
                "category": "Temel Gıda",
                "price": 79.90,
                "unit": UnitType.PACK,
                "unit_amount": 1.0,
                "stock_quantity": 200.0,
                "sku": "GROC-PIR-BAL-01",
                "is_organic": False,
                "origin": "Balıkesir Gönen",
            },
            {
                "name": "Osmancık Pirinç 2kg",
                "description": "Lezzetli Osmancık pirinç 2kg paket",
                "category": "Temel Gıda",
                "price": 119.00,
                "discount_price": 105.00,
                "unit": UnitType.PACK,
                "unit_amount": 2.0,
                "stock_quantity": 120.0,
                "sku": "GROC-PIR-OSM-02",
                "is_organic": False,
                "origin": "Çorum",
            },
            {
                "name": "Ayçiçek Yağı 5L",
                "description": "Saf rafine ayçiçek yağı 5 litre teneke",
                "category": "Temel Gıda",
                "price": 249.90,
                "unit": UnitType.LITER,
                "unit_amount": 5.0,
                "stock_quantity": 90.0,
                "sku": "GROC-YAG-AYC-05",
                "is_organic": False,
                "origin": "Tekirdağ",
            },
            # Süt & Kahvaltılık
            {
                "name": "Tam Yağlı Günlük Süt 1L",
                "description": "%3.5 Yağlı pastörize günlük cam şişe süt",
                "category": "Süt & Kahvaltılık",
                "price": 38.50,
                "unit": UnitType.LITER,
                "unit_amount": 1.0,
                "stock_quantity": 110.0,
                "sku": "GROC-SUT-GUN-01",
                "is_organic": True,
                "origin": "Bursa",
            },
            {
                "name": "Ezine Peyniri 500g",
                "description": "Geleneksel koyun & keçi sütlü Ezine olgunlaştırılmış beyaz peynir",
                "category": "Süt & Kahvaltılık",
                "price": 165.00,
                "discount_price": 149.00,
                "unit": UnitType.GRAM,
                "unit_amount": 500.0,
                "stock_quantity": 60.0,
                "sku": "GROC-PEY-EZN-50",
                "is_organic": False,
                "origin": "Çanakkale Ezine",
            },
            {
                "name": "Organik Gezen Tavuk Yumurtası (10'lu)",
                "description": "A Sınıfı M Boy 10'lu organik gezen tavuk yumurtası",
                "category": "Süt & Kahvaltılık",
                "price": 64.90,
                "unit": UnitType.PACK,
                "unit_amount": 10.0,
                "stock_quantity": 150.0,
                "sku": "GROC-YUM-ORG-10",
                "is_organic": True,
                "origin": "Manisa",
            },
            # İçecekler
            {
                "name": "Doğal Maden Suyu 6'lı Paket",
                "description": "Zengin mineralli doğal maden suyu 6x200ml",
                "category": "İçecekler",
                "price": 42.00,
                "unit": UnitType.PACK,
                "unit_amount": 6.0,
                "stock_quantity": 180.0,
                "sku": "GROC-IC-MAD-06",
                "is_organic": False,
                "origin": "Bursa Uludağ",
            },
            {
                "name": "Rize Siyah Dökme Çay 1kg",
                "description": "Rize harmanı yüksek kaliteli dökme siyah çay",
                "category": "İçecekler",
                "price": 145.00,
                "unit": UnitType.PACK,
                "unit_amount": 1.0,
                "stock_quantity": 130.0,
                "sku": "GROC-IC-CAY-01",
                "is_organic": False,
                "origin": "Rize",
            },
        ]

        for prod_in in products_data:
            cat = created_categories[prod_in["category"]]
            existing = crud.get_product_by_sku(db, prod_in["sku"])
            if not existing:
                prod = crud.create_product(
                    db,
                    ProductCreate(
                        name=prod_in["name"],
                        description=prod_in["description"],
                        category_id=cat.id,
                        price=prod_in["price"],
                        discount_price=prod_in.get("discount_price"),
                        unit=prod_in["unit"],
                        unit_amount=prod_in["unit_amount"],
                        stock_quantity=prod_in["stock_quantity"],
                        sku=prod_in["sku"],
                        is_organic=prod_in["is_organic"],
                        origin=prod_in["origin"],
                    ),
                )
                print(f"  🛒 Created Product: {prod.name} ({prod.price} TL / {prod.unit_amount} {prod.unit.value})")

        print("🎉 Sanal Market Seed Completed Successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_market_data()
