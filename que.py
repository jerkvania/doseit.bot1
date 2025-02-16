import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, CallbackQueryHandler, ContextTypes
)

# 🔹 Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Загружаем токен и вебхук URL из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7085352038:AAHD5jSpLk_sYq4gLW44iukYhEa3YHafHDA")
WEBHOOK_URL = "https://doseit.bot1.onrender.com/webhook"
PORT = int(os.getenv("PORT", 5000))

# 🔹 Определяем состояния опроса
LANGUAGE, QUESTION_1, QUESTION_2, QUESTION_3, QUESTION_4, QUESTION_5, QUESTION_6 = range(7)

# 🔹 Словарь для хранения ответов пользователя
user_responses = {}

# Language texts
language_texts = {
    'ru': {
        'welcome': "👋 Добро пожаловать! Этот быстрый опросник поможет определить, какой комплект биодобавок DoseIt лучше всего подойдет вам для старта: комплект для печени, нервной системы или ЖКТ.📝",
        'question_1': "Вопрос 1: Как часто вы испытываете проблемы с пищеварением? (например, вздутие, тяжесть, запоры, диарея)\n\nA: Часто — почти каждый день или более 3 раз в неделю.\nB: Иногда — зависит от пищи или образа жизни.\nC: Редко — почти никогда не испытываю проблем.",
        'question_2': "Вопрос 2: Бывают ли у вас кожные высыпания (акне, экзема), или неприятный запах изо рта, или проблемы с обменом веществ?\n\nA: Часто — моя кожа и тело сильно реагируют на изменения питания.\nB: Иногда — бывают вспышки, но не критично.\nC: Редко или вообще не бывает.",
        'question_3': "Вопрос 3: Как вы оцениваете состояние своей печени? (например, ощущение тяжести, употребление жирной пищи или алкоголя)\n\nA: Плохо — употребляю жирную пищу или алкоголь, есть дискомфорт.\nB: Нормально — злоупотребляю, но особых проблем не чувствую.\nC: Отлично — Моя печень в полном порядке.",
        'question_4': "Вопрос 4: Бывают ли у вас изменения на коже (сухость, зуд, покраснение) или частые синяки без причины?\n\nA: Часто — замечаю значительные изменения на коже.\nB: Иногда — но я не придаю этому значения.\nC: Редко или вообще не бывает.",
        'question_5': "Вопрос 5: Как часто вы испытываете стресс, тревожность или проблемы со сном?\n\nA: Почти постоянно — сложно расслабиться и заснуть.\nB: Иногда — стресс бывает, но я справляюсь.\nC: Редко или вообще не испытываю проблем.",
        'question_6': "Вопрос 6: Какой у вас уровень энергии в течение дня?\n\nA: Часто чувствую усталость и сонливость.\nB: Бывает упадок сил, но это не регулярно.\nC: Энергии хватает на весь день.",
        'result_gut': "🍃 Рекомендуется комплект для ЖКТ.\n\nЗдоровый желудок — это основа хорошего усвоения питательных веществ. Этот комплект улучшит переваривание пищи и устранит проблемы с пищеварением. А с промокодом START вы получите 5% на покупку любого комплекта!🎁 \n\nhttps://doseit.ee/products/healthy-gut-support-supplement-pack-30-day-supply",
        'result_liver': "🍀 Рекомендуется комплект для печени.\n\nВаша печень нуждается в поддержке из-за нагрузки на организм. Комплект для печени поможет вывести токсины, улучшить обмен веществ и уменьшить тяжесть в правом подреберье. А с промокодом START вы получите 5% на покупку любого комплекта!🎁 \n\nhttps://doseit.ee/products/liver-support-supplement-pack-30-day-supply",
        'result_nervous': "🧠 Рекомендуется комплект для нервной системы.\n\nВаша нервная система испытывает стресс и напряжение. Этот комплект улучшит сон, снизит тревожность и обеспечит спокойствие, влияя на работу внутренних органов. А с промокодом START вы получите 5% на покупку любого комплекта!🎁 \n\nhttps://doseit.ee/products/nervous-system-support-supplement-pack-30-day-supply",
        'note_gut': "\n\n🌟 Примечание: ЖКТ имеет приоритет, так как здоровый желудок помогает усваивать питательные вещества.",
        'note_nervous': "\n\n🌟 Примечание: Приоритет был отдан комплекту для нервной системы, так как для начала этот комплект будет вам более полезен, чем поддержка печени. Нервная система управляет работой внутренних органов.",
        'result_healthy': "🎉 Молодцы, у вас не наблюдается серьезных недомоганий! Если же вы принимаете какие-либо пищевые добавки или витамины, то советуем вам пропить курс для ЖКТ, ведь здоровый желудок - путь к усваиванию полезных веществ.А с промокодом START вы получите 5% на покупку любого комплекта!🎁 \n\nhttps://doseit.ee/products/healthy-gut-support-supplement-pack-30-day-supply",
        'restart': "Нажмите на /start, чтобы пройти опрос заново.",
        'cancel': "🛑 Опрос отменён.",
        'question_accepted': "Вопрос № {}/6 принят ✅"  # Локализованное сообщение
    },
    'en': {
        'welcome': "👋 Welcome! This short survey will help you determine which set of DoseIt supplements is best for you to start with. There are formulas for the liver, nervous system and gut support.📝",
        'question_1': "Question 1: How often do you experience digestive problems? (e.g., bloating, heaviness, constipation, diarrhea)\n\nA: Often — almost every day or more than 3 times a week.\nB: Sometimes — depends on food or lifestyle.\nC: Rarely — I almost never have problems.",
        'question_2': "Question 2: Do you have skin rashes (acne, eczema), or bad breath, or metabolic problems?\n\nA: Often — my skin and body react strongly to dietary changes.\nB: Sometimes — there are outbreaks, but not critical.\nC: Rarely or never.",
        'question_3': "Question 3: How do you assess the condition of your liver? (e.g., feeling of heaviness, consumption of fatty foods or alcohol)\n\nA: Bad — I consume fatty foods or alcohol, there is discomfort.\nB: Normal — I overindulge, but I don't feel any particular problems.\nC: Good — My liver is in perfect condition.",
        'question_4': "Question 4: Do you have skin changes (dryness, itching, redness) or frequent bruising for no reason?\n\nA: Often — I notice significant skin changes.\nB: Sometimes — but I don't pay attention to it.\nC: Rarely or never.",
        'question_5': "Question 5: How often do you experience stress, anxiety, or sleep problems?\n\nA: Almost constantly — it's hard to relax and fall asleep.\nB: Sometimes — there is stress, but I cope with it.\nC: Rarely or I don't have any problems.",
        'question_6': "Question 6: What is your energy level throughout the day?\n\nA: I often feel tired and sleepy.\nB: There is a loss of energy, but it is not regular.\nC: I have enough energy for the whole day.",
        'result_gut': "🥦 Recommended Gut Health Pack.\n\nA healthy stomach is the foundation of good nutrient absorption. This pack improves digestion and helps eliminate digestive issues. Plus, use the promo code START to get 5% off any pack purchase! 🎁\n\nhttps://doseit.ee/products/healthy-gut-support-supplement-pack-30-day-supply",
        'result_liver': "🍀 Recommended Liver Support Pack.\n\nYour liver needs support due to the strain on your body. This liver pack helps detoxify, boost metabolism, and relieve heaviness in the right upper abdomen. Plus, use the promo code START to get 5% off any pack purchase! 🎁\n\nhttps://doseit.ee/products/liver-support-supplement-pack-30-day-supply",
        'result_nervous': "🧠 Recommended Nervous System Support Pack.\n\nYour nervous system is under stress and tension. This pack improves sleep, reduces anxiety, and promotes relaxation while supporting the internal organs. Plus, use the promo code START to get 5% off any pack purchase! 🎁\n\nhttps://doseit.ee/products/nervous-system-support-supplement-pack-30-day-supply",
        'note_gut': "\n\n🌟 Note: The gut support formula takes priority, as a healthy stomach helps absorb nutrients.",
        'note_nervous': "\n\n🌟 Note: Perhaps priority can be given to the nervous system support formula, as the nervous system controls the functioning of the internal organs.",
        'result_healthy': "🎉 Well done! No significant health issues detected. However, if you take any supplements or vitamins, we recommend a Gut Health Pack, as a healthy stomach is key to absorbing nutrients. Plus, use the promo code START to get 5% off any pack purchase! 🎁\n\nhttps://doseit.ee/products/healthy-gut-support-supplement-pack-30-day-supply",
        'restart': "Click /start to take the survey again.",
        'cancel': "🛑 Survey canceled.",
        'question_accepted': "Question № {}/6 accepted ✅"  # Локализованное сообщение  
    },
    'et': {
        'welcome': "👋 Tere tulemast! See kiir küsimustik aitab teil kindlaks teha, Milline DoseIt lisakomplekt on teile kõige parem alustamiseks: maksa-, närvi- või seedetrakti toetus.📝",
        'question_1': "Küsimus 1: Kui sageli teil esineb seedehäireid? (nt kõhu puhitus, raskustunne, kõhukinnisus, kõhulahtisus)\n\nA: Sageli — peaaegu iga päev või rohkem kui 3 korda nädalas.\nB: Mõnikord — sõltub toidust või eluviisist.\nC: Harva — mul ei ole peaaegu kunagi probleeme.",
        'question_2': "Küsimus 2: Kas teil on nahalööve (akne, ekseem), või halb hingamine või ainevahetushaigused?\n\nA: Sageli — mu nahk ja keha reageerivad toidu muutustele tugevalt.\nB: Mõnikord — on puhanguid, kuid mitte kriitilisi.\nC: Harva või mitte kunagi.",
        'question_3': "Küsimus 3: Kuidas hindate oma maksa seisundit? (nt raskustunne, rasvase toidu või alkoholi tarbimine)\n\nA: Halb — tarbin rasvast toitu või alkoholi, on ebamugavust.\nB: Normaalne — ületarbin, kuid ei tunne erilisi probleeme.\nC: Väga hea — Mu maks on täiuslikus korras.",
        'question_4': "Küsimus 4: Kas teil on nahamuutused (kuivus, sügelus, punetus) või sageli sinikaid ilma põhjuseta?\n\nA: Sageli — märkan olulisi nahamuutusi.\nB: Mõnikord — kuid ma ei pööra sellele tähelepanu.\nC: Harva või mitte kunagi.",
        'question_5': "Küsimus 5: Kui sageli tunnete stressi, ärevust või unehäireid?\n\nA: Peaaegu pidevalt — on raske lõõgastuda ja magama jääda.\nB: Mõnikord — on stressi, kuid ma saan hakkama.\nC: Harva või mul pole probleeme.",
        'question_6': "Küsimus 6: Mis on teie energiatase päeva jooksul?\n\nA: Tunnetan sageli väsimust ja unisust.\nB: Energiatase langeb, kuid see ei ole regulaarne.\nC: Mul on piisavalt energiat kogu päevaks.",
        'result_gut': "🥦 Soovitatav seedetrakti toidulisandite komplekt.\n\nTerve magu on hea toitainete omastamise alus. See komplekt parandab seedimist ja aitab kõrvaldada seedeprobleeme. Lisaks saate sooduskoodiga START 5% allahindlust iga komplekti ostult! 🎁\n\nhttps://doseit.ee/products/healthy-gut-support-supplement-pack-30-day-supply",
        'result_liver': "🍀 Soovitatav maksatoetuse komplekt.\n\nTeie maks vajab toetust organismi koormuse tõttu. See komplekt aitab eemaldada toksiine, parandada ainevahetust ja vähendada raskustunnet paremal ülakõhus. Lisaks saate sooduskoodiga START 5% allahindlust iga komplekti ostult! 🎁\n\nhttps://doseit.ee/products/liver-support-supplement-pack-30-day-supply",
        'result_nervous': "🧠 Soovitatav närvisüsteemi toetav komplekt.\n\nTeie närvisüsteem on stressis ja pinges. See komplekt parandab und, vähendab ärevust ja aitab lõõgastuda, toetades samal ajal siseorganite tööd. Lisaks saate sooduskoodiga START 5% allahindlust iga komplekti ostult! 🎁\n\nhttps://doseit.ee/products/nervous-system-support-supplement-pack-30-day-supply",
        'note_gut': "\n\n🌟 Märkus: Soolestiku toetuse komplektil on prioriteet, kuna terve kõht aitab toitaineid omastada.",
        'note_nervous': "\n\n🌟 Märkus: Võib-olla saab prioriteediks pidada närvisüsteemi komplekti, kuna see kontrollib siseorganite tööd.",
        'result_healthy': "🎉 Tubli! Teil ei ole märkimisväärseid terviseprobleeme. Kui te siiski tarvitate toidulisandeid või vitamiine, soovitame seedetrakti komplekti, sest terve magu aitab toitaineid paremini omastada. Lisaks saate sooduskoodiga START 5% allahindlust iga komplekti ostult! 🎁\n\nhttps://doseit.ee/products/healthy-gut-support-supplement-pack-30-day-supply",
        'restart': "Klõpsake /start, et uuesti uuringut teha.",
        'cancel': "🛑 Uuring tühistati.",
        'question_accepted': "Küsimus № {}/6 vastu võetud ✅"  # Локализованное сообщение
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_responses.clear()

    keyboard = [
        [InlineKeyboardButton("Русский", callback_data='ru')],
        [InlineKeyboardButton("English", callback_data='en')],
        [InlineKeyboardButton("Eesti", callback_data='et')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💊Please choose your language / Пожалуйста, выберите язык / Palun valige keel:💊", reply_markup=reply_markup)
    return LANGUAGE

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_responses['language'] = query.data  # Сохраняем выбранный язык

    lang = user_responses['language']
    keyboard = [
        [InlineKeyboardButton("A", callback_data='A')],
        [InlineKeyboardButton("B", callback_data='B')],
        [InlineKeyboardButton("C", callback_data='C')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(language_texts[lang]['welcome'])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=language_texts[lang]['question_1'], reply_markup=reply_markup)
    return QUESTION_1  # Переходим к первому вопросу

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question_num, next_question, question_text):
    query = update.callback_query
    await query.answer()
    user_responses[f'q{question_num}'] = query.data

    lang = user_responses['language']
    # Используем локализованное сообщение
    await query.edit_message_text(language_texts[lang]['question_accepted'].format(question_num))
    await asyncio.sleep(1)

    keyboard = [
        [InlineKeyboardButton("A", callback_data='A')],
        [InlineKeyboardButton("B", callback_data='B')],
        [InlineKeyboardButton("C", callback_data='C')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=question_text, reply_markup=reply_markup)
    return next_question

async def handle_question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_responses['language']
    return await handle_question(update, context, 1, QUESTION_2, language_texts[lang]['question_2'])

async def handle_question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_responses['language']
    return await handle_question(update, context, 2, QUESTION_3, language_texts[lang]['question_3'])

async def handle_question_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_responses['language']
    return await handle_question(update, context, 3, QUESTION_4, language_texts[lang]['question_4'])

async def handle_question_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_responses['language']
    return await handle_question(update, context, 4, QUESTION_5, language_texts[lang]['question_5'])

async def handle_question_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_responses['language']
    return await handle_question(update, context, 5, QUESTION_6, language_texts[lang]['question_6'])

async def handle_question_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_responses['q6'] = query.data

    lang = user_responses.get('language', 'ru')  # Безопасное получение языка
    try:
        await query.edit_message_text(language_texts[lang]['question_accepted'].format(6))
    except Exception:
        pass  # Игнорируем ошибку изменения сообщения

    await asyncio.sleep(1)

    # Подсчёт приоритетов для "A" и "B"
    digestive_A = sum(1 for q in ['q1', 'q2'] if user_responses.get(q) == 'A')
    liver_A = sum(1 for q in ['q3', 'q4'] if user_responses.get(q) == 'A')
    nervous_A = sum(1 for q in ['q5', 'q6'] if user_responses.get(q) == 'A')

    digestive_B = sum(1 for q in ['q1', 'q2'] if user_responses.get(q) == 'B')
    liver_B = sum(1 for q in ['q3', 'q4'] if user_responses.get(q) == 'B')
    nervous_B = sum(1 for q in ['q5', 'q6'] if user_responses.get(q) == 'B')

    # ✅ 1. Если все ответы "C" → здоровый результат
    if all(user_responses.get(q) == 'C' for q in ['q1', 'q2', 'q3', 'q4', 'q5', 'q6']):
        result = language_texts[lang]['result_healthy']
    
    else:
        # ✅ 2. Определяем приоритет по "A"
        if digestive_A > max(liver_A, nervous_A):
            result = language_texts[lang]['result_gut']
        elif nervous_A > max(digestive_A, liver_A):
            result = language_texts[lang]['result_nervous']
        elif liver_A > max(digestive_A, nervous_A):
            result = language_texts[lang]['result_liver']
        
        # ✅ 3. Разрешение конфликтов "A"
        elif digestive_A == nervous_A and digestive_A > liver_A:
            result = language_texts[lang]['result_gut'] + "\n\n" + language_texts[lang].get('note_gut', "")
        elif digestive_A == liver_A and digestive_A > nervous_A:
            result = language_texts[lang]['result_gut'] + "\n\n" + language_texts[lang].get('note_gut', "")
        elif nervous_A == liver_A and nervous_A > digestive_A:
            result = language_texts[lang]['result_nervous'] + "\n\n" + language_texts[lang].get('note_nervous', "")
        elif digestive_A == nervous_A == liver_A:
            result = language_texts[lang]['result_gut'] + "\n\n🌟 " + language_texts[lang].get('note_gut', "")

        # ✅ 4. Если "A" нет, но есть "B" → выбираем по "B"
        elif max(digestive_A, liver_A, nervous_A) == 0:
            if liver_B > max(digestive_B, nervous_B):
                result = language_texts[lang]['result_liver'] + "\n\n🌟 " + language_texts[lang].get('note_nervous', "")
            elif nervous_B > max(digestive_B, liver_B):
                result = language_texts[lang]['result_nervous'] + "\n\n🌟 " + language_texts[lang].get('note_nervous', "")
            elif digestive_B > max(liver_B, nervous_B):
                result = language_texts[lang]['result_gut'] + "\n\n🌟 " + language_texts[lang].get('note_gut', "")
            elif digestive_B == nervous_B == liver_B and digestive_B > 0:
                result = language_texts[lang]['result_nervous'] + "\n\n🌟 " + language_texts[lang].get('note_nervous', "")

        # ✅ 5. Разрешение конфликтов "B"
        elif digestive_B == nervous_B and digestive_B > liver_B:
            result = language_texts[lang]['result_nervous'] + "\n\n🌟 " + language_texts[lang].get('note_nervous', "")
        elif digestive_B == liver_B and digestive_B > nervous_B:
            result = language_texts[lang]['result_liver'] + "\n\n🌟 " + language_texts[lang].get('note_nervous', "")
        elif nervous_B == liver_B and nervous_B > digestive_B:
            result = language_texts[lang]['result_nervous'] + "\n\n🌟 " + language_texts[lang].get('note_nervous', "")

        # ✅ 6. Если нет "A" и "B" → ЖКТ по умолчанию
        else:
            result = language_texts[lang]['result_gut'] + "\n\n🌟 " + language_texts[lang].get('note_gut', "")

    # Отправка результата клиенту
    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=language_texts[lang].get('restart', "Click /start to take the survey again."))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_responses.get('language', 'ru')
    await update.message.reply_text(language_texts[lang]['cancel'])
    return ConversationHandler.END

async def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],  # Команда /start запускает опрос
        states={
            LANGUAGE: [CallbackQueryHandler(handle_language)],  # Состояние выбора языка
            QUESTION_1: [CallbackQueryHandler(handle_question_1)],
            QUESTION_2: [CallbackQueryHandler(handle_question_2)],
            QUESTION_3: [CallbackQueryHandler(handle_question_3)],
            QUESTION_4: [CallbackQueryHandler(handle_question_4)],
            QUESTION_5: [CallbackQueryHandler(handle_question_5)],
            QUESTION_6: [CallbackQueryHandler(handle_question_6)],
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('cancel', cancel)]  # /start и /cancel сбрасывают опрос
    )

    application.add_handler(conv_handler)

    # 🔹 Удаляем старый вебхук перед установкой нового
    logger.info("Удаление старого вебхука...")
    await application.bot.delete_webhook()

    # 🔹 Устанавливаем новый вебхук
    logger.info(f"Устанавливаем вебхук: {WEBHOOK_URL}")
    await application.bot.set_webhook(url=WEBHOOK_URL)

    # 🔹 Запускаем сервер вебхука
    await application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
