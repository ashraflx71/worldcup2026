import os
import requests
import datetime
import re

# 1. استدعاء مفتاح نوكيا السري من إعدادات جيتهاب بأمان
LIVE_KEY = os.environ.get('LIVE_KEY')

def fetch_live_matches():
    try:
        # رابط ESPN الذكي والمفتوح لجلب المباريات الحية بدون مفتاح معقد
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        match_html = ""
        events = data.get('events', [])
        
        # إذا لم تكن هناك مباريات جارية حالياً، نضع مباراة افتراضية احترافية
        if not events:
            return """
            <div class="match-box">
                <div class="match-info">
                    <div class="team-name">الأرجنتين 🇦🇷</div>
                    <div class="live-score"> VS </div>
                    <div class="team-name">إسبانيا 🇪🇸</div>
                </div>
                <div class="match-status">📅 في انتظار انطلاق البث المباشر للمباريات (تحديث تلقائي عبر ESPN)</div>
            </div>
            """
            
        # جلب أول 3 مباريات جارية حالياً
        for event in events[:3]:
            title = event.get('name', 'مباراة دولية')
            status_type = event.get('status', {}).get('type', {}).get('name', 'STATUS_SCHEDULED')
            
            # تحديد حالة المباراة (حية، قادمة، انتهت)
            if status_type == 'STATUS_IN_PROGRESS':
                status_icon = "🟢 حية الآن"
                status_class = "live-status"
            elif status_type == 'STATUS_FINAL':
                status_icon = "🏁 انتهت"
                status_class = "final-status"
            else:
                status_icon = "⏰ قادمة"
                status_class = "upcoming-status"
            
            # استخراج أسماء الفرق والنتائج
            competitors = event.get('competitions', [{}])[0].get('competitors', [])
            if len(competitors) >= 2:
                team1 = competitors[0].get('team', {}).get('displayName', 'فريق 1')
                team1_logo = competitors[0].get('team', {}).get('logo', '')
                score1 = competitors[0].get('score', '0')
                team2 = competitors[1].get('team', {}).get('displayName', 'فريق 2')
                team2_logo = competitors[1].get('team', {}).get('logo', '')
                score2 = competitors[1].get('score', '0')
                
                # وقت المباراة
                match_date = event.get('date', '')
                match_time = ""
                if match_date:
                    try:
                        dt = datetime.datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                        local_dt = dt + datetime.timedelta(hours=2)  # توقيت مصر +2
                        match_time = local_dt.strftime("%H:%M")
                    except:
                        match_time = "تحديد لاحق"
                
                match_html += f"""
                <div class="match-box {status_class}">
                    <div class="match-header">
                        <span class="match-time">{match_time}</span>
                        <span class="match-status-badge {status_class}">{status_icon}</span>
                    </div>
                    <div class="match-info">
                        <div class="team">
                            <span class="team-name">{team1}</span>
                            <img src="{team1_logo}" class="team-logo" onerror="this.style.display='none'" alt="">
                        </div>
                        <div class="live-score">{score1} - {score2}</div>
                        <div class="team">
                            <span class="team-name">{team2}</span>
                            <img src="{team2_logo}" class="team-logo" onerror="this.style.display='none'" alt="">
                        </div>
                    </div>
                    <div class="match-details">{title}</div>
                </div>
                """
        return match_html if match_html else "<div class='match-box'>لا توجد مباريات حالياً</div>"
        
    except Exception as e:
        print(f"⚠️ حدث خطأ أثناء جلب البيانات: {e}")
        return f"""
        <div class='match-box error-box'>
            <div class='match-info'>⚠️ خطأ في جلب البيانات</div>
            <div class='match-status'>سيتم المحاولة مرة أخرى قريباً</div>
        </div>
        """

def update_index_file():
    print("🔄 بدء تحديث الموقع...")
    
    # جلب البيانات الحية الجديدة
    new_matches = fetch_live_matches()
    if not new_matches:
        print("❌ لم يتم جلب أي بيانات")
        return False

    try:
        # قراءة ملف الـ HTML الحالي
        with open("index.html", "r", encoding="utf-8") as file:
            content = file.read()

        # تحديد منطقة الحقن
        start_tag = "<!-- DATA_START -->"
        end_tag = "<!-- DATA_END -->"
        
        if start_tag in content and end_tag in content:
            before = content.split(start_tag)[0]
            after = content.split(end_tag)[1]
            
            # إضافة توقيت التحديث الحالي بتوقيت مصر
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_tag = "<!-- TIME_PLACEHOLDER -->"
            
            if time_tag in after:
                after = after.replace(time_tag, f"🕐 آخر تحديث: {current_time}")
            
            # بناء المحتوى الجديد بالكامل
            updated_content = f"{before}{start_tag}\n{new_matches}\n{end_tag}{after}"
            
            # حفظ الملف المحدث مع نسخة احتياطية
            backup_file = f"index_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(backup_file, "w", encoding="utf-8") as backup:
                backup.write(content)
            
            with open("index.html", "w", encoding="utf-8") as file:
                file.write(updated_content)
            
            print(f"✅ تم تحديث الموقع بنجاح في {current_time}")
            print(f"📦 تم إنشاء نسخة احتياطية: {backup_file}")
            return True
        else:
            print("❌ لم يتم العثور على علامات DATA_START و DATA_END في ملف index.html")
            print("💡 أضف هاتين العلامتين في المكان المناسب")
            return False
            
    except Exception as e:
        print(f"❌ خطأ أثناء تحديث الملف: {e}")
        return False

def add_css_styles():
    """إضافة CSS للمباريات في index.html إذا لم تكن موجودة"""
    css_styles = """
    <style>
        .match-box {
            background: rgba(0,0,0,0.6);
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid rgba(57,255,20,0.3);
        }
        .match-box.live-status { border-left: 4px solid #39ff14; }
        .match-box.final-status { opacity: 0.8; }
        .match-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.8rem;
        }
        .match-time { color: #ffd700; }
        .match-status-badge {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
        }
        .match-status-badge.live-status { background: #39ff14; color: #000; }
        .match-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .team {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
        }
        .team:first-child { justify-content: flex-end; }
        .team-name { font-weight: bold; font-size: 1.1rem; }
        .live-score {
            font-size: 1.5rem;
            font-weight: bold;
            color: #39ff14;
            min-width: 80px;
            text-align: center;
        }
        .team-logo { width: 30px; height: 30px; object-fit: contain; }
        .match-details {
            font-size: 0.7rem;
            color: #888;
            margin-top: 10px;
            text-align: center;
        }
        @media (max-width: 700px) {
            .team-name { font-size: 0.8rem; }
            .live-score { font-size: 1.1rem; min-width: 60px; }
            .team-logo { width: 20px; height: 20px; }
        }
    </style>
    """
    return css_styles

if __name__ == "__main__":
    print("=" * 50)
    print("🏆 تحديث مباريات كأس العالم 2026")
    print("📡 المصدر: ESPN API")
    print("=" * 50)
    
    success = update_index_file()
    
    if success:
        print("\n🎉 تم الانتهاء بنجاح!")
    else:
        print("\n⚠️ يرجى التحقق من الأخطاء أعلاه")
