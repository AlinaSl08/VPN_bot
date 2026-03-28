from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from utils.delete_last_message import safe_delete, delete_last_message
from keyboards.menu_kb import menu_kb
from keyboards.admin_kb import payment_settings_kb, settings_tariff_kb, settings_payment_method_kb, get_tariff_kb
from states.menu_state import Menu
from states.admin_state import Admin
from database.db import database

admin_router = Router()

#настройка тарифов и методов оплат
@admin_router.callback_query(F.data == "payment_settings")
async def payment_settings(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=payment_settings_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

#выбор действия настройки тарифа
@admin_router.callback_query(F.data == "settings_tariff")
async def settings_tariff(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_tariff_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

#выбор лействия настройки метода
@admin_router.callback_query(F.data == "settings_payment_method")
async def settings_payment_method(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_payment_method_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

#добавление
@admin_router.callback_query(F.data.startswith("add_"))
async def settings_add(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    mode = call.data.split('_')[1]
    if mode == 'tariff':
        bot_msg = await call.message.answer('Напишите название тарифа. Примеры: "7 дней", "12 месяцев".'
                                            '\n\n❌ Как писать не надо: "Тариф 7 дней", "Тариф 12 месяцев", '
                                            'иначе будет некорректное отображение текста.'
                                            '\nТак же имя тарифа повторятся не должно, иначе он не сохранится!')
        await state.set_state(Admin.add_tariff_name)
        await state.update_data(last_msg_id=bot_msg.message_id)
    else: #доделать
        bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_payment_method_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

#название тарифа
@admin_router.message(Admin.add_tariff_name)
async def get_name(message: Message, state: FSMContext): #название задачи
    name_tariff = message.text
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    bot_msg = await message.answer('Напишите кол-во дней действия подписки.'
                                   '\nПишите целым числом, иначе отображение будет некорректное.')
    await state.update_data(last_msg_id=bot_msg.message_id, name_tariff=name_tariff)
    await state.set_state(Admin.add_tariff_days)

#кол-во дней
@admin_router.message(Admin.add_tariff_days)
async def get_days(message: Message, state: FSMContext): #название задачи
    days_tariff = int(message.text)
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    bot_msg = await message.answer('Напишите цену.\nПишите целым числом, иначе отображение будет некорректное.')
    await state.update_data(last_msg_id=bot_msg.message_id, days_tariff=days_tariff)
    await state.set_state(Admin.add_tariff_price)

#цена тарифа
@admin_router.message(Admin.add_tariff_price)
async def get_price(message: Message, state: FSMContext): #название задачи
    price_tariff = int(message.text)
    data = await state.get_data()
    last_msg_id = data.get("last_msg_id")
    await delete_last_message(last_msg_id, message)
    days_tariff = data.get("days_tariff")
    name_tariff = data.get("name_tariff")
    database.add_tariff(name_tariff, price_tariff, days_tariff)
    await message.answer(f'Добавили тариф на {days_tariff} дней. Отображение для клиента будет: — Тариф {name_tariff} — {price_tariff}₽'
                                   f'\n\nЕсли вы допустили ошибку при создании тарифа, вам необходимо удалить его и добавить заново')
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg = await message.answer("👋 С возвращением!\n\nВыберите действие 👇:", reply_markup=menu_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

#удаление
@admin_router.callback_query(F.data.startswith("del_"))
async def settings_del(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    mode = call.data.split('_')[1]
    if mode == 'tariff':
        tariffs_list = database.get_all_tariffs()
        tariffs_lines = []
        tariffs_text = ""
        for _, name, price, _, is_status in tariffs_list:
            if is_status:
                status = '🟢 Включен'
            else:
                status = '🔴 Выключен'
            tariffs_lines.append(f"{name} — {price}₽ — {status}")
        for idx, line  in enumerate(tariffs_lines, 1):
            tariffs_text += f"{idx}) {line}\n"
        bot_msg = await call.message.answer(f'Список тарифов:\n\n{tariffs_text}\nКакой тариф удалить? 👇:', reply_markup=get_tariff_kb(len(tariffs_lines), tariffs_list, mode_key=1))
        await state.update_data(last_msg_id=bot_msg.message_id)
    else: #доделать
        bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_payment_method_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

#удаление тарифа ли метода
@admin_router.callback_query(F.data.startswith("num_del_"))
async def num_tariff_or_method_del(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    num = call.data.split('_')[3]
    mode = call.data.split('_')[2]
    if mode == 'tariff':
        database.delete_tariff(num)
        await call.message.answer('✅ Тариф удален!')
    else:
        database.delete_method(num)
        await call.message.answer('✅ Метод удален!')
    await state.clear()
    await state.set_state(Menu.menu)
    bot_msg = await call.message.answer("👋 С возвращением!\n\nВыберите действие 👇:", reply_markup=menu_kb())
    await state.update_data(last_msg_id=bot_msg.message_id)

#включение
@admin_router.callback_query(F.data.startswith("on_"))
async def settings_on(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    mode = call.data.split('_')[1]
    if mode == 'tariff':
        tariffs_list = database.get_all_tariffs_off()
        tariffs_lines = []
        tariffs_text = ""
        for _, name, price, _, is_status in tariffs_list:
            if not is_status:
                status = '🔴 Выключен'
                tariffs_lines.append(f"{name} — {price}₽ — {status}")
        for idx, line in enumerate(tariffs_lines, 1):
            tariffs_text += f"{idx}) {line}\n"
        bot_msg = await call.message.answer(f'Список тарифов:\n\n{tariffs_text}\nНажмите на тариф, чтобы включить его 👇:',
                                            reply_markup=get_tariff_kb(len(tariffs_lines), tariffs_list, mode_key=2))
        await state.update_data(last_msg_id=bot_msg.message_id)
    else:  # доделать
        bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_payment_method_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

#выключение
@admin_router.callback_query(F.data.startswith("off_"))
async def settings_off(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await safe_delete(call.message)
    mode = call.data.split('_')[1]
    if mode == 'tariff':
        tariffs_list = database.get_all_tariffs()
        tariffs_lines = []
        tariffs_text = ""
        for _, name, price, _, is_status in tariffs_list:
            if is_status:
                status = '🟢 Включен'
                tariffs_lines.append(f"{name} — {price}₽ — {status}")
        for idx, line in enumerate(tariffs_lines, 1):
            tariffs_text += f"{idx}) {line}\n"
        bot_msg = await call.message.answer(
            f'Список тарифов:\n\n{tariffs_text}\nНажмите на тариф, чтобы выключить его 👇:',
            reply_markup=get_tariff_kb(len(tariffs_lines), tariffs_list, mode_key=3))
        await state.update_data(last_msg_id=bot_msg.message_id)
    else:  # доделать
        bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_payment_method_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)

#переключение
@admin_router.callback_query(F.data.startswith("turn_"))
async def switch(call: CallbackQuery, state: FSMContext):
    await call.answer()
    switch_on_or_off = call.data.split('_')[2] #вкл или выкл
    switch_mode = call.data.split('_')[1] #тариф или метод
    tariff_id = call.data.split('_')[3]
    if switch_on_or_off == 'on':
        if switch_mode == 'tariff':
            database.tariff_activation(tariff_id)
            await call.message.answer('Тариф включен 🟢')
        else:
            database.method_activation(tariff_id)
            await call.message.answer('Метод включен 🟢')
        await safe_delete(call.message)
        bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_tariff_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)
    else:
        if switch_mode == 'tariff':
            database.tariff_deactivation(tariff_id)
            await call.message.answer('Тариф выключен 🔴')
        else:
            database.method_deactivation(tariff_id)
            await call.message.answer('Метод выключен 🔴')
        await safe_delete(call.message)
        bot_msg = await call.message.answer('Выберите действие ниже 👇:', reply_markup=settings_payment_method_kb())
        await state.update_data(last_msg_id=bot_msg.message_id)



