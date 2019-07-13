import os
import sys
import pywikibot
import mwparserfromhell
import requests
import re
from typing import *
from Utility import genDiff
from pywikibot import pagegenerators
from AL_Config_Parser.src.main.ConfigParser import ConfigParser


def preProcess(pageText: str) -> str:
    return re.sub("ShipMain", "Ship", pageText)


def main():
    requests.post('https://azurlane.koumakan.jp/w/api.php?action=purge&titiles=Category:Ships')

    enParser = ConfigParser(
        os.path.expanduser("~/Projects/AL Serializer/Data_Dump/AzurLane_ClientSource/Src/EN/sharecfg/"))
    cnParser = ConfigParser(
        os.path.expanduser("~/Projects/AL Serializer/Data_Dump/AzurLane_ClientSource/Src/CN/sharecfg/"))
    jpParser = ConfigParser(
        os.path.expanduser("~/Projects/AL Serializer/Data_Dump/AzurLane_ClientSource/Src/JP/sharecfg/"))
    krParser = ConfigParser(
        os.path.expanduser("~/Projects/AL Serializer/Data_Dump/AzurLane_ClientSource/Src/KR/sharecfg/"))

    alwiki = pywikibot.Site()
    ships = pywikibot.Category(alwiki, "Ships")
    unreleasedShips = pywikibot.Category(alwiki, "Unreleased ships")

    for ship in pagegenerators.CategorizedPageGenerator(ships):
        parsed = mwparserfromhell.parse(preProcess(ship.text))
        cats = list(ship.categories())
        for template in parsed.filter_templates():
            if template.name.matches("Ship") and unreleasedShips not in cats:
                pageName = ship.title()

                def changeVal(key: str, value: Union[str, int]):
                    """
                    Change the value of a specific key in the template while preserving its original format
                    """
                    if template.has(key):
                        template.get(key).value = " " + str(value) + "\n "
                    else:
                        template.add(key, value)

                idStr = str(template.get("ID").value).strip()
                nationality = str(template.get("Nationality").value).strip()

                if bool(idStr.strip()):
                    if "Plan" in idStr:
                        metaId = int(re.sub("Plan", "", idStr)) + 20000
                    elif "Collab" in idStr:
                        metaId = int(re.sub("Collab", "", idStr)) + 10000
                    else:
                        metaId = int(idStr)
                else:
                    metaIdList = enParser.getMetaIdList()
                    metaId = 0
                    for Id in metaIdList:
                        enMetaShip = enParser.getMetaShip(Id)
                        if enMetaShip.getLocalizedName() == pageName:
                            changeVal("ID", enMetaShip.id)
                            metaId = Id
                            break
                    if metaId == 0:
                        print(
                            "Page {} don't have Id and mokoubot has failed to find one, skipping".format(ship.title()),
                            file=sys.stderr)
                        break

                metaShip = cnParser.getMetaShip(metaId)

                isSubmarine = metaShip.isSubmarine
                hasRefit = metaShip.hasRefit
                changeHullTypeUponRefit = metaShip.changeHullTypeUponRefit

                def changeLocalizedName():
                    if not nationality == "Bilibili":
                        try:
                            KRmetaShip = krParser.getMetaShip(metaId)
                            changeVal("KRName", KRmetaShip.getLocalizedName())
                        except KeyError:
                            print("Ship {} not available on KR server".format(metaId), file=sys.stderr)
                        JPmetaShip = jpParser.getMetaShip(metaId)
                        changeVal("JPName", JPmetaShip.getLocalizedName())
                    if (not bool(template.get("CNName"))) or metaShip.nationality != 3:
                        changeVal("CNName", metaShip.getLocalizedName())

                def changeGeneralStat():
                    statList = ["Health", "Fire", "Torp", "AA", "Air", "Reload", "Armor",
                                "Acc", "Evade", "Speed", "Luck", "ASW"]
                    levelIndependentStatList = ["Armor", "Speed", "Luck"]

                    initialKeyListWithIndex = list(zip([statName + "Initial" for statName in statList], range(1, 13)))
                    maxKeyListWithIndex = list(zip([statName + "Max" for statName in statList], range(1, 13)))
                    maxRefittedKeyListWithIndex = list(zip([statName + "Kai" for statName in statList], range(1, 13)))
                    awakenKeyListWithIndex = list(zip([statName + "120" for statName in statList], range(1, 13)))
                    awakenRefittedKeyListWithIndex = list(
                        zip([statName + "Kai120" for statName in statList], range(1, 13)))

                    changeVal("Speed", metaShip.getStat(10, 1, 0, 0, False, False))
                    changeVal("Luck", metaShip.getStat(11, 1, 0, 0, False, False))

                    def notExcluded(statName: str) -> bool:
                        return all([excludedStat not in statName for excludedStat in levelIndependentStatList])

                    for pair in initialKeyListWithIndex:
                        statName, statId = pair
                        if notExcluded(statName):
                            stat = metaShip.getStat(statId, 1, 0, 0, False, False)
                            changeVal(statName, stat)

                    for pair in maxKeyListWithIndex:
                        statName, statId = pair
                        if notExcluded(statName):
                            stat = metaShip.getStat(statId, 100, 3, 6, False, True)
                            changeVal(statName, stat)

                    for pair in awakenKeyListWithIndex:
                        statName, statId = pair
                        if notExcluded(statName):
                            stat = metaShip.getStat(statId, 120, 3, 6, False, True)
                            changeVal(statName, stat)

                    if hasRefit:
                        if changeHullTypeUponRefit:
                            changeVal("SpeedKai", metaShip.getStat(10, 100, 3, 0, True, False))

                        for pair in maxRefittedKeyListWithIndex:
                            statName, statId = pair
                            if notExcluded(statName):
                                stat = metaShip.getStat(statId, 100, 3, 6, True, True)
                                changeVal(statName, stat)

                        for pair in awakenRefittedKeyListWithIndex:
                            statName, statId = pair
                            if notExcluded(statName):
                                stat = metaShip.getStat(statId, 120, 3, 6, True, True)
                                changeVal(statName, stat)

                def changeSubmarineStat():
                    if isSubmarine:
                        changeVal("AmmoInitial", metaShip.getAmmo())
                        changeVal("AmmoMax", metaShip.getAmmo())
                        changeVal("Ammo120", metaShip.getAmmo())
                        changeVal("OxygenInitial", metaShip.getOxygen(0))
                        changeVal("OxygenMax", metaShip.getOxygen(3))
                        changeVal("Oxygen120", metaShip.getOxygen(3))

                def changeEquipProficiency():
                    def getProficiencyString(slotId: int, lbLevel: int, countRefit: bool) -> str:
                        return str(round(metaShip.getEquipProficiency(slotId, lbLevel, countRefit) * 100)) + "%"

                    for slot in [1, 2, 3]:
                        changeVal("Eq{}EffInit".format(slot), getProficiencyString(slot, 0, False))
                        changeVal("Eq{}EffInitMax".format(slot), getProficiencyString(slot, 3, False))
                        if hasRefit:
                            changeVal("Eq{}EffInitKai".format(slot), getProficiencyString(slot, 3, True) + "\n")

                changeLocalizedName()
                changeGeneralStat()
                changeSubmarineStat()
                changeEquipProficiency()

                if ship.text != str(parsed):
                    print("{} ({}):\n{}".format(pageName, metaShip.groupId, genDiff(ship.text, str(parsed))))
                    ship.text = str(parsed)
                    ship.save("Update ship info via mokoubot")


if __name__ == "__main__":
    main()
