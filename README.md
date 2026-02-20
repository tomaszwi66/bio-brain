# 🧠 Bio Brain

**Biologically Inspired Spiking Neural Creature Simulator**

A real-time simulation of a virtual creature controlled by a spiking neural
network built on biologically accurate mechanisms. The creature navigates a
2D world, forages for food, avoids predators and poisons, and learns from
experience through dopamine-modulated synaptic plasticity.

Unlike traditional AI approaches, this project uses actual neuroscience
models — every neuron fires discrete spikes, every synapse has
excitatory/inhibitory dynamics, and learning happens through biologically
plausible STDP (Spike-Timing Dependent Plasticity).

![Bio Brain Screenshot](screenshots/screenshot.png)

---

## Quick Start

**Requirements:** Python 3.8 or higher

**Install and run:**

    git clone https://github.com/yourusername/bio-brain.git
    cd bio-brain
    pip install -r requirements.txt
    python bio_brain.py

---

## Controls

| Key | Action |
|---|---|
| SPACE | Pause / Resume |
| R | Reset world |
| + / - | Simulation speed |
| D | Inject dopamine (reward) |
| S | Inject serotonin (pain) |
| ESC | Quit |

---

## Biological Mechanisms

### Neurons — Izhikevich Model (2003)

Each neuron simulates membrane voltage dynamics using the Izhikevich model,
which reproduces the spiking behavior of real cortical neurons with just
two differential equations.

| Type | Name | Biological Role |
|---|---|---|
| RS | Regular Spiking | Excitatory pyramidal cells |
| FS | Fast Spiking | Inhibitory interneurons (GABA) |
| IB | Intrinsically Bursting | Layer 5 cortical neurons |
| CH | Chattering | Layer 2/3 cortical neurons |
| LTS | Low-Threshold Spiking | Inhibitory interneurons |

### Synaptic Transmission

Excitatory synapses increase post-synaptic current (glutamate-like).
Inhibitory synapses decrease it (GABA-like). Synaptic current decays
exponentially, simulating receptor kinetics — excitatory with AMPA-like
time constant (~5ms, decay 0.85), inhibitory with GABA-A-like time
constant (~10ms, decay 0.90).

### Learning — Three-Factor STDP

The network learns through a biologically plausible three-factor rule:

**Factor 1 — Spike timing.** Pre-before-post creates eligibility for
potentiation (LTP). Post-before-pre creates eligibility for depression (LTD).

**Factor 2 — Eligibility trace.** Decaying memory of recent spike
coincidences (tau ~ 25ms). This implements synaptic tagging — the synapse
remembers that something happened.

**Factor 3 — Neuromodulation.** Dopamine (reward) and serotonin (punishment)
gate whether eligible synapses actually change their weight. Without a
neuromodulator signal, no learning occurs.

This mirrors how real brains learn: Hebbian coincidence detection identifies
candidate synapses, eligibility traces tag them, and reward signals from
dopamine neurons decide which changes to keep.

### Neuromodulators

| Molecule | Role | Biological Analog |
|---|---|---|
| Dopamine (DA) | Reward signal, strengthens active synapses | VTA/SNc dopamine neurons |
| Serotonin (5-HT) | Punishment signal, weakens active synapses | Dorsal raphe nucleus |

---

## Neural Architecture

The network contains 29 neurons and approximately 60 synapses organized
into functional layers inspired by insect brain anatomy
(Drosophila melanogaster).

### Sensory Layer (13 neurons)

- **Visual:** Food and danger detected in three sectors (front, left, right) plus a near-field detector for each
- **Proprioceptive:** Wall proximity via ray-casting in three directions
- **Interoceptive:** Hunger (inverse of energy) and pain

### Decision Layer (11 neurons)

- **Approach circuit:** Activated by food detection, drives forward movement
- **Avoid circuit:** Activated by danger and pain, drives escape
- **Explore circuit:** Chattering neuron provides spontaneous activity when no stimuli are present
- **Pre-motor commands:** go_fwd, turn_l, turn_r translate decisions into motor patterns
- **Working memory:** Two recurrent neurons (mem1, mem2) maintain recent decisions
- **Lateral inhibition:** Three fast-spiking interneurons implement Winner-Take-All between competing motor outputs

### Motor Layer (3 neurons)

Forward (mot_fwd), turn left (mot_tl), and turn right (mot_tr). Spike
count per simulation frame determines movement speed and direction.

### Modulatory Layer (2 neurons)

DA (dopamine) fires when food is near, strengthening approach pathways.
5HT (serotonin) fires on pain or danger contact, strengthening avoidance
pathways.

### Key Circuit Motifs

- **Innate reflexes:** Direct sensory-to-motor connections guarantee immediate behavioral responses
- **Winner-Take-All:** Lateral inhibition between turn motors prevents simultaneous left and right turning
- **Approach vs Avoid:** Competing circuits modulated by dopamine and serotonin determine behavioral strategy
- **Exploration drive:** Chattering neuron injects random activity, preventing the creature from freezing when idle

---

## World Environment

The creature inhabits a 600x600 pixel 2D world.

| Object | Count | Color | Effect |
|---|---|---|---|
| Food | 8 | Green | +30 energy, +10 score, triggers dopamine |
| Enemies | 3 | Red | -2 energy per contact, triggers serotonin |
| Poisons | 3 | Purple | -1.2 energy per contact, triggers serotonin |

The creature moves at 3.5 units/step while enemies move at max 0.6,
making the creature approximately 6x faster. Enemies exhibit weak tracking
behavior with large random movement components. Energy drains at 0.01 per
step. When energy reaches zero, the creature dies and respawns as a new
generation. Food respawns when fewer than 4 items remain.

### Sensory Specifications

- **Sensor range:** 200 units
- **Field of view:** ~153 degrees (0.85 pi radians)
- **Near-field detection:** 60 units (food), 70 units (danger)
- **Wall detection:** Ray-casting with 7 steps at 10-unit intervals

---

## Real-Time Visualization

The interface displays three synchronized panels:

**World View (left).** Top-down view showing the creature (triangle with
eye), food, enemies, poisons, movement trail, and field-of-view cone.
Energy bar floats above the creature.

**Brain View (right).** Neural network graph with all neurons and synapses
rendered in real-time. Firing neurons flash yellow. Synapse thickness
reflects weight. Excitatory connections shown in blue-green, inhibitory
in red. Motor output bars at the bottom.

**Dashboard (bottom).** Creature statistics, sensor activation bars, motor
output values, neuromodulator levels (dopamine and serotonin), and learning
counters (LTP and LTD events).

---

## What to Observe

### Innate Behavior (immediate)

The creature exhibits hardwired reflexes from the first moment: turning
toward visible food, turning away from danger, avoiding walls, and random
exploration when idle. These behaviors emerge from the innate wiring with
no learning required.

### Learned Behavior (over time)

Watch the LTP and LTD counters increase as the creature encounters food
and enemies. Synapses strengthen after dopamine release (food reward)
and weaken after serotonin release (pain). Over many generations, the
approach and avoidance pathways may shift in strength based on accumulated
experience.

### Neuromodulator Dynamics

Dopamine spikes when the creature approaches food (food_near to DA
pathway). Serotonin spikes on enemy or poison contact. Learning only
occurs when neuromodulator levels are elevated — this is the three-factor
gating mechanism in action.

---

## Comparison with Other AI Approaches

| Feature | Bio Brain | Typical RL Agent | Real Brain |
|---|---|---|---|
| Neuron model | Izhikevich (biophysical) | None (abstract) | Hodgkin-Huxley |
| Discrete spikes | Yes | No | Yes |
| Continuous time | 1ms steps | Discrete episodes | Continuous |
| Embodiment | Sensorimotor loop | Abstract state space | Full body |
| Learning rule | STDP + neuromodulation | Backpropagation | STDP + neuromodulation |
| Online learning | During lifetime | Batch training | During lifetime |
| Neurotransmitters | DA, 5-HT | None | DA, 5-HT, ACh, NE, ... |
| E/I balance | Explicit | No distinction | Explicit |
| Scale | ~30 neurons | ~millions of params | ~86 billion (human) |

---

## Possible Extensions

Each extension should be added one at a time with thorough testing after
each change. Multiple simultaneous additions tend to break the delicate
balance of spiking network dynamics.

- Refractory period (2ms absolute)
- Axonal transmission delays (1-3ms)
- 8-directional vision (octant-based)
- Kenyon Cells and mushroom body sparse coding
- Obstacles in world with collision detection
- Octopamine arousal system
- Reward Prediction Error (RPE)
- Short-Term Synaptic Depression (Tsodyks-Markram)
- Homeostatic synaptic scaling (Turrigiano 2008)
- Multiple creature population
- Genetic evolution of network topology

---

## License

MIT License — see LICENSE file for details.
