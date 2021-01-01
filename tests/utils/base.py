from aiohttp.web_urldispatcher import DynamicResource


def url_for(path: str, **kwargs) -> str:
    """Генерирует URL с подставновкой url-параметров."""
    kwargs = {
        key: str(value)  # все значения должны быть str для DynamicResource
        for key, value in kwargs.items()
    }
    return str(DynamicResource(path).url_for(**kwargs))
