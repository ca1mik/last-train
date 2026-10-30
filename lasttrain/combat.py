"""Action pacing, bounded melee attacks and persistent encounter results."""
import math
import pygame as pg

V=pg.Vector2
ENCOUNTERS={'waiting':((650,720),(1110,580)),
            'yard':((1300,750),(700,520)),
            'switchyard':((1000,780),(840,480))}
ENCOUNTER_TYPES={'waiting':('runner','walker'),'yard':('brute','walker'),'switchyard':('runner','brute')}
SPECS={
    'walker':dict(name='Путевой',health=100,speed=175,reach=70,windup=.38,recovery=.9,damage=24),
    'runner':dict(name='Бегун',health=80,speed=210,reach=195,windup=.5,recovery=1.0,damage=24),
    'brute':dict(name='Сцепщик',health=165,speed=115,reach=115,windup=.8,recovery=1.15,damage=32)}
CHARGE_DISTANCE=195
CHARGE_SPEED=780
SWEEP_RADIUS=150
SWEEP_HALF_ANGLE=75
FLAGS={'action_mode','action_started'}|{f'combat_down_{scene}_{i}' for scene,points in ENCOUNTERS.items() for i in range(len(points))}
RADIO={'c_action_start','opening','lida_reminder','relay_nina','relay_tool','relay_fixed','nina_ward',
       'c2_intro','c2_plan','c2_generator','c2_logbook','c2_memorial','c2_cable','c2_winch'}


def moving_dialogue(state):
    from .hospital_action import MOBILE
    return 'action_mode' in state.flags and state.dialogue in RADIO|MOBILE


def cold_open():
    from .model import Session
    from .brakes import BrakeTest
    s=Session()
    s.flags.update(('action_mode','opening','nina_boarded','c1_brake_started','c1_brake_ready',
                    'drive','c1_stop','c1_parked','c1_inspected_step','c1_inspected_gap',
                    'c1_inspected_landing','c1_align','arrive','met_lida'))
    s.brake=BrakeTest.initial(True)
    s.enter('waiting');s.start_dialogue('c_action_start')
    return s


def strike_hits(scene,origin,direction,target,reach=118):
    from .content import SCENES,clear_sight
    delta=V(target)-V(origin)
    return (delta.length()<=reach and (delta.length_squared()<1 or V(direction).dot(delta.normalize())>.3)
            and clear_sight(SCENES[scene],origin,target))


def sweep_hits(origin,direction,target):
    delta=V(target)-V(origin)
    return delta.length()<=SWEEP_RADIUS and (delta.length_squared()<1 or V(direction).dot(delta.normalize())>=math.cos(math.radians(SWEEP_HALF_ANGLE)))


def segment_hits(start,end,target,radius=38):
    start,end,target=V(start),V(end),V(target);delta=end-start
    t=max(0,min(1,(target-start).dot(delta)/delta.length_squared())) if delta.length_squared() else 0
    return target.distance_to(start+delta*t)<=radius


def begin_attack(enemy,target):
    enemy.attack_origin=V(enemy.pos);direction=V(target)-enemy.pos
    enemy.attack_direction=direction.normalize() if direction.length_squared() else V(enemy.facing)
    enemy.facing=V(enemy.attack_direction);enemy.strike=V(target)
    enemy.attack_state='windup';enemy.attack_timer=enemy.spec['windup'];enemy.charge_hit=False
    if enemy.kind=='runner':enemy.strike=enemy.pos+enemy.attack_direction*CHARGE_DISTANCE


def install(dialogues,journal):
    dialogues['c_action_start']={'lines':[
        ('Лида · рация','В аптеке раненый. Дверь справа заклинило — подними жалюзи у дальнего щита.'),
        ('Нина · рация','Я с тобой. Не стой на месте: удар — ЛКМ, рывок — пробел.')], 'effect':'action_started'}
    journal['action_mode']=('Служебная платформа','Поезд остановлен и закреплён. Лида ждёт на платформе. В аптеке раненый, проход заперт. Нина принесла носилки. Пройти зал, открыть жалюзи и вернуться с человеком к поезду.')
