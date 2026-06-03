import os
import requests
import datetime

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
            
        # جلب أول 3 مباريات جارية حالياً وحقنها في الموقع
        for event in events[:3]:
            title = event.get('name', 'مباراة دولية')
            status_text = event.get('status', {}).get('type', {}).get('detail', 'قيد الانتظار')
            
            # استخراج أسماء الفرق والنتائج
            competitors = event.get('competitions', [{}])[0].get('competitors', [])
            if len(competitors) >= 2:
                team1 = competitors[0].get('team', {}).get('displayName', 'فريق 1')
                score1 = competitors[0].get('score', '0')
                team2 = competitors[1].get('team', {}).get('displayName', 'فريق 2')
                score2 = competitors[1].get('score', '0')
                
                match_html += f"""
                <div class="match-box">
                    <div class="match-info">
                        <div class="team-name">{team1}</div>
                        <div class="live-score"> {score1} - {score2} </div>
                        <div class="team-name">{team2}</div>
                    </div>
                    <div class="match-status">⚡ الحالة: {status_text} (محدث عبر ESPN)</div>
                </div>
                """
        return match_html
    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

def update_index_file():
    # جلب البيانات الحية الجديدة
    new_matches = fetch_live_matches()
    if not new_matches:
        return

    # قراءة ملف الـ HTML الحالي
    with open("index.html", "r", encoding="utf-8") as file:
        content = file.read()

    # تحديد منطقة الحقن واستبدال المباريات القديمة بالجديدة
    start_tag = "<!-- DATA_START -->"
    end_tag = "<!-- DATA_END -->"
    
    if start_tag in content and end_tag in content:
        before = content.split(start_tag)[0]
        after = content.split(end_tag)[1]
        
        # إضافة توقيت التحديث الحالي بتوقيت مصر
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_tag = "<!-- TIME_PLACEHOLDER -->"
        if time_tag in after:
            parts = after.split(time_tag)
            after = f"{parts[0]}{time_tag} {current_time} {time_tag}{parts[2]}"
            
        # بناء المحتوى الجديد بالكامل
        updated_content = f"{before}{start_tag}{new_matches}{end_tag}{after}"
        
        # حفظ الملف المحدث
        with open("index.html", "w", encoding="utf-8") as file:
            file.write(updated_content)
        print("🚀 تم تحديث الموقع بنجاح وحقن المباريات الحية من ESPN!")

if __name__ == "__main__":
    update_index_file()
