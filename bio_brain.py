#!/usr/bin/env python3
"""
🧠 BIOLOGICAL BRAIN CREATURE v5
Szybka mysz, wolni wrogowie, biologicznie wierna sieć.
"""

import numpy as np
import pygame
import sys
import math
import random
from collections import deque


# ═══════════════════════════════════════════════════════
#  NEURON — Izhikevich
# ═══════════════════════════════════════════════════════

class Neuron:
    TYPES = {
        'RS':  (0.02,  0.2,  -65.0,  8.0),
        'FS':  (0.1,   0.2,  -65.0,  2.0),
        'IB':  (0.02,  0.2,  -55.0,  4.0),
        'CH':  (0.02,  0.2,  -50.0,  2.0),
        'LTS': (0.02,  0.25, -65.0,  2.0),
    }

    def __init__(self, nid, ntype='RS', excitatory=True, label=''):
        self.id = nid
        self.label = label
        self.is_exc = excitatory
        a, b, c, d = self.TYPES[ntype]
        self.a, self.b, self.c, self.d = a, b, c, d
        self.v = c + random.uniform(-5, 5)
        self.u = b * self.v
        self.I_ext = 0.0
        self.I_syn = 0.0
        self.fired = False
        self.trace = 0.0
        self.spikes = 0
        self.syn_decay = 0.85 if excitatory else 0.90
        self.vx, self.vy = 0.0, 0.0

    def step(self):
        self.fired = False
        I = self.I_ext + self.I_syn
        for _ in range(2):
            if self.v >= 30.0:
                break
            dv = 0.04 * self.v * self.v + 5.0 * self.v + 140.0 - self.u + I
            self.v += dv * 0.5
            du = self.a * (self.b * self.v - self.u)
            self.u += du * 0.5
        if self.v >= 30.0:
            self.v = self.c
            self.u += self.d
            self.fired = True
            self.trace = 1.0
            self.spikes += 1
        self.v = max(-100.0, min(30.0, self.v))
        self.I_syn *= self.syn_decay
        self.trace *= 0.93
        self.I_ext = 0.0
        return self.fired


class Synapse:
    __slots__ = ['pre', 'post', 'w', 'exc', 'elig']
    def __init__(self, pre, post, w, exc=True):
        self.pre = pre
        self.post = post
        self.w = abs(w)
        self.exc = exc
        self.elig = 0.0


# ═══════════════════════════════════════════════════════
#  BRAIN
# ═══════════════════════════════════════════════════════

class Brain:
    def __init__(self):
        self.neurons = []
        self.synapses = []
        self.ids = {}
        self.outgoing = {}
        self.step_num = 0
        self.dopamine = 0.0
        self.serotonin = 0.0
        self.ltp_total = 0
        self.ltd_total = 0
        self._build()
        self._index()
        self._test()

    def _n(self, label, ntype='RS', exc=True):
        nid = len(self.neurons)
        self.neurons.append(Neuron(nid, ntype, exc, label))
        self.ids[label] = nid
        return nid

    def _s(self, pre, post, w, exc=True):
        self.synapses.append(Synapse(self.ids[pre], self.ids[post], w, exc))

    def _index(self):
        self.outgoing = {n.id: [] for n in self.neurons}
        for i, s in enumerate(self.synapses):
            self.outgoing[s.pre].append(i)

    def _build(self):
        # ── SENSORY (13) ──
        for s in ['food_front', 'food_left', 'food_right', 'food_near']:
            self._n(s)
        for s in ['dang_front', 'dang_left', 'dang_right', 'dang_near']:
            self._n(s)
        for s in ['wall_front', 'wall_left', 'wall_right']:
            self._n(s)
        self._n('hunger')
        self._n('pain', 'IB')

        # ── INTER (11) ──
        self._n('approach')
        self._n('avoid')
        self._n('explore', 'CH')
        self._n('go_fwd')
        self._n('turn_l')
        self._n('turn_r')
        self._n('mem1')
        self._n('mem2')
        self._n('inh_l', 'FS', exc=False)
        self._n('inh_r', 'FS', exc=False)
        self._n('inh_fwd', 'FS', exc=False)

        # ── MOTOR (3) ──
        self._n('mot_fwd')
        self._n('mot_tl')
        self._n('mot_tr')

        # ── MODULATORY (2) ──
        self._n('DA', 'IB')
        self._n('5HT', 'IB')

        # ── WIRING ──
        R = 14.0   # Reflex
        S = 10.0   # Strong
        M = 6.0    # Medium
        W = 3.0    # Weak
        I = 8.0    # Inhibitory

        # Jedzenie → jedź / skręć w stronę
        self._s('food_front', 'mot_fwd', R)
        self._s('food_front', 'go_fwd', S)
        self._s('food_left',  'mot_tl',  R)
        self._s('food_left',  'turn_l',  S)
        self._s('food_right', 'mot_tr',  R)
        self._s('food_right', 'turn_r',  S)
        self._s('food_near',  'mot_fwd', R)
        self._s('food_near',  'DA',      S)

        # Podejście
        self._s('food_front', 'approach', M)
        self._s('food_left',  'approach', M)
        self._s('food_right', 'approach', M)
        self._s('food_near',  'approach', S)
        self._s('approach',   'go_fwd',  M)
        self._s('go_fwd',     'mot_fwd', S)
        self._s('turn_l',     'mot_tl',  S)
        self._s('turn_r',     'mot_tr',  S)

        # Zagrożenie → ucieczka
        self._s('dang_front', 'mot_tl',  S)
        self._s('dang_front', 'mot_tr',  S)
        self._s('dang_front', 'inh_fwd', S)
        self._s('dang_left',  'mot_tr',  R)
        self._s('dang_left',  'mot_fwd', M)
        self._s('dang_left',  'mot_tl',  I, exc=False)
        self._s('dang_right', 'mot_tl',  R)
        self._s('dang_right', 'mot_fwd', M)
        self._s('dang_right', 'mot_tr',  I, exc=False)
        self._s('dang_near',  'avoid',   S)
        self._s('dang_near',  'mot_fwd', S)
        self._s('dang_near',  '5HT',    S)
        self._s('avoid',      'mot_fwd', M)
        self._s('pain',       'avoid',   S)
        self._s('pain',       '5HT',    S)

        # Ściany
        self._s('wall_front', 'inh_fwd',  S)
        self._s('wall_front', 'mot_tl',   M)
        self._s('wall_left',  'mot_tr',   M)
        self._s('wall_left',  'mot_tl',   M, exc=False)
        self._s('wall_right', 'mot_tl',   M)
        self._s('wall_right', 'mot_tr',   M, exc=False)

        # WTA lateralne
        self._s('mot_tl',  'inh_r',   M)
        self._s('inh_r',   'mot_tr',  I, exc=False)
        self._s('mot_tr',  'inh_l',   M)
        self._s('inh_l',   'mot_tl',  I, exc=False)
        self._s('inh_fwd', 'mot_fwd', I, exc=False)

        # Eksploracja
        self._s('explore', 'mot_fwd', M)
        self._s('explore', 'mot_tl',  W)
        self._s('explore', 'mot_tr',  W)
        self._s('hunger',  'explore', M)
        self._s('hunger',  'approach', M)

        # Pamięć
        self._s('mem1', 'mem1',   1.0)
        self._s('mem2', 'mem2',   1.0)
        self._s('go_fwd', 'mem1', W)
        self._s('turn_l', 'mem2', W)
        self._s('mem1', 'go_fwd', W)
        self._s('mem2', 'turn_l', W)

        # Modulacja
        self._s('DA',  'approach', M)
        self._s('5HT', 'avoid',   M)

        self._set_vis()
        print(f"🧠 Brain: {len(self.neurons)} neurons, "
              f"{len(self.synapses)} synapses")

    def _set_vis(self):
        groups = {'S': [], 'I': [], 'M': [], 'X': []}
        for n in self.neurons:
            if n.label.startswith(('food','dang','wall','hunger','pain')):
                groups['S'].append(n)
            elif n.label.startswith('mot_'):
                groups['M'].append(n)
            elif n.label in ('DA','5HT'):
                groups['X'].append(n)
            else:
                groups['I'].append(n)
        xs = {'S': 0.07, 'I': 0.48, 'M': 0.92, 'X': 0.75}
        for g, ns in groups.items():
            for i, n in enumerate(ns):
                n.vx = xs[g]
                n.vy = (i + 1) / (len(ns) + 1)
                if g == 'X':
                    n.vy = 0.82 + i * 0.08

    def _test(self):
        print("Testing motor pathways...")
        tests = [
            ('food_front', 'mot_fwd', 'FWD←food_front'),
            ('food_left',  'mot_tl',  'TL←food_left'),
            ('food_right', 'mot_tr',  'TR←food_right'),
            ('dang_left',  'mot_tr',  'TR←dang_left'),
        ]
        ok = True
        for src, dst, desc in tests:
            for n in self.neurons:
                n.v, n.u = n.c, n.b * n.c
                n.I_syn = n.I_ext = 0
                n.spikes = 0
                n.trace = 0
            for _ in range(50):
                self.neurons[self.ids[src]].I_ext = 22.0
                for neuron in self.neurons:
                    if neuron.step():
                        for si in self.outgoing[neuron.id]:
                            s = self.synapses[si]
                            p = self.neurons[s.post]
                            p.I_syn += s.w if s.exc else -s.w
            sp = self.neurons[self.ids[dst]].spikes
            r = "✅" if sp > 0 else "❌"
            print(f"  {r} {desc}: {sp} spikes")
            if sp == 0: ok = False

        for n in self.neurons:
            n.v, n.u = n.c, n.b * n.c
            n.I_syn = n.I_ext = 0
            n.spikes = 0
            n.trace = 0
        print(f"  {'✅ ALL OK' if ok else '⚠ Check wiring'}\n")

    def sense(self, label, value):
        if label in self.ids and value > 0.02:
            self.neurons[self.ids[label]].I_ext += value * 22.0

    def step(self):
        self.step_num += 1
        self.neurons[self.ids['explore']].I_ext += random.uniform(5, 14)

        for neuron in self.neurons:
            if neuron.step():
                for si in self.outgoing[neuron.id]:
                    s = self.synapses[si]
                    p = self.neurons[s.post]
                    p.I_syn += s.w if s.exc else -s.w

        self._stdp()

        if self.neurons[self.ids['DA']].fired:
            self.dopamine = min(self.dopamine + 0.25, 3.0)
        if self.neurons[self.ids['5HT']].fired:
            self.serotonin = min(self.serotonin + 0.25, 3.0)
        self.dopamine *= 0.993
        self.serotonin *= 0.993

    def _stdp(self):
        reward = self.dopamine - self.serotonin * 0.5
        for syn in self.synapses:
            if not syn.exc:
                continue
            pre = self.neurons[syn.pre]
            post = self.neurons[syn.post]
            dw = 0.0
            if pre.fired and post.trace > 0.05:
                dw -= 0.008 * post.trace
            if post.fired and pre.trace > 0.05:
                dw += 0.010 * pre.trace
            syn.elig = syn.elig * 0.96 + dw
            if abs(reward) > 0.03 and abs(syn.elig) > 0.001:
                actual = syn.elig * reward * 0.015
                if actual > 0:
                    syn.w += actual * (18.0 - syn.w) / 18.0
                    self.ltp_total += 1
                else:
                    syn.w += actual * (syn.w - 0.1) / 18.0
                    self.ltd_total += 1
                syn.w = max(0.1, min(18.0, syn.w))

    def get_motors(self):
        return {
            'fwd': self.neurons[self.ids['mot_fwd']].spikes,
            'tl':  self.neurons[self.ids['mot_tl']].spikes,
            'tr':  self.neurons[self.ids['mot_tr']].spikes,
        }

    def reset_spikes(self):
        for n in self.neurons:
            n.spikes = 0

    def reward(self, amt):
        if amt > 0:
            self.dopamine = min(self.dopamine + amt, 3.0)
            self.neurons[self.ids['DA']].I_ext += amt * 20
        else:
            self.serotonin = min(self.serotonin + abs(amt), 3.0)
            self.neurons[self.ids['5HT']].I_ext += abs(amt) * 20
            self.neurons[self.ids['pain']].I_ext += abs(amt) * 15


# ═══════════════════════════════════════════════════════
#  WORLD — szybka mysz, wolni wrogowie
# ═══════════════════════════════════════════════════════

class World:
    def __init__(self, w=600, h=600):
        self.w, self.h = w, h
        self.cx, self.cy = w / 2.0, h / 2.0
        self.heading = random.uniform(0, 2 * math.pi)
        self.fwd_speed = 3.5        # Szybka mysz!
        self.turn_speed = 0.12      # Szybkie skręty!
        self.energy = 100.0
        self.food_eaten = 0
        self.damage = 0
        self.alive_t = 0
        self.gen = 1
        self.best_score = 0
        self.score = 0
        self.sensor_range = 200.0
        self.fov = math.pi * 0.85

        self.foods = []
        self.enemies = []
        self.poisons = []
        self.trail = deque(maxlen=300)
        self._spawn()

    def _spawn(self):
        m = 50
        self.foods = [
            {'x': random.uniform(m, self.w - m),
             'y': random.uniform(m, self.h - m), 'alive': True}
            for _ in range(8)
        ]
        self.enemies = []
        for _ in range(3):
            a = random.uniform(0, 6.28)
            sp = random.uniform(0.15, 0.4)     # WOLNI!
            self.enemies.append({
                'x': random.uniform(m, self.w - m),
                'y': random.uniform(m, self.h - m),
                'vx': math.cos(a) * sp,
                'vy': math.sin(a) * sp
            })
        self.poisons = [
            {'x': random.uniform(m, self.w - m),
             'y': random.uniform(m, self.h - m)}
            for _ in range(3)
        ]

    def _angle_to(self, tx, ty):
        dx, dy = tx - self.cx, ty - self.cy
        abs_angle = math.atan2(dy, dx)
        rel = abs_angle - self.heading
        while rel > math.pi:  rel -= 2 * math.pi
        while rel < -math.pi: rel += 2 * math.pi
        return rel

    def _dist_to(self, tx, ty):
        return math.sqrt((tx - self.cx)**2 + (ty - self.cy)**2)

    def sensors(self):
        sr = self.sensor_range
        d = {k: 0.0 for k in [
            'food_front', 'food_left', 'food_right', 'food_near',
            'dang_front', 'dang_left', 'dang_right', 'dang_near',
            'wall_front', 'wall_left', 'wall_right',
            'hunger', 'pain'
        ]}

        for f in self.foods:
            if not f['alive']:
                continue
            dist = self._dist_to(f['x'], f['y'])
            if dist > sr or dist < 1:
                continue
            angle = self._angle_to(f['x'], f['y'])
            strength = 1.0 - dist / sr

            if abs(angle) < self.fov / 2:
                if abs(angle) < 0.4:
                    d['food_front'] = max(d['food_front'], strength)
                elif angle < 0:
                    d['food_left'] = max(d['food_left'], strength)
                else:
                    d['food_right'] = max(d['food_right'], strength)

            if dist < 60:
                d['food_near'] = max(d['food_near'], min(1.0, strength * 2.5))
                if abs(angle) >= self.fov / 2:
                    if angle < 0:
                        d['food_left'] = max(d['food_left'], strength * 0.5)
                    else:
                        d['food_right'] = max(d['food_right'], strength * 0.5)

        dangers = [(e['x'], e['y'], 1.5) for e in self.enemies] + \
                  [(p['x'], p['y'], 1.0) for p in self.poisons]
        for tx, ty, mult in dangers:
            dist = self._dist_to(tx, ty)
            if dist > sr or dist < 1:
                continue
            angle = self._angle_to(tx, ty)
            strength = (1.0 - dist / sr) * mult

            if abs(angle) < self.fov / 2:
                if abs(angle) < 0.4:
                    d['dang_front'] = max(d['dang_front'], strength)
                elif angle < 0:
                    d['dang_left'] = max(d['dang_left'], strength)
                else:
                    d['dang_right'] = max(d['dang_right'], strength)
            if dist < 70:
                d['dang_near'] = max(d['dang_near'], min(1.0, strength * 2))
                if abs(angle) >= self.fov / 2:
                    if angle < 0:
                        d['dang_left'] = max(d['dang_left'], strength * 0.4)
                    else:
                        d['dang_right'] = max(d['dang_right'], strength * 0.4)

        for name, angle_off in [('wall_front', 0), ('wall_left', -0.7),
                                 ('wall_right', 0.7)]:
            a = self.heading + angle_off
            for step in range(1, 8):
                px = self.cx + math.cos(a) * step * 10
                py = self.cy + math.sin(a) * step * 10
                if px < 10 or px > self.w - 10 or py < 10 or py > self.h - 10:
                    d[name] = max(d[name], 1.0 - step / 8.0)
                    break

        d['hunger'] = max(0, 1.0 - self.energy / 100.0)
        return d

    def move(self, motor):
        fwd = motor.get('fwd', 0)
        tl = motor.get('tl', 0)
        tr = motor.get('tr', 0)

        turn = (tr - tl) * self.turn_speed
        turn = max(-0.35, min(0.35, turn))
        self.heading = (self.heading + turn) % (2 * math.pi)

        if fwd > 0:
            speed = min(fwd * 0.6, self.fwd_speed)    # Szybsze przyspieszenie
            self.cx += math.cos(self.heading) * speed
            self.cy += math.sin(self.heading) * speed

        self.cx = max(12, min(self.w - 12, self.cx))
        self.cy = max(12, min(self.h - 12, self.cy))
        self.trail.append((self.cx, self.cy))

    def update(self, brain):
        ev = {'ate': False, 'hit': False, 'poison': False}

        # Wrogowie — WOLNI i LOSOWI
        for e in self.enemies:
            dx, dy = self.cx - e['x'], self.cy - e['y']
            dist = math.sqrt(dx * dx + dy * dy)

            # Słabe śledzenie — bardziej losowy ruch
            if 0 < dist < 200:
                e['vx'] += dx / dist * 0.008     # Bardzo słabe śledzenie
                e['vy'] += dy / dist * 0.008
            
            # Duży komponent losowy
            e['vx'] += random.uniform(-0.12, 0.12)
            e['vy'] += random.uniform(-0.12, 0.12)

            # Losowe zmiany kierunku
            if random.random() < 0.02:
                a = random.uniform(0, 6.28)
                e['vx'] = math.cos(a) * 0.3
                e['vy'] = math.sin(a) * 0.3

            # Niska max prędkość
            sp = math.sqrt(e['vx']**2 + e['vy']**2)
            if sp > 0.6:                          # Max 0.6 (mysz ma 3.5!)
                e['vx'] *= 0.6 / sp
                e['vy'] *= 0.6 / sp

            e['x'] += e['vx']
            e['y'] += e['vy']
            if e['x'] < 15 or e['x'] > self.w - 15: e['vx'] *= -1
            if e['y'] < 15 or e['y'] > self.h - 15: e['vy'] *= -1
            e['x'] = max(10, min(self.w - 10, e['x']))
            e['y'] = max(10, min(self.h - 10, e['y']))

        for f in self.foods:
            if not f['alive']:
                continue
            if self._dist_to(f['x'], f['y']) < 18:
                f['alive'] = False
                self.energy = min(100, self.energy + 30)
                self.food_eaten += 1
                self.score += 10
                ev['ate'] = True
                brain.reward(3.0)

        for e in self.enemies:
            if math.hypot(self.cx - e['x'], self.cy - e['y']) < 20:
                self.energy -= 2.0
                self.damage += 1
                ev['hit'] = True
                brain.reward(-2.0)

        for p in self.poisons:
            if math.hypot(self.cx - p['x'], self.cy - p['y']) < 18:
                self.energy -= 1.2
                ev['poison'] = True
                brain.reward(-1.5)

        self.energy -= 0.01
        self.alive_t += 1

        alive_f = sum(1 for f in self.foods if f['alive'])
        if alive_f < 4:
            for f in self.foods:
                if not f['alive']:
                    f['x'] = random.uniform(50, self.w - 50)
                    f['y'] = random.uniform(50, self.h - 50)
                    f['alive'] = True
                    break

        if self.energy <= 0:
            self.best_score = max(self.best_score, self.score)
            self.gen += 1
            self.cx, self.cy = self.w / 2, self.h / 2
            self.heading = random.uniform(0, 6.28)
            self.energy = 100
            self.score = 0
            self.alive_t = 0
            self.trail.clear()
            self._spawn()

        return ev


# ═══════════════════════════════════════════════════════
#  RENDERER
# ═══════════════════════════════════════════════════════

class Renderer:
    def __init__(self, ww=600, wh=600):
        pygame.init()
        self.WW, self.WH = ww, wh
        self.BW = 380
        self.PH = 120
        self.TW = ww + self.BW
        self.TH = wh + self.PH
        self.screen = pygame.display.set_mode((self.TW, self.TH))
        pygame.display.set_caption("🧠 Bio Brain v5 — Fast Mouse")
        self.font = pygame.font.SysFont("Consolas", 12)
        self.fontb = pygame.font.SysFont("Consolas", 14, bold=True)
        self.fonts = pygame.font.SysFont("Consolas", 10)
        self.clock = pygame.time.Clock()

    def draw(self, world, brain, motor, sensors, events):
        self.screen.fill((8, 8, 18))
        self._world(world, events)
        self._brain(brain, motor)
        self._panel(world, brain, sensors, motor)
        pygame.display.flip()

    def _world(self, w, ev):
        s = pygame.Surface((self.WW, self.WH))
        s.fill((5, 8, 15))
        for x in range(0, self.WW, 50):
            pygame.draw.line(s, (15, 18, 25), (x, 0), (x, self.WH))
        for y in range(0, self.WH, 50):
            pygame.draw.line(s, (15, 18, 25), (0, y), (self.WW, y))

        # Trail
        pts = list(w.trail)
        for i in range(1, len(pts)):
            a = i / len(pts)
            c = (int(20 * a), int(50 * a), int(30 * a))
            pygame.draw.line(s, c,
                (int(pts[i-1][0]), int(pts[i-1][1])),
                (int(pts[i][0]), int(pts[i][1])), 1)

        cx, cy = int(w.cx), int(w.cy)

        # FOV cone
        fov_len = int(w.sensor_range)
        for ao in [-w.fov/2, w.fov/2]:
            a = w.heading + ao
            pygame.draw.line(s, (25, 35, 50), (cx, cy),
                (cx + int(math.cos(a)*fov_len),
                 cy + int(math.sin(a)*fov_len)), 1)

        # Poisons
        for p in w.poisons:
            px, py = int(p['x']), int(p['y'])
            pygame.draw.circle(s, (120, 25, 160), (px, py), 12)
            pygame.draw.circle(s, (160, 40, 200), (px, py), 12, 2)

        # Food
        for f in w.foods:
            if f['alive']:
                fx, fy = int(f['x']), int(f['y'])
                pygame.draw.circle(s, (15, 160, 40), (fx, fy), 7)
                pygame.draw.circle(s, (40, 220, 70), (fx, fy), 7, 2)

        # Enemies — z oczami i kierunkiem
        for e in w.enemies:
            ex, ey = int(e['x']), int(e['y'])
            pygame.draw.circle(s, (160, 20, 20), (ex, ey), 10)
            # Kierunek ruchu
            sp = math.sqrt(e['vx']**2 + e['vy']**2)
            if sp > 0.01:
                dx, dy = e['vx']/sp, e['vy']/sp
                pygame.draw.line(s, (220, 50, 50), (ex, ey),
                    (ex + int(dx*15), ey + int(dy*15)), 2)
                # Oczka
                pygame.draw.circle(s, (255, 100, 100),
                    (ex + int(dx*5 - dy*3), ey + int(dy*5 + dx*3)), 2)
                pygame.draw.circle(s, (255, 100, 100),
                    (ex + int(dx*5 + dy*3), ey + int(dy*5 - dx*3)), 2)

        # Flash
        if ev.get('ate'):
            pygame.draw.circle(s, (50, 255, 50), (cx, cy), 25, 3)
        if ev.get('hit') or ev.get('poison'):
            pygame.draw.circle(s, (255, 30, 30), (cx, cy), 25, 3)

        # Creature — trójkąt z okiem
        er = w.energy / 100.0
        body_col = (int(40 + 200*(1-er)), int(70 + 180*er), int(120*er))

        hx = cx + int(math.cos(w.heading) * 15)
        hy = cy + int(math.sin(w.heading) * 15)
        lx = cx + int(math.cos(w.heading + 2.4) * 11)
        ly = cy + int(math.sin(w.heading + 2.4) * 11)
        rx = cx + int(math.cos(w.heading - 2.4) * 11)
        ry = cy + int(math.sin(w.heading - 2.4) * 11)

        pygame.draw.polygon(s, body_col, [(hx,hy),(lx,ly),(rx,ry)])
        pygame.draw.polygon(s, (170,170,255), [(hx,hy),(lx,ly),(rx,ry)], 2)

        # Oko
        ex2 = cx + int(math.cos(w.heading) * 8)
        ey2 = cy + int(math.sin(w.heading) * 8)
        pygame.draw.circle(s, (255, 255, 255), (ex2, ey2), 3)
        px = ex2 + int(math.cos(w.heading) * 1.5)
        py2 = ey2 + int(math.sin(w.heading) * 1.5)
        pygame.draw.circle(s, (0, 0, 0), (px, py2), 1)

        # Energy bar
        bw = 26
        pygame.draw.rect(s, (40,40,40), (cx-bw//2, cy-20, bw, 3))
        pygame.draw.rect(s, (40,200,40), (cx-bw//2, cy-20, int(bw*er), 3))

        pygame.draw.rect(s, (35,35,70), (0,0,self.WW,self.WH), 2)
        self.screen.blit(s, (0, 0))

    def _brain(self, brain, motor):
        s = pygame.Surface((self.BW, self.WH))
        s.fill((6, 6, 16))

        t = self.fontb.render("BRAIN", True, (120,120,240))
        s.blit(t, (self.BW//2 - 22, 3))

        for syn in brain.synapses:
            pre, post = brain.neurons[syn.pre], brain.neurons[syn.post]
            x1 = int(pre.vx * (self.BW-20) + 10)
            y1 = int(pre.vy * (self.WH-40) + 20)
            x2 = int(post.vx * (self.BW-20) + 10)
            y2 = int(post.vy * (self.WH-40) + 20)
            wn = min(1.0, syn.w / 14.0)
            if syn.exc:
                c = (0, int(60+100*wn), int(40+60*wn))
            else:
                c = (int(100+100*wn), int(20*wn), int(20*wn))
            pygame.draw.line(s, c, (x1,y1), (x2,y2), max(1, int(wn*2.5)))

        for n in brain.neurons:
            nx = int(n.vx * (self.BW-20) + 10)
            ny = int(n.vy * (self.WH-40) + 20)
            sz = 4 + min(4, n.spikes)
            if n.fired:
                pygame.draw.circle(s, (255,255,40), (nx,ny), sz+5, 2)
                col = (255,255,170)
            elif n.is_exc:
                vn = max(0, min(1, (n.v+80)/110.0))
                col = (int(15+50*vn), int(30+100*vn), int(60+130*vn))
            else:
                vn = max(0, min(1, (n.v+80)/110.0))
                col = (int(80+120*vn), int(15+25*vn), int(25+30*vn))
            pygame.draw.circle(s, col, (nx,ny), sz)
            t = self.fonts.render(n.label, True, (100,100,140))
            s.blit(t, (nx - len(n.label)*3, ny + sz + 2))

        # Motor bars
        my = self.WH - 35
        mnames = {'fwd': 'FORWARD', 'tl': 'TURN L', 'tr': 'TURN R'}
        for i, (key, name) in enumerate(mnames.items()):
            val = motor.get(key, 0)
            bw = int(min(val, 15) / 15.0 * 80)
            mx = 15 + i * 125
            t = self.fonts.render(name, True, (160,160,200))
            s.blit(t, (mx, my))
            pygame.draw.rect(s, (180,140,20), (mx, my+12, bw, 8))
            t2 = self.fonts.render(str(val), True, (180,180,200))
            s.blit(t2, (mx+bw+3, my+10))

        pygame.draw.rect(s, (35,35,70), (0,0,self.BW,self.WH), 2)
        self.screen.blit(s, (self.WW, 0))

    def _panel(self, world, brain, sensors, motor):
        p = pygame.Surface((self.TW, self.PH))
        p.fill((10,10,24))
        y0 = 4
        c1, c2, c3, c4 = 10, 210, 440, 700

        t = self.fontb.render("CREATURE", True, (60,160,255))
        p.blit(t, (c1, y0))
        ls = [
            f"Energy: {world.energy:.0f}%",
            f"Food: {world.food_eaten}   Dmg: {world.damage}",
            f"Gen: {world.gen}   Score: {world.score}",
            f"Best: {world.best_score}   "
            f"Hdg: {math.degrees(world.heading):.0f}°",
            f"Time: {world.alive_t // 30}s"
        ]
        for i, l in enumerate(ls):
            col = (255,50,50) if 'Energy' in l and world.energy < 25 else (150,150,170)
            p.blit(self.font.render(l, True, col), (c1, y0+18+i*14))

        t = self.fontb.render("SENSORS", True, (60,230,110))
        p.blit(t, (c2, y0))
        show = ['food_front','food_left','food_right',
                'dang_front','dang_left','dang_right','hunger']
        for i, nm in enumerate(show):
            v = sensors.get(nm, 0)
            col = (0,150,40) if 'food' in nm else (
                (150,25,25) if 'dang' in nm else (150,150,30))
            p.blit(self.fonts.render(f"{nm:>12}", True, (120,120,140)),
                   (c2, y0+18+i*13))
            pygame.draw.rect(p, col, (c2+85, y0+19+i*13, int(v*55), 9))

        t = self.fontb.render("MOTORS", True, (230,160,60))
        p.blit(t, (c3, y0))
        mnames = {'fwd':'FORWARD', 'tl':'TURN_L', 'tr':'TURN_R'}
        for i, (k, nm) in enumerate(mnames.items()):
            v = motor.get(k, 0)
            bw = int(min(v, 15) / 15.0 * 90)
            p.blit(self.font.render(f"{nm:>8}: {v}", True, (150,150,170)),
                   (c3, y0+18+i*20))
            pygame.draw.rect(p, (180,130,20),
                             (c3+95, y0+20+i*20, bw, 14))

        t = self.fontb.render("BRAIN", True, (160,120,240))
        p.blit(t, (c4, y0))
        bl = [
            f"Dopamine:  {brain.dopamine:.2f}",
            f"Serotonin: {brain.serotonin:.2f}",
            f"LTP: {brain.ltp_total}  LTD: {brain.ltd_total}",
            f"Step: {brain.step_num}",
        ]
        for i, l in enumerate(bl):
            col = (150,150,170)
            if 'Dopa' in l and brain.dopamine > 0.5: col = (50,240,50)
            if 'Sero' in l and brain.serotonin > 0.5: col = (240,50,50)
            p.blit(self.font.render(l, True, col), (c4, y0+18+i*14))

        p.blit(self.fonts.render(
            "SPACE=pause  R=reset  +/-=speed  D=reward  S=pain  ESC=quit",
            True, (50,50,80)), (10, self.PH-14))
        pygame.draw.rect(p, (35,35,70), (0,0,self.TW,self.PH), 2)
        self.screen.blit(p, (0, self.WH))


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    print("=" * 50)
    print("🧠 BIO BRAIN v5 — Fast Mouse, Slow Enemies")
    print("=" * 50)
    print("Mouse speed: 3.5   Enemy speed: 0.3-0.6")
    print("SPACE=pause R=reset +/-=speed D=reward S=pain")
    print()

    world = World(600, 600)
    brain = Brain()
    rend = Renderer(600, 600)

    running = True
    paused = False
    sim_speed = 10
    motor = {'fwd': 0, 'tl': 0, 'tr': 0}
    sensors = {}
    events = {}
    frame = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    world.gen += 1
                    world.cx, world.cy = 300, 300
                    world.heading = random.uniform(0, 6.28)
                    world.energy = 100
                    world.score = 0
                    world.trail.clear()
                    world._spawn()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    sim_speed = min(40, sim_speed + 2)
                    print(f"Speed: {sim_speed}")
                elif event.key == pygame.K_MINUS:
                    sim_speed = max(2, sim_speed - 2)
                    print(f"Speed: {sim_speed}")
                elif event.key == pygame.K_d:
                    brain.reward(4.0)
                    print("💊 REWARD")
                elif event.key == pygame.K_s:
                    brain.reward(-4.0)
                    print("💀 PAIN")

        if paused:
            rend.draw(world, brain, motor, sensors, events)
            rend.clock.tick(30)
            continue

        brain.reset_spikes()
        sensors = world.sensors()

        for _ in range(sim_speed):
            for name, val in sensors.items():
                brain.sense(name, val)
            brain.step()

        motor = brain.get_motors()
        world.move(motor)
        events = world.update(brain)

        rend.draw(world, brain, motor, sensors, events)
        rend.clock.tick(30)

        frame += 1
        if frame % 90 == 0:
            print(
                f"  FWD:{motor['fwd']:2d} TL:{motor['tl']:2d} "
                f"TR:{motor['tr']:2d} | "
                f"E:{world.energy:.0f} F:{world.food_eaten} "
                f"DA:{brain.dopamine:.2f} "
                f"Gen:{world.gen} Score:{world.score}"
            )

    pygame.quit()
    print(f"\nBest: {world.best_score}  Food: {world.food_eaten}")


if __name__ == '__main__':
    main()