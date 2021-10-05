# -*- coding: utf8 -*-

import vk_api
import sys
import random
import os
import csv
import traceback
import getpass


NAMEFILE_CSV = 'groups'
NAMEFILE_TXT = 'post_text'
NAMEFOLDER_IMG = 'img'
FIELDNAME = ['Название', 'Кол-во участников', 'Ссылка', 'ID группы', 'Ссылка на пост']
PATH = ''


def AuthCode():

    key = input("Enter authentication code: ")
    remember_device = False # Если: True - сохранить, False - не сохранять.

    return key, remember_device


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

    print('Start -\treading txt ( ' + namefile + ' )')

    with open(namefile, "r", encoding='utf-8') as f_obj:
        message = f_obj.read()

    print('Stop -\treading txt ( ' + namefile + ' )')

    return message


def Posting(vk, vk_session, ownerId, message, nameFolderImg):

    try:
        response_post = vk.wall.post(owner_id = ownerId, attachment = UploadPhoto(vk_session, ownerId, nameFolderImg), message = message) #Опубликовать пост
        urlPost = 'https://vk.com/wall{}_{}'.format(ownerId, response_post['post_id'])   
        print('\tResult -\tready ( ' + urlPost + ' )')
    except vk_api.AuthError as error_msg:
        urlPost = 'err'
        print('\tResult -\terror ( ' + error_msg + ' )',end="")
    
    return urlPost

    # sleep(30) #шобы не забанили, но я хз сколько надо ставить


def GetValidUrl(vk, url):

    response = vk.utils.resolveScreenName(screen_name=url) # научиться забирать тип (пользователь\группа) и проверить что за Id возвращается и можно ли оп этому Id выкладвыать посты

    if response:
        if response['type']=='group':
            # все ок, это группа
            pass
        elif response['type']=='page':
            # это страница, но вроде при постинге все ок
            url = url.replace('public','')
            # print(url)
        elif response['type']=='user':
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
        response = [{'name':'err','countUsers':'err','id':'err', 'url':originalUrl}]
    response[0]['countUsers'] = vk.groups.getMembers(group_id=url)['count']

    return response[0]


def ReadingCsv(vk, namefile):

    print('Start -\treading csv ( ' + namefile + ' )')

    arrDataGroups = []
    url = None
    originalUrl = None
    countRow = 0
    with open(namefile, "r", encoding='cp1251') as f_obj:
        reader = csv.reader(f_obj, delimiter=';')
        for row in reader:
            if countRow != 0:
                originalUrl = row[2]
                print('\tNew -\turl ( ' + originalUrl + ' ) -\t', end="")
                if row[3] == '':
                    # нет id группы
                    url = GetValidUrl(vk, row[2].split('/')[-1].split('?')[0].split('-')[-1])
                else:
                    url = row[3]
                arrDataGroups.append(GetDataGroup(vk, url, originalUrl))
                print('ready')
            countRow += 1

    print('Stop -\treading csv ( ' + namefile + ' )')

    return arrDataGroups


def WritingCsv(namefile, arrDataGroups):

    print('Start -\twriting csv ( ' + namefile + ' )')

    with open(namefile, mode="w", encoding='cp1251') as w_file:
        writer = csv.writer(w_file, 
                                delimiter=';', 
                                lineterminator="\r")
        writer.writerow(FIELDNAME)
        for i in arrDataGroups:
            tmp = i['name'], i['countUsers'], i['url'], i['id'], i['urlPost']
            writer.writerow(tmp)

    print('Stop -\twriting csv ( ' + namefile + ' )')


def Main(nameFileTxt, nameFileCsv, nameFolderImg):

    print('===AUTHORIZATION===')
    login = input("Login: ")
    #password = getpass.getpass('Password: ')
    password = input("Password: ")

    vk_session = vk_api.VkApi(
        login, password,
        auth_handler=AuthCode
    )
    print('======\n')

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    vk = vk_session.get_api()

    arrDataGroups = ReadingCsv(vk, nameFileCsv)
    message = ReadingTxt(vk, nameFileTxt)
    print('Start -\tposting')
    for group in arrDataGroups:
        ownerId = -1 * group['id']
        group['urlPost'] = Posting(vk, vk_session, ownerId, message, nameFolderImg)
    print('Stop -\tposting')
    WritingCsv(nameFileCsv, arrDataGroups)
        

if __name__ == '__main__':

    PATH = os.path.dirname(os.path.abspath(__file__))

    nameFileCsv = PATH + '\\' + NAMEFILE_CSV + '.csv'
    nameFileTxt = PATH + '\\' + NAMEFILE_TXT + '.txt'
    nameFolderImg = PATH + '\\' + NAMEFOLDER_IMG + '\\'

    try:
        Main(nameFileTxt, nameFileCsv, nameFolderImg)
    except Exception as exc:
        print('\nCRASH\t ( ' + exc + ' )')