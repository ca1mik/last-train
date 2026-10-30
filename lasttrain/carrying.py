"""Shared projection of the selected stretcher's authored handle positions."""
import pygame as pg
V=pg.Vector2
ELEVATION=54
STRETCHER_WIDTH=130
CARRIER_SPACING=120
# Normalized positions in the alpha-cropped selected Mikhail raster.
HANDLES=((.056,.057),(.013,.532),(.989,.416),(.987,.950))
# The painted bed's long axis already slopes by eight degrees. Cancel that
# authored perspective before orienting it to the carriers' floor direction.
SOURCE_AXIS_DEGREES=8


def stretcher_transform(rotation):
    if rotation>90:return True,rotation-180-SOURCE_AXIS_DEGREES
    if rotation<-90:return True,rotation+180-SOURCE_AXIS_DEGREES
    return False,rotation+SOURCE_AXIS_DEGREES


def grip_pairs(center,size,scale,rotation=0):
    flip,angle=stretcher_transform(rotation)
    points=[]
    for x,y in HANDLES:
        if flip:x=1-x
        local=V((x-.5)*size[0],(y-.5)*size[1])
        points.append(V(center)+V(0,-ELEVATION*scale)+local.rotate(-angle))
    return (tuple(points[:2]),tuple(points[2:]))


def carrier_grips(center,size,scale,rotation,front,rear):
    a,b=grip_pairs(center,size,scale,rotation)
    # Choose ends by actual projected distance, including horizontal mirroring.
    midpoint=lambda pair:(pair[0]+pair[1])*.5
    cost=lambda left,right:midpoint(left).distance_squared_to(front)+midpoint(right).distance_squared_to(rear)
    if cost(a,b)>cost(b,a):a,b=b,a
    return a,b


def rigid_rear(origin,trail,distance):
    """First point on the recorded floor path a full stretcher length away."""
    origin=V(origin)
    for a,b in zip(trail,trail[1:]):
        a,b=V(a),V(b)
        if b.distance_squared_to(origin)<distance*distance:continue
        delta=b-a;offset=a-origin
        if not delta.length_squared():continue
        q=offset.dot(delta)
        disc=q*q-delta.length_squared()*(offset.length_squared()-distance*distance)
        t=(-q+max(0,disc)**.5)/delta.length_squared()
        if 0<=t<=1:return a+delta*t
    # Reversing toward the old trail must not shorten a rigid stretcher.
    for point in reversed(trail):
        direction=V(point)-origin
        if direction.length_squared()>1e-6:return origin+direction.normalize()*distance
    return origin-V(distance,0)


def team_walkable(scene,front,rear,radius=22):
    from .content import walkable
    front,rear=V(front),V(rear)
    steps=max(1,round(front.distance_to(rear)/18))
    return all(walkable(scene,front.lerp(rear,i/steps),radius) for i in range(steps+1))


def follow_rear(front,previous_rear,distance):
    front=V(front);direction=V(previous_rear)-front
    return front+direction.normalize()*distance if direction.length_squared()>1e-6 else front-V(distance,0)
