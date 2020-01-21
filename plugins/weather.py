import nonebot, json, requests, re, html, cssselect
from nonebot.command.argfilter import extractors, validators
from datetime import datetime, timedelta, timezone
from lxml.html import fromstring


@nonebot.on_command('天气', shell_like=True)
async def weather(session):
    """根据关键字返回可能的城市，并设置地区"""
    settings = await read_settings()
    city_name = await member_in_list(settings, session.ctx['user_id'])
    if city_name:
        current_weather_data = await get_current_weather_data(settings['city_list'][city_name]['code'])
        await session.finish(await format_msg(current_weather_data, city_name, current=True))
    
    if session.is_first_run:
        await session.send('您还没有注册过推送地区，接下来将自动开始注册')
    key_word = session.get('key_word', prompt="您希望推送哪里的天气？（仅支持中文名）", arg_filters=[extractors.extract_text, str.strip, validators.not_empty('输入不能为空')])
    if key_word in settings['city_list']:
        settings['city_list'][key_word]['members'].append(session.ctx['user_id'])
        await update_settings(settings)
        await session.finish(f'“{key_word}”已经存在，已将您的推送地区设置为“{key_word}”')

    search_results = await get_search_results(key_word)
    format_str = await format_results(search_results)
    if session.current_key != 'selection':
        await session.send(format_str)
    selection = session.get('selection', prompt="回复序号确认地区", arg_filters=[extractors.extract_text, str.strip, validators.not_empty('输入不能为空'), int])
    
    results_url = search_results[selection].cssselect('a')[0].get('href')
    code = re.search(r'id=(\d*)', results_url).group(1)

    # current_location = search_results[selection]
    city = current_location['localizedName']
    city = search_results[selection].text_content()
    weather_data = await get_current_weather_data(current_location['key'])
    time_zone = tz_calc(weather_data['current_time'][7:9])
    settings['city_list'][city] = {'code': code, 'time_zone': time_zone, 'members': [session.ctx['user_id']]}
    
    
    await update_settings(settings)
    await session.send(f"已将您的天气推送地区设为：\n {format_str.splitlines()[selection]}")

async def member_in_list(settings, user_id):
    """检查QQ是否已经录入，并返回所在城市"""
    for city in settings['city_list']:
        for qq in settings['city_list'][city]['members']:
            if qq == user_id:
                return city
    return False

async def get_search_results(city):
    url = 'https://m.weathercn.com/search-locations.do?search=' + city
    r = requests.get(url, timeout=5)
    tree = fromstring(r.text)
    results = tree.cssselect('div#searchresult > ul > li')
    return results

async def format_results(results):
    format_string = ''
    for i in range(1, len(results)):
        format_string += f"{i}. {results[i].text_content()}\n"
    return format_string

# @nonebot.on_command('定时', shell_like=True)
# async def on_time(session):
@nonebot.scheduler.scheduled_job('cron', hour='*')
async def _():
    """根据当地时区早上6点自动更新天气数据"""
    settings = await read_settings()
    for city in settings['city_list'].keys():
        if await tz_check(settings['city_list'][city]['time_zone']):
            weather_data = await get_weather_data(settings['city_list'][city]['code'])
            settings['city_list'][city]['time_zone'] = weather_data['time_zone']
            await update_settings(settings)
            bot = nonebot.get_bot()
            for qq in settings['city_list'][city]['members']:
                weather_str = await format_msg(weather_data, city)
                await bot.send_private_msg(user_id=qq, message=weather_str)

async def format_msg(w, city, current=False):
    """把天气数据处理成易读的字符串"""
    if current:
        weather_str = f"{city}当前天气（{w['current_time']}）\n" \
            f"天气：{w['current_weather']}\n气温：{w['current_temp']}\n体感温度：{w['current_feel']}\n" \
                f"日出\\日落：{w['sunrise']}\\{w['sunset']}"
    else:
        weather_str = f"{city}今日天气（{w['date']}）\n" \
            f"白天：{w['day_weather']}\n气温：{w['day_temp']}\n体感温度：{w['day_feel']}\n" \
                f"夜晚：{w['night_weather']}\n气温：{w['night_temp']}\n体感温度：{w['night_feel']}\n" \
                    f"日出\\日落：{w['sunrise']}\\{w['sunset']}" 
    return weather_str

async def tz_calc(hour_now):
    pass

async def tz_check(time_zone):
    """查看是否有时区到早上6点了"""
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    local_tz = utc_dt.astimezone(timezone(timedelta(hours=time_zone)))
    if local_tz.hour == 6:
        return True
    return False

async def read_settings():
    """读取本地天气数据"""
    try:
        with open('settings.json', encoding='utf8') as f:
            settings = json.loads(f.read())
    except FileNotFoundError:
        settings = {"city_list": {}}
    return settings

async def get_weather_data(location):
    """爬取当天天气"""
    url = f'https://m.weathercn.com/daily-weather-forecast.do?day=1&id={code}'
    r = requests.get(url)
    tree = fromstring(r.text)

    date = tree.cssselect('section.date > div > ul > li')[0].text_content()
    weather = tree.cssselect('section.detail > section.weather > div.left > p')
    day_weather = weather[0].text_content()
    night_weather = weather[1].text_content()
    temp = tree.cssselect('ul.right li.top > p.left > strong')
    day_temp = temp[0].text_content()
    night_temp = temp[1].text_content()
    feel = tree.cssselect('ul.right li.top > p.right > strong')
    day_feel = feel[0].text_content()
    night_feel = feel[1].text_content()
    sunrise = tree.cssselect('section.cloud > p > strong')[0].text_content()
    sunset = tree.cssselect('section.cloud > p > strong')[1].text_content()

    weather_data = {
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

async def get_current_weather_data(code):
    url = f'https://m.weathercn.com/current-weather.do?id={code}'
    r = requests.get(url)
    with open('new_current_weather.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    tree = fromstring(r.text)

    current_time = tree.cssselect('section.real_weather > p.date')[0].text_content()[:16]
    current_weather = tree.cssselect('a.head-right > p')[0].text_content().split()[0]
    current_temp = tree.cssselect('section.real_weather > section.weather > p ')[0].text_content()
    current_feel = tree.cssselect('ol.detail_01 li > p')[1].text_content()
    sun = tree.cssselect('section.sun_moon > p span')
    sunrise = sun[0].text_content()
    sunset = sun[1].text_content()

    current_weather_data = {
        'current_time': current_time,
        'current_temp': current_temp,
        'current_feel': current_feel,
        'current_weather': current_weather,
        'sunrise': sunrise,
        'sunset': sunset
    }
    return current_weather_data


async def update_settings(settings):
    """更新本地天气数据"""
    with open('settings.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(settings, ensure_ascii=False, indent=4))