import telebot
import urllib
import liveqr
import os
token = '5384847315:AAHgJgpQpeUrCwAIo_c2Wh_j00XVGlJpSos'
bot = telebot.TeleBot(token)
@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, 'Отправьте изображение для получения ссылок из QR-кодов')
def save_image_from_message(message):
    image_id = message.photo[len(message.photo)-1].file_id
    file_path = bot.get_file(image_id).file_path
    image_url = "https://api.telegram.org/file/bot"+token+"/"+file_path
    image_name = "pic.jpg"
    urllib.request.urlretrieve(image_url, image_name)
    return image_name
@bot.message_handler(content_types=["text"])
def text(message):
    bot.send_message(message.chat.id, 'Отправьте изображение для получения ссылок из QR-кодов')
@bot.message_handler(content_types=["photo"])
def picture(message):
    bot.send_message(message.chat.id, 'Распознавание запущено, пожалуйста подождите...')
    picture = save_image_from_message(message)
    res = liveqr.make_picture(picture)
    if res[0] == -1 and res[1][0] == "No codes found":
        bot.send_message(message.chat.id, 'Не удалось распознать QR-коды')
    else:
        for i in range(1,res[0]+1):
            if os.path.exists('qr'+str(i)+'.jpg'):
                bot.send_photo(message.chat.id, open('qr'+str(i)+'.jpg', 'rb'))
                os.remove('qr'+str(i)+'.jpg')
                if not i in res[1]:
                    bot.send_message(message.chat.id, 'QR-код №'+str(i)+":\nНе удалось распознать текст")
                else:
                    bot.send_message(message.chat.id, 'QR-код №'+str(i)+":\n"+res[1][i][0])
bot.polling(none_stop=True, interval=0)