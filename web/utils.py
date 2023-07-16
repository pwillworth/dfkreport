#!/usr/bin/env python3
import math

def translateHeroId(heroIdString):
    if '-' in heroIdString:
        parts = heroIdString.split('-')
        if parts[0] == 'CV':
            realmAdd = 1000000000000
        elif parts[0] == 'SD':
            realmAdd = 2000000000000
        else:
            realmAdd = 0
        if parts[1].isnumeric():
            return int(parts[1]) + realmAdd
        else:
            return heroIdString
    else:
        if heroIdString.isnumeric():
            return int(heroIdString)
        else:
            return heroIdString

def timeDescription(seconds):
	appendStr = ''
	if seconds != 0:
		if seconds < 0:
			appendStr = ' ago'
			seconds = seconds * -1
		tmpDays = math.floor(seconds / 86400)
		tmpStr = ''
		if (tmpDays > 0):
			if (tmpDays > 365):
				tmpStr = str(math.floor(tmpDays / 365)) + " years, "
				tmpDays = tmpDays % 365
			tmpStr = tmpStr + str(tmpDays)+" days"
		elif (seconds / 3600 >= 1):
			tmpStr = str(math.floor(seconds/3600))+" hours"
		elif (seconds / 60 >= 1):
			tmpStr = str(math.floor(seconds/60))+" minutes"
		else:
			tmpStr = "less than a minute"
		return tmpStr + appendStr
	else:
		return "no time"