import nonebot, json, requests, re, html
from nonebot.command.argfilter import extractors, validators
from datetime import datetime, timedelta, timezone


@nonebot.on_command('天气', shell_like=True)
async def weather(session):
    """根据关键字返回可能的城市，并设置地区"""
    weather_data = await read_weather_data()
    city_name = await member_in_list(weather_data, session.ctx['user_id'])
    if city_name:
        await session.finish(await format_msg(weather_data[city_name], city_name))
    
    if session.is_first_run:
        await session.send('您还没有注册过推送地区，接下来将自动开始注册')
    key_word = session.get('key_word', prompt="您希望推送哪里的天气？（仅支持中文名）", arg_filters=[extractors.extract_text, str.strip, validators.not_empty('输入不能为空')])
    if key_word in weather_data['city_list']:
        weather_data['city_list'][key_word]['members'].append(session.ctx['user_id'])
        await update_weather_data(weather_data)
        await session.finish(f'“{key_word}”已经存在，已将您的推送地区设置为“{key_word}”')

    search_results = await get_search_results(key_word)
    format_str = await format_results(search_results)
    if session.current_key != 'selection':
        await session.send(format_str)
    selection = session.get('selection', prompt="回复序号确认地区", arg_filters=[extractors.extract_text, str.strip, validators.not_empty('输入不能为空'), int])
    current_location = search_results[selection]
    city = current_location['localizedName']
    weather_data['city_list'][city] = {'code': current_location['key'], 'members': [session.ctx['user_id']]}
    weather_data[city] = await get_weather_data(current_location['key'])
    
    await update_weather_data(weather_data)
    await session.send(f"已将您的天气推送地区设为：\n {format_str.splitlines()[selection]}")

async def member_in_list(weather_data, user_id):
    """检查QQ是否已经录入，并返回所在城市"""
    for city in weather_data['city_list']:
        for qq in weather_data['city_list'][city]['members']:
            if qq == user_id:
                return city
    return False

async def get_search_results(city):
    url = 'https://www.accuweather.com/zh/search-locations?query=' + city
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:27.0) Gecko/20121011 Firefox/72.0', 'accept-language': 'zh-CN'})
    results_text = re.search(r'(?<=var searchLocationResults = ).*(?=;)', r.text).group()
    results = json.loads(results_text)
    return results

async def format_results(results):
    format_string = ''
    for i in range(len(results)):
        r = results[i]
        format_string += f"{i}. {r['localizedName']} ({r['country']['localizedName']}, {r['administrativeArea']['localizedName']})\n"
    return format_string

@nonebot.scheduler.scheduled_job('cron', hour='*')
async def _():
    """根据当地时区早上6点自动更新天气数据"""
    weather_data = await read_weather_data()
    for city in weather_data['city_list'].keys():
        if await tz_check(weather_data[city]['time_zone']):
            weather_data[city] = await get_weather_data(weather_data['city_list'][city]['code'])
            await update_weather_data(weather_data)
            bot = nonebot.get_bot()
            for qq in weather_data['city_list'][city]['members']:
                weather_str = await format_msg(weather_data[city], city)
                await bot.send_private_msg(user_id=qq, message=weather_str)

async def format_msg(w, city):
    """把天气数据处理成易读的字符串"""
    weather_str = f"{city}天气（{w['date']}）\n" \
        f"白天：{w['day_weather']}\n气温：{w['day_temp']}\n体感温度：{w['day_feel']}\n" \
            f"夜晚：{w['night_weather']}\n气温：{w['night_temp']}\n体感温度：{w['night_feel']}\n" \
                f"日出\\日落：{w['sunrise']}\\{w['sunset']}" 
    return weather_str

async def tz_check(time_zone):
    """查看是否有时区到早上6点了"""
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    local_tz = utc_dt.astimezone(timezone(timedelta(hours=time_zone)))
    if local_tz.hour == 6:
        return True
    return False

async def read_weather_data():
    """读取本地天气数据"""
    try:
        with open('weather.json', encoding='utf8') as f:
            weather_data = json.loads(f.read())
    except FileNotFoundError:
        weather_data = {"city_list": {}}
    return weather_data

async def get_weather_data(location):
    """通过api获取最新天气"""
    url = f'https://www.accuweather.com/zh/ca/victoria/v8w/daily-weather-forecast/{location}?day=1'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:27.0) Gecko/20121011 Firefox/72.0', 'accept-language': 'zh-CN'})
    fixed_html = html.unescape(r.text)

    time_zone = int(float(re.search(r'"gmtOffset":(.*?),', fixed_html).group(1)))
    date = re.search(r'"cDate":"(.*?)",', fixed_html).group(1)
    day_temp = re.search(r'白天.*?<p class="value">\s*(.*?)\s*<span class="hi-lo-label">', fixed_html, re.S).group(1)
    night_temp = re.search(r'夜晚.*?<p class="value">\s*(.*?)\s*<span class="hi-lo-label">', fixed_html, re.S).group(1)
    day_feel = re.search(r'白天.*?RealFeel®\s*(.*?)\s*</p>', fixed_html, re.S).group(1)
    night_feel = re.search(r'夜晚.*?RealFeel®\s*(.*?)\s*</p>', fixed_html, re.S).group(1)
    day_weather = re.search(r'白天.*?<div class="phrase">(.*?)</div>', fixed_html, re.S).group(1)
    night_weather = re.search(r'夜晚.*?<div class="phrase">(.*?)</div>', fixed_html, re.S).group(1)
    sunrise = re.search(r'日出.*?<span class="section-content">(.*?)</span>', fixed_html, re.S).group(1)
    sunset = re.search(r'日落.*?<span class="section-content">(.*?)</span>', fixed_html, re.S).group(1)

    weather_data = {
        'time_zone': time_zone,
        'date': date,
        'day_weather': day_weather,
        'day_temp': day_temp,
        'day_feel': day_feel,
        'night_weather': night_weather,
        'night_temp': night_temp,
        'night_feel': night_feel,
        'sunrise': sunrise,
        'sunset': sunset
    }
    return weather_data

async def update_weather_data(weather_data):
    """更新本地天气数据"""
    with open('weather.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(weather_data, ensure_ascii=False, indent=4))