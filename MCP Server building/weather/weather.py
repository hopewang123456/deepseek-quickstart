from typing import Any
import httpx
from typing import Union, List
import datetime
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器
# 创建一个 FastMCP 实例，名字有助于识别工具
mcp = FastMCP("weather")

# --常量定义--
# 美国国家气象局API基础URL
NWS_API_BASE_URL = "https://api.weather.gov"
# 设置请求头 USER-Agent, 很多公共API要求提供
USER_AGENT = "weather-app/1.0"

# --工具定义--
@mcp.tool()
async def get_alert(state: str) -> str:
    """
    获取特定地区的天气警报信息
    """
    # 构建API请求URL
    url = f"{NWS_API_BASE_URL}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    #检查请求是否成功
    if not data or "features" not in data:
        return "无法获得预警信息或未找到相关数据"
    
    #如果feather列表为空，说明该州没有生效的预警
    if not data["features"]:
        return "该州当前没有生效的预警"
    
    # 使用列表推导和 format_alert 函数提取预警信息,将json数据转换为字符串
    alerts = [format_alert(feature) for feature in data["features"]]
    # 返回格式化后的预警信息拼接成字符串返回
    return "\n---\n".join(alerts)

#获取天气预报
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    获取特定经纬度的天气预报信息
    """
    # 构建API请求URL 使用经纬度获取天气预报
    url = f"{NWS_API_BASE_URL}/points/{latitude},{longitude}"
    point_data = await make_nws_request(url)

    if not point_data:
        return "无法取得该地的预报数据"
    
    # 提取天气预报信息
    forecast_url = point_data["properties"]["forecast"]
    # 获取预报数据
    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data:
        return "无法取得该地的预报数据"
    
    periods = forecast_data["properties"]["periods"]
    forcasts = []
    for period in periods[:5]:
        forcast = f"""
        {period["name"]}:
        温度: {period['temperature']} {period['temperatureUnit']}
        风力: {period['windSpeed']} {period['windDirection']}
        预报：{period['detailedForecast']}
        """
        forcasts.append(forcast)
    return "\n---\n".join(forcasts)


@mcp.tool()
async def get_weather_events(
    latitude: float, longitude: float, 
    days_ahead: int
) -> str:
    """
    获取指定位置和未来天数的天气事件和预报
    
    参数:
    location: 经纬度元组 (纬度, 经度) 或 州名缩写 (如 'NY')
    days_ahead: 未来天数 (0-6)
    
    返回: 包含天气事件和预报的列表
    """
    # 验证输入
    if days_ahead < 0 or days_ahead > 6:
        raise ValueError("只支持查询0-6天内的预报")
    
    # 2. 获取目标日期
    target_date = (datetime.datetime.now() + datetime.timedelta(days=days_ahead)).date()
    
    try:
        # 3. 获取网格点信息
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        if not points_data:
            return "无法取得该地的预报数据"
        
        # 4. 获取预报URL
        forecast_url = points_data["properties"]["forecast"]
        zone_url = points_data["properties"]["forecastZone"]
        
        # 5. 获取区域名称
        zone_response = await make_nws_request(zone_url)
        if not zone_response:
            return "无法取得该区域的预报数据"        
        # 6. 获取7天预报
        forecast_response = await make_nws_request(forecast_url)
        if not forecast_response:
            return "无法取得该区域7天内的预报数据"
        
        # 7. 获取天气警报
        alerts_url = f"https://api.weather.gov/alerts?point={latitude},{longitude}"
        alerts_response = await make_nws_request(alerts_url)
        if not alerts_response:
            return "无法取得该区域的警报数据"
        
        # 处理预报数据
        forcasts = []
        for period in forecast_response["properties"]["periods"]:
            period_date = datetime.datetime.fromisoformat(period["startTime"]).date()
            if period_date == target_date:
                forcast = f"""
                        {period["name"]}:
                        温度: {period['temperature']} {period['temperatureUnit']}
                        风力: {period['windSpeed']} {period['windDirection']}
                        预报：{period['detailedForecast']}
                        """
                forcasts.append(forcast)
        
        # 处理警报数据
        alerts = []
        for alert in alerts_response["features"]:
            properties = alert["properties"]
            start_time = datetime.datetime.fromisoformat(properties["onset"])
            end_time = datetime.datetime.fromisoformat(properties["expires"])
            # 检查警报是否影响目标日期
            
            if start_time.date() <= target_date <= end_time.date():
                alert = f"""
                        事件: {properties.get("event", "Unknown")}
                        描述: {properties.get("description", "N/A")}
                        区域: {properties.get("areaDesc", "N/A")}
                        严重性: {properties.get("severity", "N/A")}
                        指令: {properties.get("instruction", "N/A")}
                        """
                alerts.append(alert)
        weather_events = "\n---\n".join(forcasts) + "\n---\n" + "\n---\n".join(alerts)
        return weather_events
    except Exception as e:
        return f"获取天气事件和预报时发生错误: {str(e)}"

# --辅助函数--
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """
    发送HTTP请求到NWS API并返回响应数据
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }
    # 使用 httpx 发送HTTP请求
    async with httpx.AsyncClient() as client:
        try:
            # 发起请求
            response = await client.get(url, headers=headers, timeout=30)
            # 若响应码是 4xx, 5xx 或非200，则抛出异常
            response.raise_for_status()
            # 返回响应的JSON数据
            return response.json()
        except Exception as e:
            return None

# --辅助函数--
def format_alert(feature: dict) -> str:
    """
    格式化NWS API返回的预警信息
    """
    # 提取预警信息
    properties = feature["properties"]
    return f"""
    事件: {properties.get("event", "Unknown")}
    描述: {properties.get("description", "N/A")}
    区域: {properties.get("areaDesc", "N/A")}
    严重性: {properties.get("severity", "N/A")}
    指令: {properties.get("instruction", "N/A")}
    """

# ---服务器启动---
if __name__ == "__main__":
    # transport 参数指定服务器与客户端的通信方式，与客户端交互
    mcp.run(transport="stdio")