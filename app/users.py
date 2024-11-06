import os
import sys
import requests
import json
import logging
from dotenv import load_dotenv
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram import types, F
import app.keyboard as kb
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("bot.log"),
                        logging.StreamHandler(sys.stdout)
                    ]
)
router = Router()

def check_user_exists(user_id):
    url = f"{os.getenv('API_URL')}/bot-users"
    response = requests.get(url=url).text
    data = json.loads(response)
    for i in data:
        if i["user_id"] == str(user_id):
            return True
    return False

def create_user(username, name, user_id, number):
    url = f"{os.getenv('API_URL')}/bot-users"
    requests.post(url=url, data={'username': username, "name": name, "number": number, "user_id": user_id})

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply("Assalomu Aleykum\nBotimizga xush kelibsiz!", reply_markup=kb.contact)

@router.message(F.contact)
async def handle_contact(message: types.Message):
    contact = message.contact
    user_id = contact.user_id
    # Check if the user exists
    if check_user_exists(user_id):
        await message.reply(f"Salom, {contact.first_name}! Siz allaqachon ro'yhatdan o'tgansiz.", reply_markup=kb.main)
    else:
        create_user(message.from_user.username, contact.first_name, user_id, contact.phone_number)
        await message.reply("Siz muvaffaqiyatli ro'yhatdan o'tdingiz.", reply_markup=kb.main)

