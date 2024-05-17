import os
from dotenv import load_dotenv
load_dotenv()
import paramiko
import logging
import re
import psycopg2
from psycopg2 import Error

from telegram import Update , ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

TOKEN = os.getenv('TOKEN')
emailList = ''
phonenumbersList = ''
connection = None

logging.basicConfig(
    filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO, encoding="utf-8"
)

logger = logging.getLogger(__name__)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('/get_repl_logs - вывод логов о репликации\n'
                              +'/get_emails - вывод данных из таблиц о email-адресах\n'
                              +'/get_phone_numbers - вывод данных из таблиц о номерах телефона\n'
                              +'/find_email - поиск email в тексте\n'
                              +'/find_phone_number - поиск телефонных номеров в тексте'
                              + '\n/verify_password - определение сложности пароля\n/get_release - информация о релизе'
                              + '\n/get_uname - информация об архитектуры процессора, имени хоста системы и версии ядра'
                              + '\n/get_uptime - информация о времени работы'
                              + '\n/get_df - информация о состоянии файловой системы'
                              + '\n/get_free - информация о состоянии оперативной памяти'
                              + '\n/get_mpstat - информация о производительности системы'
                              + '\n/get_w - информация о работающих в данной системе пользователях'
                              + '\n/get_auths - информация о последних 10 входах в систему'
                              + '\n/get_critical - информация о последних 5 критических события'
                              + '\n/get_ps - информация о запущенных процессах'
                              + '\n/get_ss - информация об используемых портах'
                              + '\n/get_apt_list - информации об установленных пакетах'
                              + '\n/get_services - информации о запущенных сервисах')


def getReplLogsCommand(update: Update, context):
    update.message.reply_text('Для получения информации необходимо подключаться к пользователю с правами root (но не к самому root). В противном случае информация будет недоступна.')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    result = ''
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/pg.log | grep "replication"')
    result = stdout.read() + stderr.read() 
    result = result.decode()
    if result == '' or 'cat: /tmp/pg.log: No such file or directory' in result:
        stdin, stdout, stderr = ssh.exec_command('docker logs db 2>&1 | grep "replication"')
        result = stdout.read() + stderr.read()
        result = result.decode()
    ssh.close()
    for i in range(0, len(result), 4096):
        update.message.reply_text(result[i:i + 4096])
def getEmailsCommand(update: Update, context):
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'), 
            database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute("SELECT email FROM email_and_id;")
        data = cursor.fetchall()
        result = ''
        for i in range(len(data)):
            result += f'{i+1}. {data[i][0]}\n' 
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error(f'Ошибка при работе с PostgreSQL: {error}')
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    update.message.reply_text(result)


def getPhoneNumbersCommand(update: Update, context):
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'), 
            database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute("SELECT phonenumber FROM phonenumber_and_id;")
        data = cursor.fetchall()
        result = ''
        for i in range(len(data)):
            result += f'{i+1}. {data[i][0]}\n' 
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error(f'Ошибка при работе с PostgreSQL: {error}')
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    update.message.reply_text(result)
    

def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email: ')
    
    return 'find_email'


def findEmails (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) email

    emailRegex = re.compile(r'[^\.\t\n ]+@[a-zA-Z]+\.[a-zA-Z]+')

    global emailList
    emailList = emailRegex.findall(user_input) # Ищем email

    if not emailList: # Обрабатываем случай, когда email нет
        update.message.reply_text('Email-ы не найдены')
        return ConversationHandler.END
    
    emails = ''
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' # Записываем очередной email
        
    update.message.reply_text(emails) # Отправляем сообщение пользователю
    update.message.reply_text('Для записи email в базу данных введите "Записать". Введите любой другой текст, для того чтобы пропустить запись.')
    return 'input_email'


def inputEmails(update: Update, context):
    global emailList
    user_input = update.message.text
    if (user_input == "Записать"):
        try:
            connection = psycopg2.connect(user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'), 
                database=os.getenv('DB_DATABASE'))
            cursor = connection.cursor()
            cursor.execute("SELECT email FROM email_and_id;")
            email_rows = len(cursor.fetchall())
            for i in range(len(emailList)):
                email_rows += 1
                cursor.execute(f'INSERT INTO email_and_id VALUES{email_rows, emailList[i]};')
            connection.commit() 
            logging.info("Команда успешно выполнена")
            update.message.reply_text("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error(f'Ошибка при работе с PostgreSQL: {error}')
            update.message.reply_text(f'Ошибка при работе с PostgreSQL: {error}')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
    return ConversationHandler.END


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')
    
    global phonenumbersList
    phonenumbersList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phonenumbersList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phonenumbersList)):
        phoneNumbers += f'{i+1}. {phonenumbersList[i]}\n' # Записываем очередной номер
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    update.message.reply_text('Для записи телефонных номеров в базу данных введите "Записать". Введите любой другой текст, для того чтобы пропустить запись.')
    return 'input_phone_number'


def inputPhoneNumbers (update: Update, context):
    global phonenumbersList
    user_input = update.message.text
    if (user_input == "Записать"):
        try:
            connection = psycopg2.connect(user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'), 
                database=os.getenv('DB_DATABASE'))
            cursor = connection.cursor()
            cursor.execute("SELECT phonenumber FROM phonenumber_and_id;")
            phonenumber_rows = len(cursor.fetchall())
            for i in range(len(phonenumbersList)):
                phonenumber_rows += 1
                cursor.execute(f'INSERT INTO phonenumber_and_id VALUES{phonenumber_rows, phonenumbersList[i]};')
            connection.commit() 
            logging.info("Команда успешно выполнена")
            update.message.reply_text("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error(f'Ошибка при работе с PostgreSQL: {error}')
            update.message.reply_text(f'Ошибка при работе с PostgreSQL: {error}')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
    return ConversationHandler.END


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для определения его сложности: ')

    return 'verify_password'


def verifyPassword (update: Update, context):
    user_input = update.message.text # Получаем пароль
    
    lenFlag = A_ZFlag = a_zFlag = num_Flag = spe_symFlag = 0
    
    spe_sym = "!@#$%^&*()"
    
    if len(user_input) > 7:
        lenFlag = 1

    for i in user_input:
        if i.isalpha():
            if i.isupper():
                A_ZFlag = 1
            else:
                a_zFlag = 1
        elif i.isdigit():
            num_Flag = 1
        elif i in spe_sym:
            spe_symFlag = 1

    if lenFlag * A_ZFlag * a_zFlag * num_Flag * spe_symFlag == 0:
        update.message.reply_text('Пароль простой')
    else:
        update.message.reply_text('Пароль сложный')
   
    return ConversationHandler.END # Завершаем работу обработчика диалога


def getReleaseCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('cat /etc/os-release')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)


def getUnameCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout_arch, stderr = ssh.exec_command('uname -m')
    stdin, stdout_hn, stderr = ssh.exec_command('uname -n')
    stdin, stdout_kr, stderr = ssh.exec_command('uname -r')
    result = 'Архитектура процессора: ' + stdout_arch.read().decode() + 'Имя хоста: ' + stdout_hn.read().decode() + 'Версия ядра: ' + stdout_kr.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getUptimeCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('uptime')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    

def getDfCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('df')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getFreeCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('free')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getMpstatCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('mpstat')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getWCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('w')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getAuthsCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('last -n 10')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getCriticalCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('journalctl -p crit -n 5')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getPsCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('ps')
    result = stdout.read().decode()
    ssh.close
    update.message.reply_text(result)
    
    
def getSsCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('ss')
    result = stdout.read().decode()
    ssh.close
    for i in range(0, len(result), 4096):
        update.message.reply_text(result[i:i + 4096])
    

def getAptListCommand(update: Update, context):
    update.message.reply_text('Для вывода информации о всех установленных пакетах введите "all". Для вывода информации об определённом пакете введите название пакета')
    return 'get_apt_list'


def getAptList (update: Update, context):
    user_input = update.message.text

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    if (user_input == "all"):
        stdin, stdout, stderr = ssh.exec_command('apt list')
    else:
        stdin, stdout, stderr = ssh.exec_command('apt list|grep ' + user_input)
    result = stdout.read().decode()
    ssh.close
    if (len(result) > 4096 * 25):
        for i in range(0, 4096 * 25, 4096):
            update.message.reply_text(result[i:i + 4096])
        update.message.reply_text("и другие")
    else:
        for i in range(0, len(result), 4096):
            update.message.reply_text(result[i:i + 4096])
    return ConversationHandler.END


def getServicesCommand(update: Update, context):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USER'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT'))
    stdin, stdout, stderr = ssh.exec_command('systemctl')
    result = stdout.read().decode()
    ssh.close
    for i in range(0, len(result), 4096):
        update.message.reply_text(result[i:i + 4096])
        
        
def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'input_email': [MessageHandler(Filters.text & ~Filters.command, inputEmails)],
        },
        fallbacks=[]
    )
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'input_phone_number': [MessageHandler(Filters.text & ~Filters.command, inputPhoneNumbers)],
        },
        fallbacks=[]
    )
    convVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
    convGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
        },
        fallbacks=[]
    )

# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLogsCommand))
    dp.add_handler(CommandHandler("get_emails", getEmailsCommand))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhoneNumbersCommand))
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convVerifyPassword)
    dp.add_handler(CommandHandler("get_release", getReleaseCommand))
    dp.add_handler(CommandHandler("get_uname", getUnameCommand))
    dp.add_handler(CommandHandler("get_uptime", getUptimeCommand))
    dp.add_handler(CommandHandler("get_df", getDfCommand))
    dp.add_handler(CommandHandler("get_free", getFreeCommand))
    dp.add_handler(CommandHandler("get_mpstat", getMpstatCommand))
    dp.add_handler(CommandHandler("get_w", getWCommand))
    dp.add_handler(CommandHandler("get_auths", getAuthsCommand))
    dp.add_handler(CommandHandler("get_critical", getCriticalCommand))
    dp.add_handler(CommandHandler("get_ps", getPsCommand))
    dp.add_handler(CommandHandler("get_ss", getSsCommand))
    dp.add_handler(convGetAptList)
    dp.add_handler(CommandHandler("get_services", getServicesCommand))

        # Запускаем бота
    updater.start_polling()

        # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
