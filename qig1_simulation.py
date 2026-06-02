#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QIG-1: Quantum Informational Gravity – Tabletop Verification
Simulation of mutual information accumulation and resonant force amplification.

This script models the entanglement dynamics of two levitated nanoparticles
(NV centers) and calculates the anomalous force arising from the code-failure
potential Φ(I) = (I_c / (I_c - I))^γ with γ ≈ 1.24.

Author: International Group of Developers (IGD)
Date: 2026-06-02
License: MIT
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import os

# =====================================================================
# SYSTEM CONSTANTS (QIG-1 Technical Specification)
# =====================================================================
I_c = 100.0               # Maximum mutual information capacity (bits)
gamma = 1.24              # Critical exponent (3D Ising universality class)
m = 0.15e-12              # Mass of each nanoparticle (0.15 ng -> kg)
r_distance = 2.0e-6       # Center-to-center distance (2 µm -> m)
G_newton = 6.674e-11      # Newtonian gravitational constant
k_B = 1.38e-23            # Boltzmann constant
T_cryo = 0.020            # Cryostat temperature (20 mK -> K)
f_trap = 1.0e5            # Optical trap frequency (100 kHz -> Hz)
Q_factor = 1e6            # Mechanical quality factor (vacuum)
T2_decoh = 0.025          # Spin coherence time (25 ms) at 20 mK

# Laser-cavity coupling parameters
g_cav = 5e4               # Spin-cavity Rabi frequency (Hz)
kappa_cav = 1e6           # Cavity decay rate (Hz)

# Calibration constant F0 derived from spatial gradient of entanglement field
F0 = 1.5e-17              # Newton

# =====================================================================
# ANALYTICAL TIME SCALE ESTIMATE
# =====================================================================
R_pump = (g_cav**2 / kappa_cav) * np.log(2)   # Initial pumping rate
t_sat_est = -np.log(1 - 0.999) / R_pump       # Time to reach 99.9% of I_c

print("=== ANALYTICAL TIME BALANCE ===")
print(f"Characteristic pumping time: {t_sat_est*1e3:.2f} ms")
print(f"Spin coherence time (T2):     {T2_decoh*1e3:.2f} ms")
if t_sat_est < T2_decoh:
    print("Condition (t_sat < T2):      SATISFIED (safe margin)")
else:
    print("Condition (t_sat < T2):      VIOLATED (need optimised coupling)")
print()

# =====================================================================
# DYNAMICS OF MUTUAL INFORMATION
# =====================================================================
def entanglement_dynamics(t, y):
    """
    ODE for mutual information I12(t).
    y[0] = I12 (bits)
    dI/dt = generation - decoherence
    """
    I12 = y[0]
    if I12 >= I_c:
        return [0.0]
    generation = R_pump * (I_c - I12)
    decoherence = I12 / T2_decoh
    dI = generation - decoherence
    return [max(0.0, dI)]

# Time span and evaluation points
t_span = (0, 0.015)          # 15 ms (one modulation half‑cycle)
t_eval = np.linspace(0, 0.015, 1000)

sol = solve_ivp(entanglement_dynamics, t_span, [0.0], t_eval=t_eval, method='RK45')
t = sol.t
I12 = sol.y[0]

# =====================================================================
# INFORMATIONAL FORCE
# =====================================================================
def informational_force(I12):
    """Compute F_Theta(I12) from code‑failure potential."""
    if I12 >= I_c:
        I12 = I_c - 1e-6       # avoid division by zero
    phi = (I_c / (I_c - I12)) ** gamma
    return F0 * phi

F_theta = np.array([informational_force(I) for I in I12])

# Reference forces
F_newton = G_newton * (m**2) / (r_distance**2)
noise_floor = np.sqrt(4 * k_B * T_cryo * m * (2 * np.pi * f_trap) / Q_factor)

# Print numerical summary
print("=== SIMULATION RESULTS ===")
print(f"Maximum mutual information: {I12[-1]:.2f} bits ({I12[-1]/I_c*100:.2f}% of I_c)")
print(f"Newtonian force:            {F_newton:.2e} N")
print(f"Thermal noise floor:        {noise_floor:.2e} N/√Hz")
print(f"Peak informational force:   {F_theta[-1]:.2e} N")
print(f"Excess over Newtonian:      {F_theta[-1]/F_newton:.2e} times")
print(f"Signal-to-noise ratio:      {F_theta[-1]/noise_floor:.2e} (peak / √Hz)")
print()

# =====================================================================
# PLOTTING
# =====================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# ----- Left panel: time evolution -----
ax1.set_xlabel("Time (s)", fontsize=10)
ax1.set_ylabel("Mutual information $I_{12}$ (bits)", color='tab:blue', fontsize=10)
line1, = ax1.plot(t, I12, color='tab:blue', linewidth=2)
ax1.axhline(y=I_c, color='blue', linestyle='--', alpha=0.3, label=r'Capacity $I_c$')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, alpha=0.2)

ax1b = ax1.twinx()
ax1b.set_ylabel("Force $F$ (N)", color='tab:red', fontsize=10)
line2, = ax1b.plot(t, F_theta, color='tab:red', linewidth=2.5, label=r'$F_\Theta$')
ax1b.axhline(y=1.5e-14, color='darkred', linestyle='--', linewidth=1.5, label='Target signal')
ax1b.axhline(y=noise_floor, color='green', linestyle=':', label='Thermal noise floor')
ax1b.set_yscale('log')
ax1b.tick_params(axis='y', labelcolor='tab:red')

lines = [line1, line2]
labels = ['$I_{12}(t)$', '$F_\\Theta(t)$']
ax1.legend(lines, labels, loc='lower right', fontsize=8)
ax1.set_title("A: Kinetics of force build-up", fontweight='bold')

# ----- Right panel: force vs saturation -----
ratio = np.linspace(0.0, 0.9995, 1000)
F_vs_ratio = np.array([informational_force(r * I_c) for r in ratio])

ax2.plot(ratio, F_vs_ratio, color='purple', linewidth=2.5, label='Vacuum response')
ax2.axhline(y=noise_floor, color='green', linestyle=':', label='Thermal noise floor')
ax2.axhline(y=1.5e-14, color='darkred', linestyle='--', linewidth=1.5, label='Target signal')
ax2.axvline(x=0.99, color='black', linestyle=':', alpha=0.5, label='99% saturation threshold')
ax2.set_xlabel('Relative saturation $I_{12}/I_c$', fontsize=10)
ax2.set_ylabel('Force $F$ (N)', fontsize=10)
ax2.set_yscale('log')
ax2.grid(True, alpha=0.2)
ax2.legend(loc='upper left', fontsize=8)
ax2.set_title("B: Topological singularity $\\Phi(I)$", fontweight='bold')

plt.tight_layout()

# =====================================================================
# SAVE FIGURE (as specified in README)
# =====================================================================
os.makedirs('figures', exist_ok=True)
plt.savefig('figures/QIG1_simulation.png', dpi=300, bbox_inches='tight')
print("[INFO] Figure saved to figures/QIG1_simulation.png")

plt.show()
