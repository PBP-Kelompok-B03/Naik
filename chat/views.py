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
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
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
@csrf_exempt
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

@csrf_exempt
@require_POST
def api_create_conversation(request):
    # API TIDAK BOLEH REDIRECT
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    # Ambil data dari JSON atau form
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    other_username = data.get("other_username") or request.POST.get("other_username")
    if not other_username:
        return JsonResponse({"message": "other_username wajib diisi"}, status=400)

    if other_username == request.user.username:
        return JsonResponse({"message": "Tidak bisa chat dengan diri sendiri"}, status=400)

    try:
        other = User.objects.get(username=other_username)
    except User.DoesNotExist:
        return JsonResponse({"message": "User tidak ditemukan"}, status=404)

    # Cari conversation yang sudah ada
    convo = Conversation.objects.filter(
        Q(user_a=request.user, user_b=other) |
        Q(user_a=other, user_b=request.user)
    ).first()

    if convo is None:
        convo = Conversation.objects.create(
            user_a=request.user,
            user_b=other
        )

    return JsonResponse({
        "conversation": {
            "id": str(convo.pk),
            "other_username": other.username,
            "last_message": "",
            "unread_count": 0,
        }
    })

@login_required
def api_conversation_list(request):
    """
    API untuk mengambil daftar percakapan user dalam format JSON.
    """
    raw_convos = Conversation.objects.filter(Q(user_a=request.user) | Q(user_b=request.user)).order_by('-updated_at')
    
    data = []
    for convo in raw_convos:
        other = convo.user_a if convo.user_b == request.user else convo.user_b
        
        last_obj = convo.messages.order_by('-created_at').first()
        last_message_text = ""
        last_message_time = None
        
        if last_obj:
            last_message_text = last_obj.content.strip() if (last_obj.content and last_obj.content.strip()) else "[gambar]"
            last_message_time = last_obj.created_at.isoformat()
        
        unread_count = convo.messages.exclude(sender=request.user).filter(is_read=False).count()
        
        data.append({
            "id": str(convo.pk),
            "other_username": other.username,
            "last_message": last_message_text,
            "last_message_time": last_message_time,
            "unread_count": unread_count,
        })
        
    return JsonResponse({"conversations": data})