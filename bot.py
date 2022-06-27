import os
import json
import emoji
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from dotenv import load_dotenv

# загрузка переменных окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
TOKEN = os.environ.get('TOKEN')

# смена рабочей директории
os.chdir(os.getcwd() + '/blackbird')
print(os.getcwd())

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

start_message = "Привет!\nНапиши мне любой никнейм, я найду все совпадения!"


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message, state: FSMContext):
    sites = ['YouTube', 'Twitter', 'TikTok']
    names = await state.get_data()
    names['names'] = ''
    for site in sites:
        names['names'] += f'{site};'

    await state.update_data(names=names['names'])
    await message.answer(start_message)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(start_message)


@dp.message_handler(commands=['choice_search'])
async def process_help_command(message: types.Message, state: FSMContext):
    names = await state.get_data()
    keyboard = create_keyboard_search(names)
    await message.answer("Выберите нужные источники, по которым будет осуществляться поиск: ", reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith="add_search_"))
async def send_random_value(call: types.CallbackQuery, state: FSMContext):
    action = call.data.split("_")[2]
    names = await state.get_data()
    if action not in names['names']:
        names['names'] += action + ';'
    else:
        names_list: list = names['names'].split(';')
        names_list.pop(names_list.index(action))
        names['names'] = ';'.join(names_list)
    await state.update_data(names=names['names'])
    await call.message.edit_reply_markup(create_keyboard_search(names))
    await call.answer()


def create_keyboard_search(names: dict):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for name in all_search_list():
        text = f'{name}'
        if name in names['names']:
            text = emoji.emojize(":check_mark_button: ") + text
        buttons.append(types.InlineKeyboardButton(text=text, callback_data=f"add_search_{name}"))
    keyboard.add(*buttons)
    return keyboard


@dp.message_handler()
async def echo_message(msg: types.Message, state: FSMContext):
    name = msg.text.lower()
    await bot.send_message(msg.from_user.id, emoji.emojize(":magnifying_glass_tilted_right:") + ' Search...')
    exists_names = list(map(lambda name: name[:-5], os.listdir('results/')))
    if name not in exists_names:
        try:
            os.system(f'python blackbird.py -u "{name}"')
        except Exception:
            await bot.send_message(msg.from_user.id, 'Произошла ошибка, пожалуйста, попробуйте позже(')
            return
    names = await state.get_data()
    print(names)
    results = parse_info(name, names['names'].split(';'))
    print(results)
    if results:
        await msg.answer(results)
    else:
        await msg.answer('Совпадений не нашлось. Проверь никнейм на корректность и попробуй еще раз!')
    await msg.answer('Напиши любой никнейм. Я найду все совпадения!')


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("help", "Помощь"),
        types.BotCommand("choice_search", "Выбрать нужные сайты"),
    ])


def parse_info(name: str, sites: list) -> str:
    with open(f"results/{name}.json", "r") as read_file:
        data = json.load(read_file)
        response = data['sites']
        results = ''
        for site in response:
            if site.get('status', None) == 'FOUND' and site.get('app') in sites:
                results += emoji.emojize(":green_circle:") + f' <b>{site["app"]}</b>: '\
                                                             f'<a href="{site["url"]}">ссылка</a>\n'

    return results


def all_search_list() -> list:
    results = []
    with open(f"results/example.json", "r") as read_file:
        data = json.load(read_file)
        sites = data['sites']
        for site in sites:
            results.append(site['app'])
    return results


if __name__ == '__main__':
    executor.start_polling(dp)
