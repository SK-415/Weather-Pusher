import nonebot, json, requests
from nonebot.command.argfilter import extractors, validators

from datetime import datetime, timedelta, timezone


with open('apikey.txt', encoding='utf8') as f:
        APIKEY = f.read().strip()

@nonebot.on_command('天气', shell_like=True)
async def weather(session):
    """根据关键字返回可能的城市，并设置地区"""
    weather_data = await read_weather_data()
    city_name = await member_in_list(weather_data, session.ctx['user_id'])
    if city_name:
        await session.finish(await format_msg(weather_data[city_name], city_name))
    
    if session.is_first_run:
        await session.send('您还没有注册过推送地区，接下来将自动开始注册') # 之后添加随时可以输入***退出
    key_word = session.get('key_word', prompt="您希望推送哪里的天气？（仅支持中文名）", arg_filters=[extractors.extract_text, str.strip, validators.not_empty('输入不能为空')])
    if key_word in weather_data['city_list']:
        weather_data['city_list'][key_word]['members'].append(session.ctx['user_id'])
        await update_weather_data(weather_data)
        await session.finish(f'“{key_word}”已经存在，已将您的推送地区设置为“{key_word}”')

    url = f'http://dataservice.accuweather.com/locations/v1/cities/autocomplete?apikey=%09{APIKEY}&q={key_word}&language=zh-cn'
    response = requests.get(url)
    search_results = json.loads(response.text)
    format_str = await format_results(search_results)
    if session.current_key != 'selection':
        await session.send(format_str)
    selection = session.get('selection', prompt="回复序号确认地区", arg_filters=[extractors.extract_text, str.strip, validators.not_empty('输入不能为空'), int])
    current_location = search_results[selection]
    city = current_location['LocalizedName']
    weather_data['city_list'][city] = {'code': current_location['Key'], 'members': [session.ctx['user_id']]}
    weather_data[city] = await get_weather_data(current_location['Key'])
    
    await update_weather_data(weather_data)
    await session.send(f"已将您的天气推送地区设为：\n {format_str.splitlines()[selection]}")

async def member_in_list(weather_data, user_id):
    """检查QQ是否已经录入，并返回所在城市"""
    for city in weather_data['city_list']:
        for qq in weather_data['city_list'][city]['members']:
            if qq == user_id:
                return city
    return False

async def format_results(results):
    format_string = ''
    for i in range(len(results)):
        r = results[i]
        format_string += f"{i}. {r['LocalizedName']} ({r['Country']['LocalizedName']}, {r['AdministrativeArea']['LocalizedName']})\n"
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
    weather_str = f"城市：{city}\n日期：{w['日期']}\n天气（白天）：{w['天气（白天）']}\n天气（夜晚）：{w['天气（夜晚）']}\n" \
        f"最高：{w['最高温度']}°C\n最低：{w['最低温度']}°C"
    return weather_str

async def tz_check(time_zone):
    """查看是否有时区到早上6点了"""
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    now = utc_dt.hour
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
    url = f'http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location}?apikey={APIKEY}&language=zh-cn&metric=true'
    response = requests.get(url)
    get_data = json.loads(response.text)
    try:
        w = get_data['DailyForecasts'][0]
        weather_data = {'日期': w['Date'][:10], 
        'time_zone': int(w['Date'][19:22]),
        '天气（白天）': w['Day']['IconPhrase'], 
        '天气（夜晚）': w['Night']['IconPhrase'],
        '最高温度': w['Temperature']['Maximum']['Value'], 
        '最低温度': w['Temperature']['Minimum']['Value']}
    except KeyError:
        weather_data = '今日请求次数已到达上限'
    return weather_data

async def update_weather_data(weather_data):
    """更新本地天气数据"""
    with open('weather.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(weather_data, ensure_ascii=False, indent=4))