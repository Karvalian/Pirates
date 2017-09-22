from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from pirates.creature.DistributedAnimalAI import DistributedAnimalAI
from pirates.npc.DistributedNPCTownfolkAI import DistributedNPCTownfolkAI
from pirates.npc.DistributedNPCSkeletonAI import DistributedNPCSkeletonAI
from pirates.npc.DistributedNPCNavySailorAI import DistributedNPCNavySailorAI
from pirates.npc.DistributedKillerGhostAI import DistributedKillerGhostAI
from pirates.creature.DistributedCreatureAI import DistributedCreatureAI
from pirates.piratesbase import PiratesGlobals
from pirates.pirate import AvatarTypes
from pirates.leveleditor import NPCList
from pirates.piratesbase import PLocalizer
from pirates.battle import EnemyGlobals
import random

class DistributedEnemySpawnerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedEnemySpawnerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.wantEnemies = config.GetBool('want-enemies', True)
        self.wantDormantSpawns = config.GetBool('want-dormant-spawns', True)
        self.wantTownfolk = config.GetBool('want-townfolk', True)
        self.wantAnimals = config.GetBool('want-animals', True)
        self.wantBosses = config.GetBool('want-bosses', False)

        self.randomBosses = {}
        self._enemies = {}

    def createObject(self, objType, objectData, parent, parentUid, objKey, dynamic):
        newObj = None

        if objType == 'Townsperson':
            if self.wantTownfolk:
                newObj = self.__generateTownsperon(objType, objectData, parent, parentUid, objKey, dynamic)
        elif objType == 'Spawn Node':
            if self.wantEnemies:
                newObj = self.__generateEnemy(objType, objectData, parent, parentUid, objKey, dynamic)
        elif objType == 'Dormant NPC Spawn Node':
            if self.wantEnemies and self.wantDormantSpawns:
                newObj = self.__generateEnemy(objType, objectData, parent, parentUid, objKey, dynamic)
        elif objType == 'Animal':
            if self.wantAnimals:
                newObj = self.__generateAnimal(objType, objectData, parent, parentUid, objKey, dynamic)
        elif objType == 'Creature':
            if self.wantEnemies and self.wantBosses:
                pass
        elif objType == 'Skeleton':
            if self.wantEnemies and self.wantBosses:
                pass
        elif objType == 'NavySailor':
            if self.wantEnemies and self.wantBosses:
                pass
        else:
            self.notify.warning('Received unknown generate: %s' % objType)

        return newObj

    def __generateTownsperon(self, objType, objectData, parent, parentUid, objKey, dynamic):
        townfolk = DistributedNPCTownfolkAI(self.air)

        townfolk.setPos(objectData.get('Pos'))
        townfolk.setHpr(objectData.get('Hpr'))
        townfolk.setSpawnPosHpr(townfolk.getPos(), townfolk.getHpr())
        townfolk.setScale(objectData.get('Scale'))
        townfolk.setUniqueId(objKey)

        animSet = objectData.get('AnimSet', 'default')
        noticeAnim1 = objectData.get('Notice Animation 1', '')
        noticeAnim2 = objectData.get('Notice Animation 2', '')
        greetingAnim = objectData.get('Greeting Animation', '')
        townfolk.setActorAnims(animSet, noticeAnim1, noticeAnim2, greetingAnim)

        townfolk.setIsGhost(int(objectData.get('GhostFX', 0)))
        if 'GhostColor' in objectData and objectData['GhostColor'].isdigit():
            townfolk.setGhostColor(int(objectData.get('GhostColor', 0)))

        townfolk.setLevel(int(objectData.get('Level', 0)))

        townfolk.setAggroRadius(float(objectData.get('Aggro Radius', 0)))

        name = PLocalizer.Unknown
        if objKey in NPCList.NPC_LIST:
            name = NPCList.NPC_LIST[objKey][NPCList.setName]
        townfolk.setName(name)

        if 'Start State' in objectData:
            townfolk.setStartState(objectData['Start State'])

        townfolk.setDNAId(objKey)
        if objectData.get('CustomModel', 'None') != 'None':
            townfolk.setDNAId(objectData.get('CustomModel', ''))

        category = objectData.get('Category', '')
        if not hasattr(AvatarTypes, category):
            self.notify.warning('Failed to spawn Townfolk (%s); Unknown category %s' % (objKey, category))
            return
        townfolk.setAvatarType(getattr(AvatarTypes, category, AvatarTypes.Commoner))

        shopId = objectData.get('ShopID', 'PORT_ROYAL_DEFAULTS')
        if not hasattr(PiratesGlobals, shopId):
            self.notify.warning('Failed to spawn Townfolk (%s); Unknown shopId: %s' % (objKey, shopid))
        townfolk.setShopId(getattr(PiratesGlobals, shopId, 0))

        helpId = objectData.get('HelpID', 'NONE')
        if hasattr(PiratesGlobals, helpId):
            townfolk.setHelpId(getattr(PiratesGlobals, helpId, 0))

        parent.generateChildWithRequired(townfolk, PiratesGlobals.IslandLocalZone)

        locationName = parent.getLocalizerName()
        townfolkName = townfolk.getName()
        self.notify.debug('Generating Townfolk "%s" (%s) under zone %d in %s at %s with doId %d' % (townfolkName, objKey, townfolk.zoneId, locationName, townfolk.getPos(), townfolk.doId))

        return townfolk

    def __generateEnemy(self, objType, objectData, parent, parentUid, objKey, dynamic):
        
        spawnable = objectData.get('Spawnables', '')
        if spawnable not in AvatarTypes.NPC_SPAWNABLES:
            self.notify.warning('Failed to spawn %s (%s); Not a valid spawnable.' % (spawnable, objKey))

        avatarType = random.choice(AvatarTypes.NPC_SPAWNABLES[spawnable])()
        
        enemyCls = None
        if avatarType.isA(AvatarTypes.Undead):
            enemyCls = DistributedNPCSkeletonAI
        elif avatarType.isA(AvatarTypes.TradingCo) or avatarType.isA(AvatarTypes.Navy):
            enemyCls = DistributedNPCNavySailorAI
        elif avatarType.isA(AvatarTypes.LandCreature) or avatarType.isA(AvatarTypes.AirCreature):
            enemyCls = DistributedCreatureAI
        elif avatarType.isA(AvatarTypes.RageGhost):
            enemyCls = DistributedKillerGhostAI
        else:
            self.notify.warning('Received unknown AvatarType: %s' % avatarType)
            return

        if enemyCls is None:
            return

        enemy = enemyCls(self.air)
        enemy.setPos(objectData.get('Pos'))
        enemy.setHpr(objectData.get('Hpr'))
        enemy.setSpawnPosHpr(enemy.getPos(), enemy.getHpr())
        enemy.setScale(objectData.get('Scale'))
        enemy.setUniqueId(objKey)
        enemy.setAvatarType(avatarType)

        animSet = objectData.get('AnimSet', 'default')
        noticeAnim1 = objectData.get('Notice Animation 1', '')
        noticeAnim2 = objectData.get('Notice Animation 2', '')
        greetingAnim = objectData.get('Greeting Animation', '')
        enemy.setActorAnims(animSet, noticeAnim1, noticeAnim2, greetingAnim)

        enemy.setLevel(EnemyGlobals.getRandomEnemyLevel(avatarType))

        enemyHp, enemyMp = EnemyGlobals.getEnemyStats(avatarType, enemy.getLevel())
        enemy.setMaxHp(enemyHp)
        enemy.setHp(enemy.getMaxHp(), True)

        enemy.setMaxMojo(enemyMp)
        enemy.setMojo(enemyMp)

        weapons = EnemyGlobals.getEnemyWeapons(avatarType, enemy.getLevel()).keys()
        enemy.setCurrentWeapon(weapons[0], False)

        enemy.setIsGhost(int(objectData.get('GhostFX', 0)))
        if 'GhostColor' in objectData and objectData['GhostColor'].isdigit():
            enemy.setGhostColor(int(objectData.get('GhostColor', 0)))

        dnaId = None

        if dnaId and hasattr(eneny,'setDNAId'):
            enemy.setDNAId(dnaId)

        name = avatarType.getName()
        if dnaId and dnaId in NPCList.NPC_LIST:
            name = NPCList.NPC_LIST[dnaId][NPCList.setName]
        enemy.setName(name)  

        if 'Start State' in objectData:
            enemy.setStartState(objectData['Start State'])

        self._enemies[objKey] = enemy

        parent.generateChildWithRequired(enemy, PiratesGlobals.IslandLocalZone)

        locationName = parent.getLocalizerName()
        self.notify.debug('Generating %s (%s) under zone %d in %s at %s with doId %d' % (enemy.getName(), objKey, enemy.zoneId, locationName, enemy.getPos(), enemy.doId))

        return enemy

    def __generateAnimal(self, objType, objectData, parent, parentUid, objKey, dynamic):
        species = objectData.get('Species', None)
        if not species:
            self.notify.warning('Failed to generate Animal %s; Species was not defined' % objKey)
            return

        if not hasattr(AvatarTypes, species):
            self.notify.warning('Failed to generate Animal %s; %s is not a valid species' % (objKey, species))
            return
        avatarType = getattr(AvatarTypes, species, AvatarTypes.Chicken)

        animalClass = DistributedAnimalAI
        if species == 'Raven':
            self.notify.warning('Attempted to spawn unsupported Animal: %s' % species)
            return

        animal = animalClass(self.air)

        animal.setPos(objectData.get('Pos'))
        animal.setHpr(objectData.get('Hpr'))
        animal.setSpawnPosHpr(animal.getPos(), animal.getHpr())
        animal.setScale(objectData.get('Scale'))
        animal.setUniqueId(objKey)

        animal.setAvatarType(avatarType)

        parent.generateChildWithRequired(animal, PiratesGlobals.IslandLocalZone)

        locationName = parent.getLocalizerName()
        self.notify.debug('Generating %s (%s) under zone %d in %s at %s with doId %d' % (species, objKey, animal.zoneId, locationName, animal.getPos(), animal.doId))

        return animal
