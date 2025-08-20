#!/bin/bash
set -e

echo "نظام التدقيق الذكي - إعداد الإنتاج"
echo "Saudi AI Audit System - Production Setup"
echo "========================================"

# 1. Check Arabic locale
echo "فحص دعم اللغة العربية..."
if ! locale -a | grep -q "ar_SA"; then
    echo "خطأ: اللغة العربية غير مثبتة"
    echo "Error: Arabic locale not installed"
    echo "Run: sudo dnf install langpacks-ar"
    exit 1
fi

# 2. Check government CA certificate
echo "فحص شهادة الحكومة..."
if ! [ -f /etc/pki/ca-trust/source/anchors/saudi-govt-ca.crt ]; then
    echo "تحذير: شهادة الحكومة غير موجودة"
    echo "Warning: Government CA certificate not found"
fi

# 3. Create required directory structure with proper permissions
echo "إنشاء هيكل المجلدات..."
mkdir -p /var/audit_logs/{primary,backup,archive}
mkdir -p /var/audit_logs/archive/{2024..2031}  # 7 years
chmod 750 /var/audit_logs
chown -R aiaudit:auditors /var/audit_logs

# 4. SELinux configuration
echo "تكوين SELinux..."
semanage fcontext -a -t admin_home_t "/var/audit_logs(/.*)?"
restorecon -Rv /var/audit_logs

# 5. Set up automated backups
echo "إعداد النسخ الاحتياطي..."
cat > /etc/cron.d/audit-backup << EOF
# Backup every 4 hours
0 */4 * * * aiaudit /usr/local/bin/audit-backup.sh
EOF

# 6. Configure log rotation (7 year retention)
cat > /etc/logrotate.d/audit-logs << EOF
/var/audit_logs/*.jsonl {
    daily
    rotate 2555  # 7 years
    compress
    delaycompress
    notifempty
    create 640 aiaudit auditors
}
EOF

# 7. Performance tuning
echo "ضبط الأداء..."
sysctl -w net.core.somaxconn=1024
sysctl -w net.ipv4.tcp_max_syn_backlog=2048

# 8. Install offline dependencies
echo "تثبيت المكتبات..."
cd /opt/saudi-ai-audit
pip install --no-index --find-links ./pip-wheels -r requirements.txt

# 9. Verify installation
echo "التحقق من التثبيت..."
python -c "import arabic_reshaper; print('✓ Arabic support')"
python -c "from hijri_converter import Hijri; print('✓ Hijri calendar')"
python -c "import fastapi; print('✓ FastAPI installed')"

echo "اكتمل الإعداد بنجاح"
echo "Setup completed successfully"