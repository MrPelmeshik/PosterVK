import sys
import random
import csv
import json
import os
import PySimpleGUI as sg
import vk_api

DEBUG = True
THEME = "Dark"
FIELDNAME = ['Название', 'Кол-во участников', 'Ссылка', 'ID группы', 'Ссылка на пост']
PATH = ''
REMEMBERDEVICE = False
FIRST_CHECK_TOKEN = True
AUTHORIZED_USER = False


def ErrorOutput(callPoint='not specified', msgError=''):
    if DEBUG:
        print('\n===ERR===>\tcallPoint (', callPoint, ') -> ', msgError)
    else:
        # вывод ошибки в лог файл
        pass

def LogOutput(callPoint='not specified', msgLog=''):
    if DEBUG:
        print('\n===LOG===>\tcallPoint (', callPoint, ') -> ', msgLog)
    else:
        # вывод ошибки в лог файл
        pass

def DrawErrorWindow(msgError=''):

    LAYOUT_ERROR = [
        [sg.Text('ERROR ->')],
        [sg.Text(msgError, key='-TEXTERROR-')],
        [sg.Submit('Ok', key='-OKERROR-')]
    ]

    window = sg.Window('PosterVk - Error', LAYOUT_ERROR)
    while True:
        event, values = window.read()

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-OKERROR-':
            break

    window.close()

def DrawInfoWindow(msgInfo=''):

    LAYOUT_INFO = [
        [sg.Text('INFO ->')],
        [sg.Text(msgInfo, key='-TEXTEINFO-')],
        [sg.Submit('Ok', key='-OKINFO-')]
    ]

    window = sg.Window('PosterVk - Info', LAYOUT_INFO)
    while True:
        event, values = window.read()

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-OKINFO-':
            break

    window.close()

def Auth(login, password, rememberDevice = REMEMBERDEVICE):

    LogOutput('Auth', 'login -> ' + login + ' password -> ' + password)

    vk_session = vk_api.VkApi(
        login, password,
        config_filename = PATH + '\\vk_config.v2.json',
        auth_handler = VerificationCode
    )

    try:
        vk_session.auth()
        vk = vk_session.get_api()
        LogOutput('Auth', vk_session)
        return vk, vk_session
    except vk_api.AuthError as error_msg:
        DrawErrorWindow("Error authorization (check you login and password)")
        ErrorOutput('Auth', 'Error authorization (check you login and password)"')
        return

def AuthToken(login, token, rememberDevice = REMEMBERDEVICE):

    vk_session = vk_api.VkApi(
        login = login,
        token = token,
        config_filename = PATH + 'vk_config.v2.json'
    )

    try:
        vk_session.auth()
        vk = vk_session.get_api()
        LogOutput('AuthToken', 'ok!')
        return vk, vk_session
    except vk_api.AuthError as error_msg:
        ErrorOutput('AuthToken', error_msg)
        return

def DrawAuthorizationWindow():

    global FIRST_CHECK_TOKEN
    global REMEMBERDEVICE

    # автоматичексая попытка авторизации в ВК
    LogOutput('Auto authorization', 'start')
    if FIRST_CHECK_TOKEN:
        try:
            resultCheckAuth = ReadingJson(PATH + '\\vk_config.v2.json')  # читаем Json
        except Exception as exc:
            resultCheckAuth = None
        if resultCheckAuth:
            result = AuthToken(
                login=resultCheckAuth[0],
                token=resultCheckAuth[1],
                rememberDevice=False
            )
            LogOutput('Auto authorization', 'login -> ' + resultCheckAuth[0] + ' token -> ' + resultCheckAuth[1])
            login = resultCheckAuth[0]
            FIRST_CHECK_TOKEN = False
        else:
            login = None
    else:
        login = None

    LogOutput('Auto authorization', 'stop')

    LAYOUT_AUTH = [
        [sg.Text('Login (phone number) -> ', size=(25, 1)), sg.Input(login, key='-LOGIN-')],
        [sg.Text('Password -> ', size=(25, 1)), sg.Input(key='-PASSWORD-', password_char='*')],
        [sg.Text('Remember me (NOT SAFE) -> '), sg.Checkbox('', key='-REMEMBERDEVICE-')],
        [sg.Submit('Log in', key='-AUTHORIZATION-')]
    ]

    window = sg.Window('PosterVK - Authorization', LAYOUT_AUTH)
    while True:
        event, values = window.read()

        LogOutput('Authorization', event + ', ' + str(values))

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-AUTHORIZATION-':
            LogOutput('Authorization/Btn', 'click btn')
            REMEMBERDEVICE = values['-REMEMBERDEVICE-']
            result = Auth(
                login = values['-LOGIN-'],
                password = values['-PASSWORD-'],
                rememberDevice = REMEMBERDEVICE
            )

            if(result):
                LogOutput('Authorization/Btn/Res', 'result is not null')
                break # успешная авторизация

    window.close()
    if(result):
        return result # успешная авторизация
    else:
        return None

def VerificationCode():
    return DrawVerificationCodeWindow(), REMEMBERDEVICE

def DrawVerificationCodeWindow():
    LAYOUT_VERIFICATION = [
        [sg.Text('Verification code -> ', size=(25, 1)), sg.Input()],
        [sg.Submit(key='-VIRIFICATION-')]
    ]

    window = sg.Window('PosterVK - Verification', LAYOUT_VERIFICATION)
    while True:
        event, values = window.read()

        LogOutput('DrawVerificationCodeWindow', event + ', ' + str(values))

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-VIRIFICATION-':
            break

    window.close()
    if values[0]:
        return values[0]
    else:
        return None

def ReadingJson(namefile):
    LogOutput('ReadingJson', 'start reading json ( ' + namefile + ' )')

    with open(namefile) as f:
        d = json.load(f)

    try:
        lastLogin = list(d.keys())[0]
        app = list(d[lastLogin]['token'].keys())[0]
        scope = list(d[lastLogin]['token'][app].keys())[0]
        accessToken = d[lastLogin]['token'][app][scope]['access_token']
    except Exception as exc:
        ErrorOutput('ReadingJson', exc)
        return

    LogOutput('ReadingJson', 'stop reading json ( ' + namefile + ' )')

    return lastLogin, accessToken

def DeletingJson(namefile):
    LogOutput('DeletingJson', 'start deleting json ( ' + namefile + ' )')

    try:
        os.remove(namefile)
        LogOutput('DeletingJson', 'ready')
    except Exception as exc:
        ErrorOutput('DeletingJson', exc)

    LogOutput('DeletingJson', 'stop deleting json ( ' + namefile + ' )')


if __name__ == '__main__':

    PATH = os.path.dirname(os.path.abspath(__file__))
    sg.theme(THEME)

    while True:
        LogOutput('Main', 'start')
        if not AUTHORIZED_USER:
            LogOutput('Main/Auth', 'start')
            try:
                result = DrawAuthorizationWindow()
                AUTHORIZED_USER = True
                LogOutput('Main/Auth', 'find auth')
            except Exception as exc:
                ErrorOutput('Main/Auth', exc)
                break

            LogOutput('Main/Auth', 'AUTHORIZED_USER -> ' + str(AUTHORIZED_USER))

            vk = result[0]
            vk_session = result[1]
        else:
            LogOutput('Main/Poster', 'start')

            LAYOUT_POST = [
                [sg.Text('File with urls group (.csv): ', size=(25, 1)), sg.Input(key='-FILECSV-'), sg.FileBrowse()],
                [sg.Text('File with message (.txt): ', size=(25, 1)), sg.Input(key='-FILETXT-'), sg.FileBrowse()],
                [sg.Text('Folder with photos: ', size=(25, 1)), sg.Input(key='-FOLDERIMG-'), sg.FolderBrowse()],
                [sg.Text('Output')],
                [sg.Submit('Run', key='-RUN-')]
            ]

            LAYOUT_OUTPUT = [
                [sg.Multiline(size=(100,25), key='-OUTPUT-')],
                [sg.Text('Progress:'), sg.ProgressBar(1000000, size=(25,20), orientation='h', key='-PROFRESSBAR-')]
            ]

            LAYOUT_MAIN = [
                [[sg.Frame('Setting', LAYOUT_POST), sg.Frame('Output', LAYOUT_OUTPUT)]],
                [sg.Submit('Logout', key='-LOGOUT-')]
            ]

            window = sg.Window('PosterVK', LAYOUT_MAIN)
            while True:
                event, values = window.read()

                LogOutput('Main/Poster', event + ', ' + str(values))

                if event in (None, 'Exit', 'Cancel'):
                    break
                if event == '-RUN-':
                    LogOutput('Main/Poster', 'RUN')
                    pass
                if event == '-LOGOUT-':
                    AUTHORIZED_USER = False
                    FIRST_CHECK_TOKEN = True
                    result = None
                    vk = None
                    vk_session = None
                    DeletingJson(PATH + '\\vk_config.v2.json')
                    DrawInfoWindow('Logout', 'Attention: logout does not delete your active session. In order to completely revoke your authorization, delete the active session in your VK account settings!')
                    LogOutput('Main/Logout', 'logout')
                    break

            window.close()

            LogOutput('Main/Poster', 'stop')
        LogOutput('Main', 'stop')



# def DrawingMainWindow(vk, vk_session):
#     layout = [
#         [sg.Text('File with urls group (.csv) -> ', size=(25, 1)), sg.Input(key='-FILECSV-'), sg.FileBrowse()],
#         [sg.Text('File with message (.txt) -> ', size=(25, 1)), sg.Input(key='-FILETXT-'), sg.FileBrowse()],
#         [sg.Text('Folder with photos -> ', size=(25, 1)), sg.Input(key='-FOLDERIMG-'), sg.FileBrowse()],
#         [sg.Text('Output')],
#         [sg.Output(size=(88, 20), key='-OUTPUT-')],
#         [sg.Submit(key='-RUN-')]
#     ]
#
#     window = sg.Window('PoaterVK', layout)
#     while True:
#         event, values = window.read()
#
#         LogOutput('DrawingMainWindow', event + ', ' + str(values))
#
#         if event in (None, 'Exit', 'Cancel'):
#             break
#         if event == '-RUN-':
#             try:
#                 RunPosting(vk, vk_session, values['-FILETXT-'], values['-FILECSV-'], values['-FOLDERIMG-'])
#             except Exception as exc:
#                 ErrorOutput('DrawingMainWindow', exc)
#
# def RunPosting(vk, vk_session, nameFileTxt, nameFileCsv, nameFolderImg):
#     arrDataGroups = ReadingCsv(vk, nameFileCsv)
#     message = ReadingTxt(vk, nameFileTxt)
#     LogOutput('RunPosting', 'start posting')
#     for group in arrDataGroups:
#         ownerId = -1 * group['id']
#         group['urlPost'] = Posting(vk, vk_session, ownerId, message, nameFolderImg)
#     LogOutput('RunPosting', 'stop posting')
#     WritingCsv(nameFileCsv, arrDataGroups)
#
#     try:
#         pass
#     except Exception as exc:
#         ErrorOutput('RunPosting', exc)
#
# def UploadPhoto(vk_session, ownerId, nameFolderImg):
#     owner_id = ownerId
#     upload = vk_api.VkUpload(vk_session)  # Для загрузки изображений
#     files = os.listdir(nameFolderImg)
#     files = [i for i in files if i.endswith(('.png', '.jpg', '.jpeg'))]
#     photos = files
#     for i in range(len(photos)):
#         photos[i] = r'{}{}'.format(nameFolderImg, photos[i])
#     photo_list = upload.photo_wall(photos)
#     attachment = ','.join('photo{owner_id}_{id}'.format(**item) for item in photo_list)
#
#     return attachment
#
# def ReadingTxt(vk, namefile):
#     LogOutput('ReadingTxt', 'start reading txt ( ' + namefile + ' )')
#
#     with open(namefile, "r", encoding='utf-8') as f_obj:
#         message = f_obj.read()
#
#     LogOutput('ReadingTxt', 'stop reading txt ( ' + namefile + ' )')
#
#     return message
#
# def Posting(vk, vk_session, ownerId, message, nameFolderImg):
#     try:
#         response_post = vk.wall.post(owner_id=ownerId, attachment=UploadPhoto(vk_session, ownerId, nameFolderImg),
#                                      message=message)  # Опубликовать пост
#         urlPost = 'https://vk.com/wall{}_{}'.format(ownerId, response_post['post_id'])
#         LogOutput('Posting', 'ready ( ' + urlPost + ' )')
#     except vk_api.AuthError as error_msg:
#         urlPost = 'err'
#         LogOutput('Posting', 'error ( ' + error_msg + ' )')
#
#     return urlPost
#
#     # sleep(30) #шобы не забанили, но я хз сколько надо ставить
#
# def GetValidUrl(vk, url):
#     response = vk.utils.resolveScreenName(
#         screen_name=url)  # научиться забирать тип (пользователь\группа) и проверить что за Id возвращается и можно ли оп этому Id выкладвыать посты
#
#     if response:
#         if response['type'] == 'group':
#             # все ок, это группа
#             pass
#         elif response['type'] == 'page':
#             # это страница, но вроде при постинге все ок
#             url = url.replace('public', '')
#             # print(url)
#         elif response['type'] == 'user':
#             # это чел (надо проверить, можно ли постить)
#             pass
#         else:
#             # все говно, тут постить нельзя
#             url = None
#     else:
#         url = None
#
#     return url
#
# def GetDataGroup(vk, url, originalUrl):
#     if url:
#         response = vk.groups.getById(group_id=url)
#         response[0]['url'] = originalUrl
#     else:
#         response = [{'name': 'err', 'countUsers': 'err', 'id': 'err', 'url': originalUrl}]
#     response[0]['countUsers'] = vk.groups.getMembers(group_id=url)['count']
#
#     return response[0]
#
# def ReadingCsv(vk, namefile):
#     LogOutput('ReadingCsv', 'start reading csv ( ' + namefile + ' )')
#
#     arrDataGroups = []
#     url = None
#     originalUrl = None
#     countRow = 0
#     with open(namefile, "r", encoding='cp1251') as f_obj:
#         reader = csv.reader(f_obj, delimiter=';')
#         for row in reader:
#             if countRow != 0:
#                 originalUrl = row[2]
#                 LogOutput('ReadingCsv', 'new url ( ' + originalUrl + ' ) start verification')
#                 if row[3] == '':
#                     # нет id группы
#                     url = GetValidUrl(vk, row[2].split('/')[-1].split('?')[0].split('-')[-1])
#                 else:
#                     url = row[3]
#                 arrDataGroups.append(GetDataGroup(vk, url, originalUrl))
#                 LogOutput('ReadingCsv', 'new url ( ' + originalUrl + ' ) successfully verified')
#             countRow += 1
#
#     LogOutput('ReadingCsv', 'stop reading csv ( ' + namefile + ' )')
#
#     return arrDataGroups
#
# def WritingCsv(namefile, arrDataGroups):
#     LogOutput('WritingCsv', 'start writing csv ( ' + namefile + ' )')
#
#     with open(namefile, mode="w", encoding='cp1251') as w_file:
#         writer = csv.writer(w_file,
#                             delimiter=';',
#                             lineterminator="\r")
#         writer.writerow(FIELDNAME)
#         for i in arrDataGroups:
#             tmp = i['name'], i['countUsers'], i['url'], i['id'], i['urlPost']
#             writer.writerow(tmp)
#
#     LogOutput('WritingCsv', 'stop writing csv ( ' + namefile + ' )')
