#!/usr/bin/python

import json
import sys
import codecs
import os

def addToKeys(keyDesc, owner, count = 1):
    location = keyDesc['portalLocation'].split(',')
    latitude = int(location[0], 16)
    if latitude > 360000000 :
        latitude = latitude - int(0xffffffff)
    latitudeE6 = latitude / 1000000.0
    longitude = int(location[1], 16)
    if longitude > 360000000 :
        longitude = longitude - int(0xffffffff)
    longitudeE6 = longitude / 1000000.0
    if keyDesc['portalGuid'] not in keys:
        keys[keyDesc['portalGuid']] = { \
        'Name': keyDesc['portalTitle'].replace('"', ''), \
        'Count': {}, \
#        'Location': '"' + str(latitudeE6) + ',' + str(longitudeE6) + '"', \
        'Latitude': str(latitudeE6) , \
        'Longitude': str(longitudeE6) , \
        'Address': keyDesc['portalAddress'].replace('\n','').replace('"',''), \
        'ImageURL': keyDesc['portalImageUrl']}
    if owner not in keys[keyDesc['portalGuid']]['Count']:
        keys[keyDesc['portalGuid']]['Count'][owner] = 0
    keys[keyDesc['portalGuid']]['Count'][owner] = keys[keyDesc['portalGuid']]['Count'][owner] + count

def addToResources(obj, displayName, resourceClass, keyProperty, count = 1):
    item = obj[resourceClass]
    names[item['resourceType']] = (displayName, resourceClass);
    if item['resourceType'] not in variations:
        variations[item['resourceType']] = set()
    if type(item[keyProperty]) is int:
        item[keyProperty] = 'L' + str(item[keyProperty])
    else:
        item[keyProperty] = item[keyProperty].replace('_', ' ')
        item[keyProperty] = item[keyProperty].title()
    variations[item['resourceType']].add(item[keyProperty])
    if item['resourceType'] not in resources:
        resources[item['resourceType']] = {}
    if item[keyProperty] not in resources[item['resourceType']]:
        resources[item['resourceType']][item[keyProperty]] = 0
    resources[item['resourceType']][item[keyProperty]] = resources[item['resourceType']][item[keyProperty]] + count

def processItem(item, owner, count = 1):
    try:
        displayName = item['displayName']['displayName']
    except KeyError:
        if 'portalCoupler' in item:
            displayName = 'Portal Key'
        elif 'storyItem' in item:
            displayName = 'Media'
        else:
            displayName = 'Unknown Item'
            print(item)
    if 'flipCard' in item:
        item['resource']['resourceType'] = item['resource']['resourceType'] + '_' + item['flipCard']['flipCardType']
    if 'resourceWithLevels' in item:
        addToResources(item, displayName, 'resourceWithLevels', 'level', count)
    if 'modResource' in item:
        addToResources(item, displayName, 'modResource', 'rarity', count)
    if 'resource' in item:
        addToResources(item, displayName, 'resource', 'resourceRarity', count)
    if 'portalCoupler' in item:
        addToKeys(item['portalCoupler'], owner, count)

if len(sys.argv) < 2:
    print 'Please input inventory.json'
    print 'Error & Exit'
    sys.exit()

os.chdir(os.path.split(sys.argv[0])[0])

ret = {}
names = {}
variations = {}
keys = {}
keysjson = {}

for i in range(1, len(sys.argv)):

    owner = os.path.splitext(os.path.basename(sys.argv[i]))[0]
    resources = {}

    with codecs.open(sys.argv[i], 'r', 'utf-8') as data_file:
        data = json.load(data_file)

    data = data['gameBasket']['inventory']

    for item in data:
        processItem(item[2], owner)
        if 'container' in item[2]:
            for content in item[2]['container']['stackableItems']:
                processItem(content['exampleGameEntity'][2], owner, len(content['itemGuids']))

        ret[owner] = dict(resources)

snames = sorted(names, key = lambda p:(names[p][1], p))
ids = sorted(ret)

with codecs.open('inventory.csv', 'w', 'utf8') as of:
    of.write('Item Name,')
    for i in ids:
        of.write(i + ',')
    of.write('Total\n')
    for i in snames:
        variations[i] = sorted(variations[i])
        for j in variations[i]:
            of.write(j + ' ' + names[i][0] + ',')
            total = 0
            for k in ids:
                try:
                    count = ret[k][i][j]
                except KeyError:
                    count = 0
                of.write(str(count) + ',')
                total = total + count
            of.write(str(total) + ',\n')

with codecs.open('keys.csv', 'w', 'utf8') as of:
    of.write('GUID,Name,')
    for i in ids:
        of.write(i + ',')
    of.write('Total,Latitude,Longitude,Address,Image URL\n')
    for i in keys:
        of.write(i + ',"' + keys[i]['Name'] + '",')
        total = 0
        for j in ids:
            try:
                count = keys[i]['Count'][j]
            except KeyError:
                count = 0
            of.write(str(count) + ',')
            total = total + count
        keysjson[i] = count
        of.write(str(total) + ',')
        of.write(keys[i]['Latitude'] +','+ keys[i]['Longitude'] + ',"' + keys[i]['Address'] + '",' + keys[i]['ImageURL'] + '\n')

codecs.open('keys.json', 'w', 'utf8').write(json.dumps(keysjson))
