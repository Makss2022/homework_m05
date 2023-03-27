import aiohttp
import asyncio
import sys
from typing import Iterable, Awaitable
import platform
from datetime import date, timedelta
import json
from timing import async_timed

EUR = "EUR"
USD = "USD"
BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="


def url_list(days: int) -> list[str]:
    url_list = []
    for el in range(days):
        today = date.today()
        delta_day = timedelta(days=el)
        day = today - delta_day
        day_str = day.strftime("%d.%m.%Y")
        url = BASE_URL + day_str
        url_list.append(url)
    return url_list


def list_rate_currency_days(url_list: list[str]) -> Iterable[Awaitable]:
    result = [rate_currency_day(url) for url in url_list]
    return result


async def rate_currency(currency: str, list_courses: list) -> dict:
    result_dct = {}
    for dct in list_courses:
        if dct["currency"] == currency:
            result_dct["sale"] = dct["saleRate"]
            result_dct["purchase"] = dct["purchaseRate"]
            return {currency: result_dct}


async def rate_currency_day(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    date_bank = await response.json()
                    if date_bank:
                        result_day = {}
                        rate_eur = rate_currency(
                            EUR, date_bank["exchangeRate"])
                        rate_usd = rate_currency(
                            USD, date_bank["exchangeRate"])
                        rate_eur, rate_usd = await asyncio.gather(rate_eur, rate_usd)
                        result_day[date_bank["date"]] = rate_eur | rate_usd
                        return result_day
                    return 'Not found'
                else:
                    print(f"Error status: {response.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error: {url}', str(err))


@async_timed()
async def main():
    list_url = url_list(days)
    result_listt_rates = list_rate_currency_days(list_url)
    return await asyncio.gather(*result_listt_rates)


if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            days = 1
        else:
            days = int(sys.argv[1])
        if not 0 < days <= 10:
            raise

        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        result = asyncio.run(main())
        print(json.dumps(result, indent=4, sort_keys=True))

    except (ValueError, RuntimeError):
        print("Введите количество дней от 1 до 10")
