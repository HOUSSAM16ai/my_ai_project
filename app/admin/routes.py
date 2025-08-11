# app/admin/routes.py - The Absolute Commander v5.1 (Hotfix for User Model Compatibility)

from flask import render_template, abort, request, jsonify, flash
from flask_login import current_user, login_required

from app.admin import bp
from app.models import User
from app import db

# --- [THE SUPERCHARGED ADDITION] ---
# استيراد "العقل" المركزي مباشرة من طبقة الخدمات
from app.services.generation_service import forge_new_code

# --- The Dashboard, now serving the interactive UI ---
@bp.route('/dashboard')
@login_required
def dashboard():
    """
    يعرض لوحة التحكم الرئيسية للمشرف، والتي تحتوي الآن
    على واجهة الدردشة التفاعلية للـ AI.
    """
    # --- [HOTFIX] نعود مؤقتًا إلى التحقق من الإيميل لأن نموذج User لا يحتوي على is_admin بعد ---
    if current_user.email != "benmerahhoussam16@gmail.com":
        abort(403)
    # --- نهاية الإصلاح السريع ---

    return render_template('admin_dashboard.html', title='Admin Command Center')


# --- [THE API FOR THE UI] ---
@bp.route('/api/generate-code', methods=['POST'])
@login_required
def handle_generate_code_from_ui():
    """
    هذه هي بوابة الـ API الآمنة التي تستخدمها واجهة الدردشة.
    إنها تتلقى الطلبات من المتصفح وتستدعي "العقل" المركزي.
    """
    # --- [HOTFIX] نعود مؤقتًا إلى التحقق من الإيميل هنا أيضًا ---
    if current_user.email != "benmerahhoussam16@gmail.com":
        return jsonify({"status": "error", "message": "Forbidden"}), 403
    # --- نهاية الإصلاح السريع ---

    # التأكد من أن الطلب يحتوي على prompt
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required."}), 400

    # استدعاء "العقل" المركزي (نفس الدالة التي يستخدمها الـ CLI)
    result = forge_new_code(prompt)
    
    # إعادة النتيجة كـ JSON إلى المتصفح
    return jsonify(result)


# --- [LEGACY SUPPORT] Example of other admin routes ---
@bp.route('/users')
@login_required
def list_users():
    """
    مثال على صفحة إدارية أخرى تعرض قائمة المستخدمين.
    """
    # --- [HOTFIX] نعود مؤقتًا إلى التحقق من الإيميل هنا أيضًا ---
    if current_user.email != "benmerahhoussam16@gmail.com":
        abort(403)
    # --- نهاية الإصلاح السريع ---
    
    try:
        all_users = db.session.query(User).order_by(User.id).all()
    except Exception as e:
        flash(f"Error fetching users: {e}", "danger")
        all_users = []
        
    return render_template('admin_users.html', title='User Roster', users=all_users)