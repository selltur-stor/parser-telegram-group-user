from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsAdmins
from telethon.tl.types import UserStatusOffline, UserStatusOnline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth, UserStatusEmpty, ChannelParticipantAdmin, ChannelParticipantCreator
import pandas as pd
import datetime

# Замените API_ID и API_HASH значениями из вашего приложения Telegram
API_ID = 'You id'
API_HASH = 'You hash'
PHONE = 'You number'

# Создание клиента
client = TelegramClient('session_name', API_ID, API_HASH)

async def main():
    # Вход в аккаунт
    await client.start(PHONE)
    
    # Получение списка всех чатов
    chats = []
    last_date = None
    chunk_size = 200
    groups = []
    
    result = await client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash=0
            ))
    
    chats.extend(result.chats)
    
    for chat in chats:
        if getattr(chat, 'megagroup', False):
            groups.append(chat)
    
    # Вывод всех групп и выбор пользователя
    print('Выберите группу:')
    for i, group in enumerate(groups):
        print(f"{i} - {group.title}")
    
    group_index = int(input("Введите номер группы: "))
    target_group = groups[group_index]

    # Получение участников выбранной группы
    all_participants = []
    offset = 0
    
    while True:
        participants = await client(GetParticipantsRequest(
            channel=target_group,
            filter=ChannelParticipantsSearch(''),
            offset=offset,
            limit=chunk_size,
            hash=0
        ))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset += len(participants.users)
    
    # Получение администраторов группы
    admins = []
    offset = 0
    
    while True:
        admin_participants = await client(GetParticipantsRequest(
            channel=target_group,
            filter=ChannelParticipantsAdmins(),
            offset=offset,
            limit=chunk_size,
            hash=0
        ))
        if not admin_participants.users:
            break
        admins.extend(admin_participants.participants)
        offset += len(admin_participants.participants)
    
    # Создание Excel таблицы
    data = []
    for user in all_participants:
        last_online = None
        if isinstance(user.status, UserStatusOffline):
            last_online = user.status.was_online.replace(tzinfo=None) if user.status.was_online.tzinfo else user.status.was_online
        elif isinstance(user.status, UserStatusOnline):
            last_online = datetime.datetime.now().replace(tzinfo=None)
        elif isinstance(user.status, (UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth, UserStatusEmpty)):
            last_online = "Confident"
        
        is_bot = user.bot
        is_admin = False
        admin_title = ""
        
        for admin in admins:
            if admin.user_id == user.id:
                is_admin = True
                admin_title = admin.rank if admin.rank else 'Admin'

        data.append([
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            last_online,
            is_bot,
            is_admin,
            admin_title
        ])
    
    df = pd.DataFrame(data, columns=['ID', 'Username', 'First Name', 'Last Name', 'Last Online', 'Bot', 'Admin', 'Admin Title'])
    
    # Формирование имени файла
    filename = f"{target_group.title}_users.xlsx"
    filename = filename.replace(" ", "_")  # Замена пробелов на подчеркивания
    
    df.to_excel(filename, index=False)
    
    print(f"Данные успешно сохранены в '{filename}'.")

# Запуск клиента и основной функции
with client:
    client.loop.run_until_complete(main())
