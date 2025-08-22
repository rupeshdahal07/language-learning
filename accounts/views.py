from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You are now logged in!")
            return redirect("dashboard")  # change "home" to your actual homepage route name
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('login')