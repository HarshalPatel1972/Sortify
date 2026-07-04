import json
import os

mapping = {
    'Amplifier': 'Electronics',
    'Particle Accelerators': 'Nuclear Physics',
    'Stern-Gerlach Experiment': 'Quantum Mechanics',
    'Central Force': 'Classical Mechanics',
    'Field Quanta': 'Quantum Mechanics',
    'Nuclear Physics': 'Nuclear Physics',
    'Kinetic Theory': 'Thermodynamics',
    'Particle Physics': 'Nuclear Physics',
    'Intrinsic Semiconductors': 'Semiconductor Physics',
    'Diffraction Grating': 'Optics',
    'Electrodynamics': 'Electromagnetic Theory',
    'Hall Effect': 'Solid State Physics',
    'Linear Algebra': 'Mathematical Physics',
    'Rotational Kinetics': 'Classical Mechanics',
    'Nuclear Magnetic Resonance': 'Solid State Physics',
    'Magnetism': 'Electromagnetic Theory',
    'Magnetisation': 'Electromagnetic Theory',
    'Double Refraction': 'Optics',
    'Raman Spectroscopy': 'Atomic Physics',
    'Electromagnetism': 'Electromagnetic Theory',
    'Statistical Mechanics': 'Statistical Mechanics',
    'Nuclear Force': 'Nuclear Physics',
    'Fabry-Pérot Interferometer': 'Optics',
    'Transistor': 'Electronics',
    'Angular Momentum': 'Quantum Mechanics',
    'Semiconductors': 'Semiconductor Physics',
    'Quarks': 'Nuclear Physics',
    'Conservation Laws': 'Classical Mechanics',
    'Experimental Physics': 'Modern Physics',
    'Leptons': 'Nuclear Physics',
    'Nuclear Shell Model': 'Nuclear Physics',
    'Solid State Physics': 'Solid State Physics',
    'Quark Constituents': 'Nuclear Physics',
    'Quantum Tunneling': 'Quantum Mechanics',
    'MOSFET': 'Electronics',
    'Conservative Field': 'Classical Mechanics',
    'Molecular Physics': 'Atomic Physics',
    'Special Relativity': 'Modern Physics',
    'Hamiltonian Mechanics': 'Classical Mechanics',
    'Superconductivity': 'Superconductivity',
    'Molecular Spectroscopy': 'Atomic Physics',
    'Nuclear Fusion': 'Nuclear Physics',
    'Inertia Tensor': 'Classical Mechanics',
    'Uncertainty Principle': 'Quantum Mechanics',
    'Atomic Physics': 'Atomic Physics',
    'Nuclear Decay': 'Nuclear Physics',
    'Electric Circuits': 'Electronics',
    'Nuclear Reactions': 'Nuclear Physics',
    'Lagrangian Mechanics': 'Classical Mechanics',
    'Parity Transformation': 'Quantum Mechanics',
    'Electrostatics': 'Electromagnetic Theory',
    'Bohr Model': 'Atomic Physics',
    'JFET': 'Electronics',
    'Op-amp': 'Electronics',
    'Quantum Mechanics': 'Quantum Mechanics',
    'Electromagnetic Waves': 'Electromagnetic Theory',
    'Fraunhofer Diffraction': 'Optics',
    'Relativity': 'Modern Physics',
    'Stationary Waves': 'Wave and Oscillation',
    'Astrophysics': 'Modern Physics',
    'Operational Amplifier': 'Electronics',
    'Electromagnetic Radiation': 'Electromagnetic Theory',
    'Amplifiers': 'Electronics',
    'Black Body Radiation': 'Modern Physics',
    'Molecular Vibration': 'Atomic Physics',
    'Rotational Kinematics': 'Classical Mechanics',
    'Rigid Body Motion': 'Classical Mechanics',
    'Wave Mechanics': 'Quantum Mechanics',
    'Semiconductor Physics': 'Semiconductor Physics',
    'Radioactivity': 'Nuclear Physics',
    'Thermodynamics': 'Thermodynamics',
    'Digital Electronics': 'Electronics',
    'Oscillations': 'Wave and Oscillation',
    'Diffusion': 'Statistical Mechanics',
    'Optics': 'Optics',
    'Nuclear Binding Energy': 'Nuclear Physics',
    'Nuclear Forces': 'Nuclear Physics',
    'Magnetostatics': 'Electromagnetic Theory',
    'Laser Physics': 'Optics',
    'Michelson-Morley Experiment': 'Modern Physics',
    'Conductors and Semiconductors': 'Semiconductor Physics'
}

file_path = 'c:/Users/Harshal Patel/Desktop/PDFx/data/json_results/all_questions.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for q in data:
    old_topic = q.get('topic', 'Uncategorized')
    if old_topic in mapping:
        q['topic'] = mapping[old_topic]
    else:
        q['topic'] = 'Modern Physics' # default fallback

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print("Successfully reclassified topics!")
