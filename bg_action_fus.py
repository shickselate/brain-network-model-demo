# bg_action_fus.py — BG/Thal action selection + FUS (ALIC-like) on Action 1
import nengo, numpy as np

# --- cortical drives (same as before)
def cortical_input(t):
    if t < 1.0:   return [0.3, 0.3]
    if t < 2.5:   return [0.8, 0.3]   # favour Action 1
    if t < 4.0:   return [0.3, 0.8]   # favour Action 2
    return [0.4, 0.4]

# --- FUS schedule + strength (κ)
fus_blocks = [(1.6, 3.0)]         # ON window
kappa_default = 0.5               # 0..1 (fractional attenuation)

def fus_on(t):
    return 1.0 if any(a <= t <= b for (a,b) in fus_blocks) else 0.0

with nengo.Network(label="BG action selection + FUS") as model:
    # Inputs
    cortex = nengo.Node(cortical_input, label="Cortex")
    # κ slider (GUI-overridable)
    Kappa_in = nengo.Node(size_in=1, label="kappa_in")
    Kappa_def = nengo.Node(lambda t: kappa_default)
    nengo.Connection(Kappa_def, Kappa_in, synapse=None)

    FUS = nengo.Node(fus_on, label="FUS_on")

    # Gain vector: [1 - κ·FUS, 1] → only Action 1 attenuated
    def gain_vec(t, kappa):
        g1 = 1.0 - float(kappa) * fus_on(t)
        return [g1, 1.0]

    # Build time-varying elementwise gain using a Node with input κ
    Gain = nengo.Node(size_in=1, size_out=2,
                      output=lambda t, x: gain_vec(t, x[0]),
                      label="GainVec")

    nengo.Connection(Kappa_in, Gain, synapse=None)

    # Elementwise multiply Cortex * Gain → BG input
    Prod = nengo.networks.Product(n_neurons=200, dimensions=2, label="Cortex*Gain")
    nengo.Connection(cortex, Prod.input_a, synapse=0.01)
    nengo.Connection(Gain,   Prod.input_b, synapse=0.01)

    # BG/Thal
    bg   = nengo.networks.BasalGanglia(dimensions=2)
    thal = nengo.networks.Thalamus(dimensions=2)
    nengo.Connection(Prod.output, bg.input, synapse=0.01)
    nengo.Connection(bg.output, thal.input, synapse=0.005)

    # Probes
    p_ctx  = nengo.Probe(cortex,    synapse=0.02)
    p_gain = nengo.Probe(Gain,      synapse=None)
    p_bg   = nengo.Probe(bg.output, synapse=0.03)
    p_thal = nengo.Probe(thal.output, synapse=0.03)

if __name__ == "__main__":
    with nengo.Simulator(model) as sim:
        sim.run(5.0)
    import numpy as np
    t = sim.trange(); th = sim.data[p_thal]; gain = sim.data[p_gain]
    on = (gain[:,0] < 1.0)
    choice_on  = np.argmax(np.mean(th[on],  axis=0)) if on.any()  else -1
    choice_off = np.argmax(np.mean(th[~on], axis=0)) if (~on).any() else -1
    print(f"Mean choice OFF: Action {choice_off+1}")
    print(f"Mean choice ON : Action {choice_on+1}")
