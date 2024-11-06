import os
import asyncio

from dotenv import load_dotenv
from aiogram.types import BotCommand
from aiogram import Bot, Dispatcher ,types
from app.users import router as user_router
from app.func import router as btn_router



async def main():
    load_dotenv()
    
    bot = Bot(token=os.getenv('TOKEN'))
    dp = Dispatcher()
    dp.include_routers(user_router, btn_router)
    
    await bot.set_my_commands([
        BotCommand(command='/start', description='Botni ishga tushirish'),
        BotCommand(command='/help', description='Yordam'),
        BotCommand(command='/news', description='Eng muhim yangliklar')
    ])
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
