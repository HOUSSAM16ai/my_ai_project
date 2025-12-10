"""
Plugins Package - حزمة الإضافات
==================================

نظام الإضافات - مفتوح للتوسع مغلق للتعديل
Plugin System - Open for Extension, Closed for Modification

الخدمات الأساسية (Core Services):
1. chat - نظام الدردشة
2. llm - عميل LLM
3. database - قاعدة البيانات
4. auth - المصادقة
5. agent - أدوات الوكلاء
6. api - بوابة API
7. admin - لوحة الإدارة
8. history - سجل المحادثات
9. overmind - التخطيط الذكي
10. observability - المراقبة

كيفية إضافة plugin جديد:
1. أنشئ مجلد جديد في app/plugins/
2. أنشئ plugin.py يحتوي على متغير 'plugin'
3. Plugin يجب أن يرث من IPlugin
4. سيتم اكتشافه تلقائياً عند بدء التطبيق
"""

# This file intentionally left empty
# Plugins are discovered automatically
