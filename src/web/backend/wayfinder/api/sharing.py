from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from wayfinder.api.auth import client_ip, get_actor
from wayfinder.domain.auth import Actor


class CreateShareLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expires_in_days: int | None = Field(default=None, gt=0, strict=True)
    max_uses: int | None = Field(default=None, gt=0, le=2_147_483_647, strict=True)


class ShareLink(BaseModel):
    id: str
    token_tail: str
    created_at: str
    expires_at: str | None
    max_uses: int | None
    use_count: int
    revoked_at: str | None
    status: Literal["active", "expired", "exhausted", "revoked"]


class CreatedShareLink(ShareLink):
    token: str
    url: str


class CreatedShareLinkEnvelope(BaseModel):
    link: CreatedShareLink


class ShareLinkList(BaseModel):
    items: list[ShareLink]


class JoinPreview(BaseModel):
    course_id: str
    title: str
    owner: dict[str, str]
    module_count: int
    concept_count: int


class JoinResult(BaseModel):
    course_id: str
    role: Literal["owner", "learner"]
    joined_at: str
    already_member: bool


class OwnerInfo(BaseModel):
    user_id: str
    display_name: str


class MemberInfo(BaseModel):
    user_id: str
    display_name: str
    joined_at: str
    last_active_at: str | None
    via: str


class MemberList(BaseModel):
    role: Literal["owner", "learner"]
    owner: OwnerInfo
    member_count: int
    members: list[MemberInfo] | None = None


class MessageResponse(BaseModel):
    message: str


class InviteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    emails: list[str] = Field(min_length=1, max_length=50)


class InvitationResponse(BaseModel):
    id: str
    course_id: str
    course_title: str
    email: str
    status: Literal['pending', 'accepted', 'declined', 'cancelled', 'expired']
    expires_at: str
    created_at: str
    responded_at: str | None


class InvitationList(BaseModel):
    items: list[InvitationResponse]


class InvitationActionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')


def sharing_router():
    router = APIRouter(prefix="/api/v1", tags=["sharing"])

    @router.post('/courses/{cid}/invitations', response_model=InvitationList)
    def invite(cid: str, data: InviteRequest, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.sharing.invite_by_email(actor, cid, data.emails, ip=client_ip(request))

    @router.get('/courses/{cid}/invitations', response_model=InvitationList)
    def course_invitations(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.sharing.list_course_invitations(actor, cid)

    @router.delete('/courses/{cid}/invitations/{iid}', response_model=MessageResponse)
    def cancel_invitation(cid: str, iid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.sharing.cancel_invitation(actor, cid, iid, ip=client_ip(request))

    @router.get('/me/invitations', response_model=InvitationList)
    def my_invitations(request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.sharing.list_my_invitations(actor)

    @router.post('/invitations/{iid}/accept', response_model=JoinResult)
    def accept_invitation(iid: str, request: Request, response: Response,
                          data: InvitationActionRequest | None = None, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.sharing.accept_invitation(actor, iid, ip=client_ip(request))

    @router.post('/invitations/{iid}/decline', response_model=MessageResponse)
    def decline_invitation(iid: str, request: Request, response: Response,
                           data: InvitationActionRequest | None = None, actor: Actor = Depends(get_actor)):
        response.headers['cache-control'] = 'no-store'
        return request.app.state.services.sharing.decline_invitation(actor, iid, ip=client_ip(request))

    @router.post("/courses/{cid}/share-links", response_model=CreatedShareLinkEnvelope)
    def create_link(cid: str, data: CreateShareLinkRequest, request: Request, response: Response,
                    actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        expires = data.expires_in_days if "expires_in_days" in data.model_fields_set else None
        # The service distinguishes omitted expiry from explicit null with its private sentinel.
        if "expires_in_days" not in data.model_fields_set:
            return request.app.state.services.sharing.create_share_link(actor, cid, max_uses=data.max_uses,
                                                                         ip=client_ip(request))
        return request.app.state.services.sharing.create_share_link(actor, cid, expires_in_days=expires,
                                                                     max_uses=data.max_uses, ip=client_ip(request))

    @router.get("/courses/{cid}/share-links", response_model=ShareLinkList)
    def list_links(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.list_share_links(actor, cid)

    @router.delete("/courses/{cid}/share-links/{lid}", response_model=MessageResponse)
    def revoke_link(cid: str, lid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.revoke_share_link(actor, cid, lid, ip=client_ip(request))

    @router.get("/join/{token}", response_model=JoinPreview)
    def preview(token: str, request: Request, response: Response):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.preview_share_link(token)

    @router.post("/join/{token}", response_model=JoinResult)
    def join(token: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.join_by_link(actor, token, ip=client_ip(request))

    @router.get("/courses/{cid}/members", response_model=MemberList, response_model_exclude_none=True)
    def members(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.list_members(actor, cid)

    @router.delete("/courses/{cid}/members/{uid}", response_model=MessageResponse)
    def remove_member(cid: str, uid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.remove_member(actor, cid, uid, ip=client_ip(request))

    @router.post("/courses/{cid}/leave", response_model=MessageResponse)
    def leave(cid: str, request: Request, response: Response, actor: Actor = Depends(get_actor)):
        response.headers["cache-control"] = "no-store"
        return request.app.state.services.sharing.leave_course(actor, cid, ip=client_ip(request))

    return router
