import os 
import aiohttp
import tempfile
import app.keyboard as kb
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.state import AddCarState, AddHouseState
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
router = Router()


# # ---- Yordamchi funksiya API chaqiruvlari uchun ---- #
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None
        
async def fetch_image(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()    
        else:
            return None
        

# # ---- Katalogni ko'rsatish ---- #
@router.message(F.text == 'Katalog')
async def katalog_btn(message: Message):
    data = await fetch_data(f"{os.getenv('API_URL')}/catalog")
    if data:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=item['name'], callback_data=f"catalog_{item['id']}")] for item in data
        ])
        await message.answer("Kataloglar:", reply_markup=keyboard)
    else:
        await message.answer("Katalog ma'lumotlari topilmadi.")

# # ---- Umumiy katalog va mahsulot callback ishlovchi ---- #
@router.callback_query(F.data.startswith("catalog_"))
async def process_catalog_callback(callback_query: CallbackQuery, bot: Bot):
    catalog_id = callback_query.data.split('_')[1]
    url = f"{os.getenv('API_URL')}/{'car' if catalog_id == '1' else 'house'}-ads"
    
    data = await fetch_data(url)
    if data:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{item['name']} - {item['price']} so'm", 
                                  callback_data=f"{('car' if catalog_id == '1' else 'house')}_item_{item['id']}")] 
            for item in data
        ])
        await bot.send_message(callback_query.from_user.id, "Mahsulotlar ro'yxati:", reply_markup=keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, "Mahsulotlar mavjud emas.")

# ---- Mahsulot ma'lumotlarini ko'rsatish ---- #
async def get_item_message(bot, item_data, item_type, chat_id):
    media_group = []

    if item_type == "car":
        image_urls = [img['img'] for img in item_data.get('img', [])]
        caption = (
            f"🚗 Nomi: {item_data.get('name', 'Unknown')}\n\n"
            f"📍 Pozitsiyasi: {item_data.get('pozitsiya', 'Unknown')}\n"
            f"💰 Narxi: {item_data.get('price', 'Unknown')} so'm\n"
            f"📅 Yili: {item_data.get('year', 'Unknown')} yil\n"
            f"🎨 Rangi: {item_data.get('color', 'Unknown')}\n"
            f"📊 Probeg: {item_data.get('mileage', 'Unknown')} km\n"
            f"⛽ Fuel type: {item_data.get('oil', 'Unknown')}\n"
            f"📝 Tavsif: {item_data.get('description', 'Not available')}\n\n"
            f"E'lon beruvchi: {item_data.get('created_by')}"
        )
    elif item_type == "house":
        image_urls = [img['img'] for img in item_data.get('img', [])]
        caption = (
            f"🏠 Nomi: {item_data.get('name', 'Unknown')}\n"
            f"💰 Narxi: {item_data.get('price', 'Unknown')} so'm\n"
            f"📏 Maydoni: {item_data.get('area', 'Unknown')} kv.m\n"
            f"🛏️ Xonalar soni: {item_data.get('rooms', 'Unknown')}\n"
            f"📍 Manzili: {item_data.get('location', 'Unknown')}\n"
            f"📝 Tavsif: {item_data.get('description', 'Not available')}\n\n"
            f"E'lon beruvchi: {item_data.get('created_by')}"
        )
    else:
        return "E'lon topilmadi"

    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(image_urls):
            image_data = await fetch_image(session, url)
            if image_data:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(image_data)
                    temp_file_name = temp_file.name
                media_group.append(InputMediaPhoto(
                    media=FSInputFile(temp_file_name),
                    caption=caption if i == 0 else None
                ))
            else:
                await bot.send_message(chat_id, f"Failed to fetch image from {url}")

    if media_group:
        await bot.send_media_group(chat_id=chat_id, media=media_group)
    else:
        await bot.send_message(chat_id, caption)

    for media in media_group:
        try:
            os.remove(media.media.path)
        except FileNotFoundError:
            continue

    return None

@router.callback_query(F.data.startswith(("car_item_", "house_item_")))
async def process_item_callback(callback_query: CallbackQuery, bot):
    item_type = "car" if "car_item" in callback_query.data else "house"
    item_id = int(callback_query.data.split('_')[2])
    
    data = await fetch_data(f"{os.getenv('API_URL')}/{item_type}-ads")

    if data:
        item = next((x for x in data if x['id'] == item_id), None)
        if item:
            message = await get_item_message(bot, item, item_type, callback_query.from_user.id)
            if message:  
                await bot.send_message(callback_query.from_user.id, message)
        else:
            await bot.send_message(callback_query.from_user.id, f"{item_type.capitalize()} not found.")
    else:
        await bot.send_message(callback_query.from_user.id, "Error fetching data.")

# ---- E'lon berish tugmasi va kategoriya tanlash ---- #
@router.message(F.text == "E'lon berish")
async def elon_btn(message: Message):
    data = await fetch_data(f"{os.getenv('API_URL')}/catalog")
    if data:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=item['name'], callback_data=f"category_{item['id']}")] for item in data
        ])
        await message.answer("Katalogdan tanlang:", reply_markup=keyboard)
    else:
        await message.answer("Katalog ma'lumotlari topilmadi.")

@router.callback_query(F.data.startswith("category_"))
async def get_category(callback_query: CallbackQuery, state: FSMContext):
    """Kategoriya tanlash va holatni boshlash."""
    category_id = int(callback_query.data.split('_')[1])  # 'category_id' formatidan 'id' ni ajratamiz

    # Kategoriyani FSMga saqlab qo'yamiz
    await state.update_data(catalog_id=category_id)

    if category_id == 1:  # Mashinalar katalogi
        await callback_query.message.answer("Mashina e'loni berish uchun tayyor bo'ling!")
        await start_add_car(callback_query.message, state)  # Funksiyani to'g'ri chaqiramiz

    elif category_id == 2:  # Uy-joy katalogi
        await callback_query.message.answer("Uy-joy e'loni berish uchun tayyor bo'ling!")
        await start_add_house(callback_query.message, state)  # Uy katalogi uchun chaqirish

    else:
        await callback_query.message.answer("Bu kategoriya mavjud emas.")
    
    await callback_query.answer()  # Callback queryni yopamiz

async def get_seller_info(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8000/api/v1/bot-users") as response:
            if response.status == 200:
                users = await response.json()
                for user in users:
                    if user["user_id"] == str(user_id):
                        return user["number"]  # Foydalanuvchi ma'lumotidan ID ni qaytarish
            else:
                return None
            
@router.message(F.text == "E'lon berish")
async def elon_btn(message: Message):
    data = await fetch_data(f"{os.getenv('API_URL')}/catalog")
    if data:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=item['name'], callback_data=f"category_{item['id']}")] for item in data
        ])
        await message.answer("Katalogdan tanlang:", reply_markup=keyboard)
    else:
        await message.answer("Katalog ma'lumotlari topilmadi.")

@router.callback_query(F.data.startswith("category_"))
async def get_category(callback_query: CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])  

    await state.update_data(catalog_id=category_id)

    if category_id == 1:  
        await callback_query.message.answer("Mashina e'loni berish uchun tayyor bo'ling!")
        await start_add_car(callback_query.message, state)  

    elif category_id == 2:  
        await callback_query.message.answer("Uy-joy e'loni berish uchun tayyor bo'ling!")
        await start_add_house(callback_query.message, state) 

    else:
        await callback_query.message.answer("Bu kategoriya mavjud emas.")
    
    await callback_query.answer()  

@router.message(Command("add_car"))
async def start_add_car(message: Message, state: FSMContext):
    user_data = await state.get_data() 

    if "catalog_id" not in user_data:
        await message.answer("Iltimos, katalogni tanlang.")
        return

    await message.answer("Avtomobil nomini kiriting:")
    await state.set_state(AddCarState.name) 

@router.message(AddCarState.name)
async def enter_car_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Narxni kiriting:")
    await state.set_state(AddCarState.price)

@router.message(AddCarState.price)
async def enter_car_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Yilni kiriting:")
    await state.set_state(AddCarState.year)

@router.message(AddCarState.year)
async def enter_car_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text)
    await message.answer("Pozitsiyani kiriting:")
    await state.set_state(AddCarState.pozitsiya)

@router.message(AddCarState.pozitsiya)
async def enter_car_pozitsiya(message: Message, state: FSMContext):
    await state.update_data(pozitsiya=message.text)
    await message.answer("Rangni kiriting:")
    await state.set_state(AddCarState.color)

@router.message(AddCarState.color)
async def enter_car_color(message: Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer("Yoqilg'i turini kiriting:")
    await state.set_state(AddCarState.oil)

@router.message(AddCarState.oil)
async def enter_car_oil(message: Message, state: FSMContext):
    await state.update_data(oil=message.text)
    await message.answer("Probegni kiriting:")
    await state.set_state(AddCarState.mileage)

@router.message(AddCarState.mileage)
async def enter_car_mileage(message: Message, state: FSMContext):
    await state.update_data(mileage=message.text)
    await message.answer("Tavsifni kiriting:")
    await state.set_state(AddCarState.description)

@router.message(AddCarState.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Rasmlarni yuklang (maksimum 4 ta):")
    await state.set_state(AddCarState.images)

@router.message(AddCarState.images, F.photo)
async def process_images(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    images = data.get('images', [])

    if not os.path.exists('photos/car'):
        os.makedirs('photos/car')

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)

    original_file_name = file.file_path.split('/')[-1]  
    file_path = os.path.join('photos/car', original_file_name) 

    await bot.download_file(file.file_path, file_path)

    images.append(file_path) 
    await state.update_data(images=images)
    await message.answer(f"{len(images)} ta rasm yuklandi. Yana rasm yuklashingiz mumkin yoki /finish buyrug'ini yuborish orqali e'lonni yakunlang.")

    if len(images) >= 4:
        await message.answer("4 ta rasm yuklandi. Endi e'lonni yakunlash uchun /finish buyrug'ini yuboring.")

@router.message(AddCarState.images, F.text == "/finish")
async def finish_ad(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        seller_number = await get_seller_info(message.from_user.id)

        data = {
            "catalog": user_data["catalog_id"],
            "name": user_data["name"],
            "price": float(user_data["price"]),
            "pozitsiya": int(user_data["pozitsiya"]),
            "year": int(user_data["year"]),
            "color": user_data["color"],
            "oil": user_data["oil"],
            "mileage": int(user_data["mileage"]),
            "description": user_data["description"],
            "created_by": seller_number
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:8000/api/v1/car-ads", json=data) as response:
                if response.status == 201:
                    response_data = await response.json()
                    car_id = response_data['id']
                    await message.answer("Rasmlarni yuklaymiz...")
                else:
                    error = await response.text()
                    await message.answer("E'lon qo'shishda xatolik yuz berdi!")
                    return

            # Upload images
            for file_path in user_data.get('images', []):
                with open(file_path, 'rb') as img_file:  
                    form_data = aiohttp.FormData()
                    form_data.add_field('car', str(car_id)) 
                    form_data.add_field('img', img_file, filename=os.path.basename(file_path))

                    async with session.post("http://127.0.0.1:8000/api/v1/car-ads/add_img", data=form_data) as img_response:
                        if img_response.status != 201:
                            error = await img_response.text()
                            await message.answer("E'lon qo'shishda xatolik yuz berdi!")
                        else:
                            await message.answer("Rasm muvaffaqiyatli yuklandi.")

        ad_preview = (
            f"🚗 Nomi: {user_data['name']}\n"
            f"💰 Narxi: {user_data['price']} so'm\n"
            f"📅 Yili: {user_data['year']}\n"
            f"📍 Pozitsiyasi: {user_data['pozitsiya']}\n"
            f"🎨 Rangi: {user_data['color']}\n"
            f"⛽ Yoqilg'i turi: {user_data['oil']}\n"
            f" Probeg: {user_data['mileage']} km\n"
            f"📝 Tavsif: {user_data['description']}\n"
            f" Rasmlar soni: {len(user_data.get('images', []))}"
        )

        await message.answer(f"E'lon va rasmlar muvaffaqiyatli qo'shildi\n\n {ad_preview}")
        await message.answer("E'lon ma'lumotlari qabul qilindi va adminga jo'natildi!\n\n<a href='https://t.me/kxsmskxmks'>Admin bilan bog'lanish</a>", parse_mode=ParseMode.HTML)
        await state.clear()

    except Exception as e:
        print(f"Unexpected error: {e}")
        await message.answer("Kutilmagan xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.message(Command("add_house"))
async def start_add_house(message: Message, state: FSMContext):
    """Uy-joy e'lonini qo'shishni boshlash."""
    user_data = await state.get_data()  
 
    if "catalog_id" not in user_data: 
        await message.answer("Iltimos, avval katalogni tanlang.")
        return

    await message.answer("Uy-joy nomini kiriting:")
    await state.set_state(AddHouseState.name)


@router.message(AddHouseState.name)
async def enter_house_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Narxni kiriting:")
    await state.set_state(AddHouseState.price)

@router.message(AddHouseState.price)
async def enter_house_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Maydonini (kv.m) kiriting:")
    await state.set_state(AddHouseState.area)

@router.message(AddHouseState.area)
async def enter_house_area(message: Message, state: FSMContext):
    await state.update_data(area=message.text)
    await message.answer("Xona sonini kiriting:")
    await state.set_state(AddHouseState.rooms)

@router.message(AddHouseState.rooms)
async def enter_house_rooms(message: Message, state: FSMContext):
    await state.update_data(rooms=message.text)
    await message.answer("Uyning manzilini kiriting:")
    await state.set_state(AddHouseState.location)

@router.message(AddHouseState.location)
async def enter_house_rooms(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer("Tavsifni kiriting:")
    await state.set_state(AddHouseState.description)

@router.message(AddHouseState.description)
async def process_house_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Rasmlarni yuklang (maksimum 4 ta):")
    await state.set_state(AddHouseState.images)

@router.message(AddHouseState.images, F.photo)
async def process_images(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    images = data.get('images', [])

    if not os.path.exists('photos/house'):
        os.makedirs('photos/house')

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)

    original_file_name = file.file_path.split('/')[-1]  
    file_path = os.path.join('photos/house', original_file_name)  

    await bot.download_file(file.file_path, file_path)

    images.append(file_path) 
    await state.update_data(images=images)
    await message.answer(f"{len(images)} ta rasm yuklandi. Yana rasm yuklashingiz mumkin yoki /finish buyrug'ini yuborish orqali e'lonni yakunlang.")

    if len(images) >= 4:
        await message.answer("4 ta rasm yuklandi. Endi e'lonni yakunlash uchun /finish buyrug'ini yuboring.")

@router.message(AddHouseState.images, F.text == "/finish")
async def finish_ad(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        seller_number = await get_seller_info(message.from_user.id)

        data = {
            "catalog": user_data["catalog_id"],
            "name": user_data["name"],
            "price": float(user_data["price"]),
            "area": float(user_data["area"]),
            "rooms": int(user_data["rooms"]),
            "location": user_data["location"],
            "description": user_data["description"],
            "created_by": seller_number,
        }

        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:8000/api/v1/house-ads", json=data) as response:
                if response.status == 201:
                    response_data = await response.json()
                    house_id = response_data['id']
                    await message.answer("Rasmlarni yuklaymiz...")
                else:
                    error = await response.text()
                    await message.answer("E'lon qo'shishda xatolik yuz berdi!")
                    return

            for file_path in user_data.get('images', []):
                with open(file_path, 'rb') as img_file: 
                    form_data = aiohttp.FormData()
                    form_data.add_field('house', str(house_id)) 
                    form_data.add_field('img', img_file, filename=os.path.basename(file_path))

                    async with session.post("http://127.0.0.1:8000/api/v1/house-ads/add_img", data=form_data) as img_response:
                        if img_response.status != 201:
                            error = await img_response.text()
                            await message.answer("Kutilmagan xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
                        else:
                            await message.answer("Rasm muvaffaqiyatli yuklandi.")
        ad_preview = (
            f"🚗 Nomi: {user_data['name']}\n"
            f"💰 Narxi: {user_data['price']} so'm\n"
            f"📏 Maydoni: {user_data['area']}\n"
            f"📍 Manzili: {user_data['location']}\n"
            f"🛏️ Xonalar soni: {user_data['rooms']} km\n"
            f"📝 Tavsif: {user_data['description']}\n"
            f" Rasmlar soni: {len(user_data.get('images', []))}"
        )

        await message.answer(f"E'lon va rasmlar muvaffaqiyatli qo'shildi\n\n {ad_preview}")
        await message.answer("E'lon ma'lumotlari qabul qilindi va adminga jo'natildi!\n\n<a href='https://t.me/kxsmskxmks'>Admin bilan bog'lanish</a>", parse_mode=ParseMode.HTML)
        await state.clear()

    except Exception as e:
        print(f"Unexpected error: {e}")
        await message.answer("Kutilmagan xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")


@router.message(F.text == "Profil")
async def show_profile(message: Message):
    user_id = str(message.from_user.id)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://127.0.0.1:8000/api/v1/bot-users") as response:
            if response.status == 200:
                bot_users = await response.json()
                user_data = next((user for user in bot_users if user["user_id"] == user_id), None)
                
                if user_data:
                    created_at_datetime = datetime.fromisoformat(user_data['created_at'])
                    formatted_date = created_at_datetime.strftime("%Y-%m-%d")
                    await message.answer(
                        f"👤 Ism: {user_data['name']}\n"
                        f"📞 Telefon raqam: {user_data['number']}\n"
                        f"📅 Ro'yxatdan o'tgan sana: {formatted_date}\n",
                        parse_mode="HTML", reply_markup=kb.myads
                    )
                else:
                    await message.answer("Foydalanuvchi ma'lumotlari topilmadi.")
            else:
                await message.answer("Foydalanuvchi ma'lumotlarini olishda xatolik yuz berdi.")

@router.message(F.text == "Mening e'lonlarim")
async def show_user_ads(message: Message):
    user_number = await get_seller_info(message.from_user.id)
    
    if not user_number:
        await message.answer("Sizning e'lonlaringiz topilmadi.")
        return

    ads_message = "📋 Sizning e'lonlaringiz:\n\n"
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8000/api/v1/car-ads") as car_response:
            if car_response.status == 200:
                car_ads = await car_response.json()
                user_car_ads = [ad for ad in car_ads if ad.get("created_by") == user_number]
                
                for ad in user_car_ads:
                    ads_message += (
                        f"🚗 Mashina: {ad['name']}\n"
                        f"💰 Narxi: {ad['price']} so'm\n"
                        f"📅 Yili: {ad['year']}\n\n"
                    )
        
        async with session.get("http://127.0.0.1:8000/api/v1/house-ads") as house_response:
            if house_response.status == 200:
                house_ads = await house_response.json()
                user_house_ads = [ad for ad in house_ads if ad.get("created_by") == user_number]
                
                for ad in user_house_ads:
                    ads_message += (
                        f"🏠 Uy: {ad['name']}\n"
                        f"💰 Narxi: {ad['price']} so'm\n\n"
                    )
    
    if ads_message.strip() != "📋 Sizning e'lonlaringiz:":
        await message.answer(ads_message)
    else:
        await message.answer("Sizda hozircha hech qanday e'lon yo'q.")

@router.message(F.text == 'Orqaga')
async def process_go_back(message: Message):
    await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=kb.main)


