# main/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned
from django.views.decorators.csrf import csrf_exempt

from .models import Conversation, ConversationMessage

@login_required
def create_conversation_page(request):
    return render(request, "create_chat.html", {})

@login_required
def conversation_list(request):
    """
    Render daftar percakapan menggunakan template 'chat_list.html'.
    Menyusun list 'conversations' agar template bisa mengakses convo.other,
    last_message, last_sender_is_me, last_sender_username, unread_count, id.
    """
    raw_convos = Conversation.objects.filter(Q(user_a=request.user) | Q(user_b=request.user)).order_by('-updated_at')[:200]

    conversations = []
    for convo in raw_convos:
        # tentukan user lain dalam percakapan ini
        other = convo.user_a if convo.user_b == request.user else convo.user_b

        # pesan terakhir (ambil object terakhir bila ada)
        last_obj = convo.messages.order_by('-created_at').first()
        if last_obj:
            # jika content kosong (mis. image only) tampilkan placeholder
            last_message_text = last_obj.content.strip() if (last_obj.content and last_obj.content.strip()) else "[gambar]"
            last_sender_is_me = (last_obj.sender_id == request.user.id)
            # nama pengirim untuk preview; jika pengirim adalah current user kita set "You" agar lebih jelas
            last_sender_username = "You" if last_sender_is_me else (last_obj.sender.username if last_obj.sender else "")
            last_message_time = last_obj.created_at
        else:
            last_message_text = ""
            last_sender_is_me = False
            last_sender_username = ""
            last_message_time = None

        # hitung unread dari pihak lain
        unread_count = convo.messages.exclude(sender=request.user).filter(is_read=False).count()

        conversations.append({
            "id": convo.pk,
            "other": other,
            "last_message": last_message_text,
            "last_message_time": last_message_time,
            "last_sender_is_me": last_sender_is_me,
            "last_sender_username": last_sender_username,
            "unread_count": unread_count,
            "updated_at": convo.updated_at,
        })

    return render(request, "chat_list.html", {"conversations": conversations})

@login_required
@csrf_exempt
def api_list(request):
    """
    API endpoint to get list of conversations for the current user.
    Returns JSON with conversations array.
    """
    raw_convos = Conversation.objects.filter(Q(user_a=request.user) | Q(user_b=request.user)).order_by('-updated_at')[:200]

    conversations = []
    for convo in raw_convos:
        # determine the other user in this conversation
        other = convo.user_a if convo.user_b == request.user else convo.user_b

        # last message (get the last object if exists)
        last_obj = convo.messages.order_by('-created_at').first()
        if last_obj:
            # if content is empty (e.g. image only) show placeholder
            last_message_text = last_obj.content.strip() if (last_obj.content and last_obj.content.strip()) else "[gambar]"
            last_sender_is_me = (last_obj.sender_id == request.user.id)
            # sender name for preview; if sender is current user set "You" for clarity
            last_sender_username = "You" if last_sender_is_me else (last_obj.sender.username if last_obj.sender else "")
            last_message_time = last_obj.created_at.isoformat()
        else:
            last_message_text = ""
            last_sender_is_me = False
            last_sender_username = ""
            last_message_time = None

        # count unread messages from the other party
        unread_count = convo.messages.exclude(sender=request.user).filter(is_read=False).count()

        conversations.append({
            "id": str(convo.pk),
            "other_username": other.username,
            "other_id": str(other.pk),
            "last_message": last_message_text,
            "last_message_time": last_message_time,
            "last_sender_is_me": last_sender_is_me,
            "last_sender_username": last_sender_username,
            "unread_count": unread_count,
            "updated_at": convo.updated_at.isoformat(),
        })

    return JsonResponse({"conversations": conversations})

@login_required
def conversation_view(request, convo_id):
    convo = get_object_or_404(Conversation, pk=convo_id)
    if request.user not in convo.participants():
        return HttpResponseForbidden("not allowed")

    # determine the "other" user
    other = convo.user_a if convo.user_b == request.user else convo.user_b

    return render(request, "chat_room.html", {"convo": convo, "other": other})


@login_required
def create_conversation(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("only POST")

    # terima berbagai nama field form untuk kompatibilitas
    username = request.POST.get('username') or request.POST.get('other_username')
    user_id = request.POST.get('user_id')

    other = None
    try:
        if user_id:
            other = User.objects.get(pk=user_id)
        elif username:
            other = User.objects.get(username=username)
    except User.DoesNotExist:
        # kalau tidak ditemukan, kembalikan bad request (anda bisa render template error jika mau)
        return HttpResponseBadRequest("user not found")

    if other == request.user:
        return HttpResponseBadRequest("cannot create conversation with yourself")

    # Coba gunakan helper model jika tersedia, jika tidak fallback create/find manual
    try:
        convo = Conversation.get_or_create_for(request.user, other)
    except Exception:
        convo = Conversation.objects.filter(
            (Q(user_a=request.user) & Q(user_b=other)) | (Q(user_a=other) & Q(user_b=request.user))
        ).first()
        if not convo:
            convo = Conversation.objects.create(user_a=request.user, user_b=other)

    return redirect('chat:conversation_view', convo.pk)


def api_fetch_messages(request, convo_id):
    convo = get_object_or_404(Conversation, pk=convo_id)
    if request.user not in convo.participants():
        return JsonResponse({"error": "not allowed"}, status=403)

    # Mark all messages in this conversation as read for the current user
    # (only mark those sent by others and not already read)
    try:
        ConversationMessage.objects.filter(conversation=convo, is_read=False).exclude(sender=request.user).update(is_read=True)
    except Exception:
        # If marking fails, proceed to still return messages
        pass

    messages = convo.messages.order_by('created_at').all()
    data = []
    for m in messages:
        data.append({
            "id": str(m.id),
            "sender_id": m.sender_id,
            "sender_username": "You" if m.sender_id == request.user.id else m.sender.username,
            "content": m.content,
            "image_url": m.image.url if m.image else None,
            "created_at": m.created_at.isoformat(),
            "is_read": m.is_read,
        })
    return JsonResponse({"messages": data})

# --- API: send message (supports image) ---
@login_required
@require_POST
@transaction.atomic
def api_send_message(request, convo_id):
    convo = get_object_or_404(Conversation, pk=convo_id)
    if request.user not in convo.participants():
        return JsonResponse({"error": "not allowed"}, status=403)

    content = request.POST.get('content', '').strip()
    image = None
    if 'image' in request.FILES:
        image = request.FILES.get('image')

    if not content and not image:
        return JsonResponse({"error":"no content or image"}, status=400)

    msg = ConversationMessage.objects.create(
        conversation=convo,
        sender=request.user,
        content=content,
        image=image
    )
    # update convo updated_at
    Conversation.objects.filter(pk=convo.pk).update(updated_at=msg.created_at)

    return JsonResponse({"ok": True, "id": str(msg.id)})

@login_required
@require_POST
def api_create_conversation(request):
    """
    Create or return existing conversation between request.user and another user.
    Accepts form-POST with 'username' or 'user_id', or JSON body with same keys.
    Returns JSON: {"ok": True, "id": "<conversation_uuid>"} or {"error": "..."}.
    """
    # Try form POST first
    username = request.POST.get('username')
    other_id = request.POST.get('user_id')

    # If JSON, try parse JSON body as fallback
    if not username and not other_id:
        try:
            body = json.loads(request.body.decode() or "{}")
            username = body.get('username') or username
            other_id = body.get('user_id') or other_id
        except Exception:
            # ignore parse errors; we'll validate below
            pass

    if not username and not other_id:
        return JsonResponse({"error": "missing 'username' or 'user_id' in request"}, status=400)

    # Resolve the other user
    try:
        if other_id:
            other = User.objects.get(pk=other_id)
        else:
            other = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "user not found"}, status=404)

    if other == request.user:
        return JsonResponse({"error": "cannot create conversation with yourself"}, status=400)

    # Try to use model helper if available; otherwise, fallback to simple lookup/create
    try:
        # If your Conversation model defines get_or_create_for(user_a, user_b) this will use it.
        convo = Conversation.get_or_create_for(request.user, other)
    except Exception:
        # Fallback: find existing conversation between the two users, ignoring order
        convo = Conversation.objects.filter(
            (Q(user_a=request.user) & Q(user_b=other)) | (Q(user_a=other) & Q(user_b=request.user))
        ).first()
        if not convo:
            convo = Conversation.objects.create(user_a=request.user, user_b=other)

    return JsonResponse({"ok": True, "id": str(convo.pk)})