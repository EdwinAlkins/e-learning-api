import fastapi

import src.database.schemas.catalog
from src.services.catalog import catalog_service


router = fastapi.APIRouter(prefix="/formations", tags=["formations"])


@router.get("", response_model=src.database.schemas.catalog.CatalogResponse)
async def get_formations() -> src.database.schemas.catalog.CatalogResponse:
    """
    Get the complete catalog of formations.

    Returns:
        CatalogResponse: The catalog with all formations, chapters, and videos
    """
    return catalog_service.get_catalog()
