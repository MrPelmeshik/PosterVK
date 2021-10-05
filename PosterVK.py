import PySimpleGUI as sg

import vk_api
import sys
import random
import os
import csv
import traceback
import getpass
import json

DEBUG = True
THEME = "Dark"
FIELDNAME = ['Название', 'Кол-во участников', 'Ссылка', 'ID группы', 'Ссылка на пост']
PATH = ''
REMEMBERDEVICE = False
FIRST_CHECK_TOKEN = False
AUTHORIZED_USER = False


def ErrorOutput(callPoint='not specified', msgError=''):
    if DEBUG:
        print('\nERROR => callPoint (', callPoint, ') -> ', msgError)
    else:
        # вывод ошибки в лог файл
        pass


def LogOutput(callPoint='not specified', msgLog=''):
    if DEBUG:
        print('\nLOG => callPoint (', callPoint, ') -> ', msgLog)
    else:
        # вывод ошибки в лог файл
        pass


def Auth(login, password):


def DrawAuthorizationWindow():
    layout = [
        [sg.Text('Login (phone number) -> ', size=(25, 1)), sg.Input(key='-LOGIN-')],
        [sg.Text('Password -> ', size=(25, 1)), sg.Input(key='-PASSWORD-', password_char='*')],
        [sg.Checkbox('Remember you -> ', key='-REMEMBERDEVICE-')],
        [sg.Text('Result -> waiting send', key='-RESULT-')],
        [sg.Submit('Log in', key='-AUTHORIZATION-')]
    ]
    result = {
        'vk': '',
        'vk_session': ''
    }

    window = sg.Window('PosterVK - Authorization', layout)
    while True:
        event, values = window.read()

        LogOutput('Authorization', event + ', ' + str(values))

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-AUTHORIZATION-':
            Auth()

            REMEMBERDEVICE = values['-REMEMBERDEVICE-']
            result['vk_session'] = vk_api.VkApi(
                values['-LOGIN-'], values['-PASSWORD-'],
                config_filename=PATH + 'vk_config.v2.json',
                auth_handler=VerificationCode
            )

            try:
                result['vk_session'].auth()
                result['vk'] = result['vk_session'].get_api()
                LogOutput('Authorization/auth and get api', result['vk_session'])
                return result
            except vk_api.AuthError as error_msg:
                window.Element('-RESULT-').update('Result -> error authorization (check you login and password)')
                ErrorOutput('Authorization/trying_authorization', event + ', ' + str(values))


def VerificationCode():
    return DrawingverificationWindow(), REMEMBERDEVICE


def DrawingverificationWindow():
    layout = [
        [sg.Text('Verification code -> ', size=(25, 1)), sg.Input()],
        [sg.Submit(key='-VIRIFICATION-')]
    ]

    window = sg.Window('PosterVK - Verification', layout)
    while True:
        event, values = window.read()

        LogOutput('DrawingverificationWindow', event + ', ' + str(values))

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-VIRIFICATION-':
            return values[0]


def DrawingMainWindow(vk, vk_session):
    layout = [
        [sg.Text('File with urls group (.csv) -> ', size=(25, 1)), sg.Input(key='-FILECSV-'), sg.FileBrowse()],
        [sg.Text('File with message (.txt) -> ', size=(25, 1)), sg.Input(key='-FILETXT-'), sg.FileBrowse()],
        [sg.Text('Folder with photos -> ', size=(25, 1)), sg.Input(key='-FOLDERIMG-'), sg.FileBrowse()],
        [sg.Text('Output')],
        [sg.Output(size=(88, 20), key='-OUTPUT-')],
        [sg.Submit(key='-RUN-')]
    ]

    window = sg.Window('PoaterVK', layout)
    while True:
        event, values = window.read()

        LogOutput('DrawingMainWindow', event + ', ' + str(values))

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-RUN-':
            try:
                RunPosting(vk, vk_session, values['-FILETXT-'], values['-FILECSV-'], values['-FOLDERIMG-'])
            except Exception as exc:
                ErrorOutput('DrawingMainWindow', exc)


def RunPosting(vk, vk_session, nameFileTxt, nameFileCsv, nameFolderImg):
    arrDataGroups = ReadingCsv(vk, nameFileCsv)
    message = ReadingTxt(vk, nameFileTxt)
    LogOutput('RunPosting', 'start posting')
    for group in arrDataGroups:
        ownerId = -1 * group['id']
        group['urlPost'] = Posting(vk, vk_session, ownerId, message, nameFolderImg)
    LogOutput('RunPosting', 'stop posting')
    WritingCsv(nameFileCsv, arrDataGroups)

    try:
        pass
    except Exception as exc:
        ErrorOutput('RunPosting', exc)


def UploadPhoto(vk_session, ownerId, nameFolderImg):
    owner_id = ownerId
    upload = vk_api.VkUpload(vk_session)  # Для загрузки изображений
    files = os.listdir(nameFolderImg)
    files = [i for i in files if i.endswith(('.png', '.jpg', '.jpeg'))]
    photos = files
    for i in range(len(photos)):
        photos[i] = r'{}{}'.format(nameFolderImg, photos[i])
    photo_list = upload.photo_wall(photos)
    attachment = ','.join('photo{owner_id}_{id}'.format(**item) for item in photo_list)

    return attachment


def ReadingTxt(vk, namefile):
    LogOutput('ReadingTxt', 'start reading txt ( ' + namefile + ' )')

    with open(namefile, "r", encoding='utf-8') as f_obj:
        message = f_obj.read()

    LogOutput('ReadingTxt', 'stop reading txt ( ' + namefile + ' )')

    return message


def Posting(vk, vk_session, ownerId, message, nameFolderImg):
    try:
        response_post = vk.wall.post(owner_id=ownerId, attachment=UploadPhoto(vk_session, ownerId, nameFolderImg),
                                     message=message)  # Опубликовать пост
        urlPost = 'https://vk.com/wall{}_{}'.format(ownerId, response_post['post_id'])
        LogOutput('Posting', 'ready ( ' + urlPost + ' )')
    except vk_api.AuthError as error_msg:
        urlPost = 'err'
        LogOutput('Posting', 'error ( ' + error_msg + ' )')

    return urlPost

    # sleep(30) #шобы не забанили, но я хз сколько надо ставить


def GetValidUrl(vk, url):
    response = vk.utils.resolveScreenName(
        screen_name=url)  # научиться забирать тип (пользователь\группа) и проверить что за Id возвращается и можно ли оп этому Id выкладвыать посты

    if response:
        if response['type'] == 'group':
            # все ок, это группа
            pass
        elif response['type'] == 'page':
            # это страница, но вроде при постинге все ок
            url = url.replace('public', '')
            # print(url)
        elif response['type'] == 'user':
            # это чел (надо проверить, можно ли постить)
            pass
        else:
            # все говно, тут постить нельзя
            url = None
    else:
        url = None

    return url


def GetDataGroup(vk, url, originalUrl):
    if url:
        response = vk.groups.getById(group_id=url)
        response[0]['url'] = originalUrl
    else:
        response = [{'name': 'err', 'countUsers': 'err', 'id': 'err', 'url': originalUrl}]
    response[0]['countUsers'] = vk.groups.getMembers(group_id=url)['count']

    return response[0]


def ReadingCsv(vk, namefile):
    LogOutput('ReadingCsv', 'start reading csv ( ' + namefile + ' )')

    arrDataGroups = []
    url = None
    originalUrl = None
    countRow = 0
    with open(namefile, "r", encoding='cp1251') as f_obj:
        reader = csv.reader(f_obj, delimiter=';')
        for row in reader:
            if countRow != 0:
                originalUrl = row[2]
                LogOutput('ReadingCsv', 'new url ( ' + originalUrl + ' ) start verification')
                if row[3] == '':
                    # нет id группы
                    url = GetValidUrl(vk, row[2].split('/')[-1].split('?')[0].split('-')[-1])
                else:
                    url = row[3]
                arrDataGroups.append(GetDataGroup(vk, url, originalUrl))
                LogOutput('ReadingCsv', 'new url ( ' + originalUrl + ' ) successfully verified')
            countRow += 1

    LogOutput('ReadingCsv', 'stop reading csv ( ' + namefile + ' )')

    return arrDataGroups


def WritingCsv(namefile, arrDataGroups):
    LogOutput('WritingCsv', 'start writing csv ( ' + namefile + ' )')

    with open(namefile, mode="w", encoding='cp1251') as w_file:
        writer = csv.writer(w_file,
                            delimiter=';',
                            lineterminator="\r")
        writer.writerow(FIELDNAME)
        for i in arrDataGroups:
            tmp = i['name'], i['countUsers'], i['url'], i['id'], i['urlPost']
            writer.writerow(tmp)

    LogOutput('WritingCsv', 'stop writing csv ( ' + namefile + ' )')


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


def CheckToken(token):
    try:
        result = vk_api.chickToken(token)
    except Exception as exc:
        print(exc)

    return result


if __name__ == '__main__':

    PATH = os.path.dirname(os.path.abspath(__file__))
    sg.theme(THEME)

    # result = ReadingJson('D:\\Digital_SMM\\PosterVK\\vk_config.v2.json')
    # print(result[0], result[1])

    layoutPost = [
        [sg.Text('File with urls group (.csv) -> ', size=(25, 1)), sg.Input(key='-FILECSV-'), sg.FileBrowse()],
        [sg.Text('File with message (.txt) -> ', size=(25, 1)), sg.Input(key='-FILETXT-'), sg.FileBrowse()],
        [sg.Text('Folder with photos -> ', size=(25, 1)), sg.Input(key='-FOLDERIMG-'), sg.FileBrowse()],
        [sg.Text('Output')],
        [sg.Submit(key='-RUN-')]
    ]

    layoutOutput = [
        [sg.Output(size=(88, 20), key='-OUTPUT-')]
    ]

    layoutAuth = [
        [sg.Text('Login (phone number) -> ', size=(25, 1)), sg.Input(key='-LOGIN-')],
        [sg.Text('Password -> ', size=(25, 1)), sg.Input(key='-PASSWORD-', password_char='*')],
        [sg.Checkbox('Remember you -> ', key='-REMEMBERDEVICE-')],
        [sg.Text('Result -> waiting send', key='-RESULT-')],
        [sg.Submit('Log in', key='-AUTHORIZATION-')]
    ]

    layout = [[sg.TabGroup([[
        sg.Tab('Authorization', layoutAuth),
        sg.Tab('Send post', layoutPost),
        sg.Tab('Output', layoutOutput),
    ]],
        tab_location='topleft', enable_events=True, key='tab_group'
    )]]

    # автоматичексая попытка авторизации в ВК
    if (FIRST_CHECK_TOKEN == False):  # если это первый проход
        FIRST_CHECK_TOKEN = True
        resultCheckAuth = ReadingJson()  # читаем Json
        if (CheckToken(resultCheckAuth[1])):  # провряем актульность token
            Auth(resultCheckAuth[0])

    window = sg.Window('PosterVK', layout)
    while True:
        event, values = window.read()

        LogOutput('Main', event + ', ' + str(values))

        if event in (None, 'Exit', 'Cancel'):
            break
        if event == '-AUTHORIZATION-':
            pass
