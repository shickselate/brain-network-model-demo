# bg_action_demo.py
import nengo
import numpy as np

# two actions, each with time-varying cortical drive
def cortical_input(t):
    if t < 1.0:
        return [0.3, 0.3]        # both low
    elif t < 2.5:
        return [0.8, 0.3]        # favour Action 1
    elif t < 4.0:
        return [0.3, 0.8]        # favour Action 2
    else:
        return [0.4, 0.4]        # rest / tie

with nengo.Network(label="Action selection (BG-Thalamus)") as model:
    cortex = nengo.Node(cortical_input, label="Cortex")

    bg   = nengo.networks.BasalGanglia(dimensions=2)
    thal = nengo.networks.Thalamus(dimensions=2)

    nengo.Connection(cortex, bg.input, synapse=0.01)
    nengo.Connection(bg.output, thal.input, synapse=0.005)

    # Probes for plotting
    p_ctx  = nengo.Probe(cortex, synapse=0.02)
    p_bg   = nengo.Probe(bg.output, synapse=0.03)
    p_thal = nengo.Probe(thal.output, synapse=0.03)

if __name__ == "__main__":
    with nengo.Simulator(model) as sim:
        sim.run(5.0)

    t = sim.trange()
    th = sim.data[p_thal]
    print(f"Choice (argmax Thalamus) per segment:")
    for (a,b) in [(1,2.5),(2.5,4)]:
        seg = (t>=a)&(t<b)
        choice = np.argmax(np.mean(th[seg],axis=0))
        print(f"  {a:.1f}–{b:.1f}s → Action {choice+1}")
