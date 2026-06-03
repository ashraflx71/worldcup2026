import requests
import datetime
import re

def fetch_live_matches():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        match_html = ""
        events = data.get('events', [])
        
        if not events:
            return """
            <div class="match-box">
                <div class="match-info">
                    <div class="team"><span class="team-name">الأرجنتين 🇦🇷</span></div>
                    <div class="live-score"> VS </div>
                    <div class="team"><span class="team-name">إسبانيا 🇪🇸</span></div>
                </div>
                <div class="match-details">📅 في انتظار انطلاق المباريات (تحديث تلقائي عبر ESPN)</div>
            </div>
            """
        
        for event in events[:5]:
            status_type = event.get('status', {}).get('type', {}).get('name', 'STATUS_SCHEDULED')
            
            if status_type == 'STATUS_IN_PROGRESS':
                status_icon = "🟢 حية الآن"
                status_class = "live-status"
            elif status_type == 'STATUS_FINAL':
                status_icon = "🏁 انتهت"
                status_class = "final-status"
            else:
                status_icon = "⏰ قادمة"
                status_class = "upcoming-status"
            
            competitors = event.get('competitions', [{}])[0].get('competitors', [])
            if len(competitors) >= 2:
                team1 = competitors[0].get('team', {}).get('displayName', 'فريق 1')
                team1_logo = competitors[0].get('team', {}).get('logo', '')
                score1 = competitors[0].get('score', '0')
                team2 = competitors[1].get('team', {}).get('displayName', 'فريق 2')
                team2_logo = competitors[1].get('team', {}).get('logo', '')
                score2 = competitors[1].get('score', '0')
                
                match_date = event.get('date', '')
                match_time = ""
                if match_date:
                    try:
                        dt = datetime.datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                        local_dt = dt + datetime.timedelta(hours=2)
                        match_time = local_dt.strftime("%H:%M")
                    except:
                        match_time = "--:--"
                
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
                    <div class="match-details">🏆 {event.get('name', 'مباراة')}</div>
                </div>
                """
        
        return match_html if match_html else "<div class='match-box error-box'>⚠️ لا توجد مباريات متاحة حالياً</div>"
        
    except Exception as e:
        print(f"خطأ: {e}")
        return f"<div class='match-box error-box'>⚠️ حدث خطأ في جلب البيانات: {str(e)[:50]}</div>"

def update_index_file():
    print("🔄 جاري تحديث المباريات...")
    new_matches = fetch_live_matches()
    
    try:
        with open("index.html", "r", encoding="utf-8") as file:
            content = file.read()
        
        start_tag = "<!-- DATA_START -->"
        end_tag = "<!-- DATA_END -->"
        
        if start_tag in content and end_tag in content:
            before = content.split(start_tag)[0]
            after = content.split(end_tag)[1]
            
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # استبدال الوقت
            after = after.replace("<!-- TIME_PLACEHOLDER -->", current_time)
            
            updated_content = f"{before}{start_tag}\n{new_matches}\n{end_tag}{after}"
            
            with open("index.html", "w", encoding="utf-8") as file:
                file.write(updated_content)
            
            print(f"✅ تم التحديث بنجاح في {current_time}")
            return True
        else:
            print("❌ لم يتم العثور على علامات DATA_START و DATA_END")
            return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

if __name__ == "__main__":
    update_index_file()
