from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth_dependency import require_shop_owner, require_system_admin
from app.schemas.content_request_schema import ContentRequestCreate, ContentRequestDecision
from app.services.content_request_service import content_request_service


router = APIRouter(prefix="/api/content-requests", tags=["CONTENT REVIEW"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def submit_content_request(data: ContentRequestCreate, owner: dict = Depends(require_shop_owner)):
    return content_request_service.submit(data, owner)


@router.get("/admin")
def list_content_requests(kind: str = Query(..., alias="type"), admin: dict = Depends(require_system_admin)):
    return content_request_service.list_admin(kind, admin)


@router.get("/admin/{request_id}")
def get_content_request(request_id: int, admin: dict = Depends(require_system_admin)):
    return content_request_service.get_admin(request_id, admin)


@router.post("/admin/{request_id}/decision")
async def decide_content_request(request_id: int, data: ContentRequestDecision, admin: dict = Depends(require_system_admin)):
    return await content_request_service.decide(request_id, data.approved, data.admin_note, admin)


@router.get("/mine")
def list_my_content_requests(owner: dict = Depends(require_shop_owner)):
    return content_request_service.owner_requests(owner)


@router.get("/notifications")
def list_my_notifications(owner: dict = Depends(require_shop_owner)):
    return content_request_service.owner_notifications(owner)


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, owner: dict = Depends(require_shop_owner)):
    content_request_service.mark_notification_read(notification_id, owner)
    return {"message": "Đã đánh dấu đã đọc"}
