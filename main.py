import os
import sys
import requests

# 1. 讀取環境變數 (Secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 地點設定：以台北市為例 (緯度: 25.0375, 經度: 121.5637)
LATITUDE = 25.0375
LONGITUDE = 121.5637

def fetch_weather_data():
    """取得天氣資料 (最高溫度、最高降雨機率)"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": ["temperature_2m_max", "precipitation_probability_max"],
        "timezone": "Asia/Taipei"
    }
    
    response = requests.get(url, params=params, timeout=10)
    # HTTP 狀態碼檢查：非 200 會拋出 HTTPError Exception
    response.raise_for_status()
    
    data = response.json()
    daily_data = data.get("daily", {})
    
    max_temp = daily_data.get("temperature_2m_max", [None])[0]
    max_pop = daily_data.get("precipitation_probability_max", [None])[0]
    
    return max_temp, max_pop


def fetch_aqi_data():
    """取得空氣品質資料 (AQI)"""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "us_aqi",
        "timezone": "Asia/Taipei"
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    aqi = data.get("current", {}).get("us_aqi", None)
    
    return aqi


def generate_recommendations(max_temp, max_pop, aqi):
    """根據數據產生通勤建議 (條件可同時成立)"""
    recommendations = []
    
    # 條件 1：降雨機率達 60%
    if max_pop is not None and max_pop >= 60:
        recommendations.append("☔ 降雨機率高，提醒攜帶雨傘。")
        
    # 條件 2：最高溫度達 33°C
    if max_temp is not None and max_temp >= 33:
        recommendations.append("☀️ 氣溫偏高，提醒防曬與補充水分。")
        
    # 條件 3：AQI 達 100
    if aqi is not None and aqi >= 100:
        recommendations.append("😷 空氣品質較差，提醒配戴口罩。")
        
    # 條件 4：所有條件正常
    if not recommendations:
        recommendations.append("🟢 今日天候良好，適合外出通勤！")
        
    return recommendations


def send_telegram_message(message):
    """傳送訊息至 Telegram Bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 錯誤：未設定 Telegram Bot Token 或 Chat ID 環境變數！")
        sys.exit(1)
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def main():
    try:
        print("🔍 正在取得天氣與空氣品質資料...")
        max_temp, max_pop = fetch_weather_data()
        aqi = fetch_aqi_data()
        
        # 產生建議
        recommendations = generate_recommendations(max_temp, max_pop, aqi)
        
        # 組裝通報內容
        message_lines = [
            "🚨 *智慧通勤風險通知*",
            "-------------------",
            f"🌡️ **今日最高氣溫**：{max_temp}°C",
            f"🌧️ **最高降雨機率**：{max_pop}%",
            f"🌫️ **空氣品質 AQI**：{aqi}",
            "-------------------",
            "💡 **通勤建議**："
        ]
        for rec in recommendations:
            message_lines.append(f"- {rec}")
            
        full_message = "\n".join(message_lines)
        
        print("📨 正在傳送 Telegram 通知...")
        send_telegram_message(full_message)
        print("✅ 通知傳送成功！")

    except requests.exceptions.RequestException as e:
        print(f"❌ 網路連線或 API 請求錯誤：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 系統發生未預期錯誤：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
