from fastapi import APIRouter

from app.api.v1 import auth, categories, products

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(categories.router, prefix="/categories", tags=["Categories"])
router.include_router(products.router, prefix="/products", tags=["Products"])
