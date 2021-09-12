from aiohttp.web_urldispatcher import DynamicResource


def url_for(path: str, **kwargs) -> str:
    """Генерирует URL с подставновкой url-параметров."""
    kwargs = {key: str(value) for key, value in kwargs.items()}  # все значения должны быть str для DynamicResource
    return str(DynamicResource(path).url_for(**kwargs))
