from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton)


contact = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text= "Ro'yhatdan o'tish", request_contact=True)]], resize_keyboard=True)

main = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='Katalog'),
        KeyboardButton(text="E'lon berish")
    ],
    [
        KeyboardButton(text='Profil'),
        KeyboardButton(text='Biz haqimizda')
    ]], resize_keyboard=True)

add = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='Mashinalar')
    ],
    [
        KeyboardButton(text="Uy joy")
    ]], resize_keyboard=True)

myads = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text= "Mening e'lonlarim")
    ],
    [
        KeyboardButton(text="Orqaga")
    ]], resize_keyboard=True)
