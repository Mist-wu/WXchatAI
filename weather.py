import requests
from bs4 import BeautifulSoup, FeatureNotFound

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

URLS = [
    "http://www.weather.com.cn/textFC/hb.shtml",
    "http://www.weather.com.cn/textFC/db.shtml",
    "http://www.weather.com.cn/textFC/hd.shtml",
    "http://www.weather.com.cn/textFC/hz.shtml",
    "http://www.weather.com.cn/textFC/hn.shtml",
    "http://www.weather.com.cn/textFC/xb.shtml",
    "http://www.weather.com.cn/textFC/xn.shtml",
]

def make_soup(html: str) -> BeautifulSoup:
    for parser in ("html5lib", "lxml", "html.parser"):
        try:
            return BeautifulSoup(html, parser)
        except FeatureNotFound:
            continue
    # 理论上不会到这里，除非环境极简且无任何解析器
    raise RuntimeError("未找到可用的 HTML 解析器，请安装 html5lib 或 lxml。")

def get_weather(my_city: str):
    for url in URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            # 使用 requests 的自动编码探测更稳妥
            resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
            text = resp.text
        except Exception as e:
            # 请求失败则尝试下一个 URL
            continue

        soup = make_soup(text)
        div_conMidtab = soup.find("div", class_="conMidtab")
        if not div_conMidtab:
            continue

        tables = div_conMidtab.find_all("table")
        for table in tables:
            trs = table.find_all("tr")
            if len(trs) <= 2:
                continue
            for tr in trs[2:]:
                tds = tr.find_all("td")
                if len(tds) < 8:
                    continue

                # 这里倒着数，因为每个省会的td结构跟其他不一样
                try:
                    city_td = tds[-8]
                    this_city = next(city_td.stripped_strings, "")
                except Exception:
                    continue

                if this_city == my_city:
                    try:
                        high_temp_td = tds[-5]
                        low_temp_td = tds[-2]
                        weather_type_day_td = tds[-7]
                        weather_type_night_td = tds[-4]
                        wind_td_day = tds[-6]
                        wind_td_day_night = tds[-3]

                        high_temp = next(high_temp_td.stripped_strings, "-")
                        low_temp = next(low_temp_td.stripped_strings, "-")
                        weather_typ_day = next(weather_type_day_td.stripped_strings, "-")
                        weather_type_night = next(weather_type_night_td.stripped_strings, "-")

                        wind_day_parts = list(wind_td_day.stripped_strings)
                        wind_night_parts = list(wind_td_day_night.stripped_strings)
                        wind_day = "".join(wind_day_parts[:2]) if wind_day_parts else "--"
                        wind_night = "".join(wind_night_parts[:2]) if wind_night_parts else "--"

                        # 如果没有白天的数据就使用夜间的
                        temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                        weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                        wind = wind_day if wind_day != "--" else wind_night
                        return this_city, temp, weather_typ, wind
                    except Exception:
                        continue
    return None

if __name__ == "__main__":
    print(get_weather("密云"))