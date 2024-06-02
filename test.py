def time_to_min(time):
    factors = (60, 1, 1/60)

    return sum(i*j for i, j in zip(map(int, time.split(':')), factors))

print(time_to_min('09:50'))
print(450 + int(3)*45)
print()

# def email_verified_required(f):
#     ('dsfk')
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.email_verification_token:
#             return f(*args, **kwargs)
#         else:
#             flash("You need to verify your email to access this page.", "warning")
#             return redirect(url_for('profile'))
#     return decorated_function