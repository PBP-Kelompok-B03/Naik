from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import logout as auth_logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
import json

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            # Try to get data from JSON first (for Flutter app)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            else:
                # Fallback to form data (for web forms)
                username = request.POST.get('username')
                password = request.POST.get('password')
            
            if not username or not password:
                return JsonResponse({
                    "status": False,
                    "message": "Username and password are required."
                }, status=400)
            
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    # Login status successful.
                    return JsonResponse({
                        "username": user.username,
                        "status": True,
                        "message": "Login successful!",
                        "role": user.profile.role,
                        "user_id": user.id
                        # Add other data if you want to send data to Flutter.
                    }, status=200)
                else:
                    return JsonResponse({
                        "status": False,
                        "message": "Login failed, account is disabled."
                    }, status=401)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Login failed, please check your username or password."
                }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data."
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            "status": False,
            "message": "Method not allowed."
        }, status=405)
    
@csrf_exempt
def logout(request):
    username = request.user.username
    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logged out successfully!"
        }, status=200)
    except:
        return JsonResponse({
            "status": False,
            "message": "Logout failed."
        }, status=401)
    
@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password1 = data.get('password1')
            password2 = data.get('password2')
            role = data.get('role', 'buyer')  # Default to buyer if not specified

            # Validate required fields
            if not username or not password1 or not password2:
                return JsonResponse({
                    "status": False,
                    "message": "Username, password1, and password2 are required."
                }, status=400)

            # Check if the passwords match
            if password1 != password2:
                return JsonResponse({
                    "status": False,
                    "message": "Passwords do not match."
                }, status=400)

            # Check if the username is already taken
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    "status": False,
                    "message": "Username already exists."
                }, status=400)

            # Validate role
            valid_roles = ['buyer', 'seller', 'admin']
            if role not in valid_roles:
                return JsonResponse({
                    "status": False,
                    "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                }, status=400)

            # Create the new user
            user = User.objects.create_user(username=username, password=password1)
            user.save()

            # Update the user's profile with the selected role
            user.profile.role = role
            user.profile.save()

            return JsonResponse({
                "username": user.username,
                "status": 'success',
                "message": "User created successfully!",
                "role": role,
                "user_id": user.id
            }, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data."
            }, status=400)
        except KeyError as e:
            return JsonResponse({
                "status": False,
                "message": f"Missing required field: {str(e)}"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)
    
    else:
        return JsonResponse({
            "status": False,
            "message": "Invalid request method."
        }, status=400)
