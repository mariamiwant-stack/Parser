"""Константы и справочные данные для краулера."""

from __future__ import annotations

TOP_16_RU_CITIES: list[str] = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Нижний Новгород",
    "Самара",
    "Омск",
    "Казань",
    "Челябинск",
    "Ростов-на-Дону",
    "Уфа",
    "Волгоград",
    "Пермь",
    "Красноярск",
    "Воронеж",
    "Саратов",
]

CITY_SLUGS: dict[str, str] = {
    "Москва": "moscow",
    "Санкт-Петербург": "saint_petersburg",
    "Новосибирск": "novosibirsk",
    "Екатеринбург": "ekaterinburg",
    "Нижний Новгород": "nizhny_novgorod",
    "Самара": "samara",
    "Омск": "omsk",
    "Казань": "kazan",
    "Челябинск": "chelyabinsk",
    "Ростов-на-Дону": "rostov_on_don",
    "Уфа": "ufa",
    "Волгоград": "volgograd",
    "Пермь": "perm",
    "Красноярск": "krasnoyarsk",
    "Воронеж": "voronezh",
    "Саратов": "saratov",
}

DEFAULT_DISPOSABLE_DOMAIN_BLACKLIST: set[str] = {
    "example.com",
    "example.org",
    "example.net",
    "mailinator.com",
    "tempmail.com",
    "yopmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "test.com",
    "invalid",
}

COMMON_CONTACT_PATHS: tuple[str, ...] = (
    "",
    "/contacts",
    "/contact",
    "/kontakty",
    "/o-kompanii/kontakty",
    "/about/contacts",
)

CAPTCHA_MARKERS: tuple[str, ...] = (
    "captcha",
    "g-recaptcha",
    "hcaptcha",
    "проверка, что вы не робот",
    "проверка человеком",
    "i am not a robot",
)
