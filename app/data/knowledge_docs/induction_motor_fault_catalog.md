# Industrial Induction Motor Diagnostic Catalog & Fault Codes

## 1. Fault Code: E101_BEARING_DEGRADATION (Rolling Element Bearings)
- **Primary Symptoms**:
  - Vibration peak acceleration exceeds 2.2 g (often accompanied by ultrasonic shock pulses).
  - Overall vibration RMS rises gradually into Zone C (3.5 - 6.5 mm/s).
  - Bearing housing temperature exceeds 75°C - 90°C (normal operating range is 45°C - 65°C).
  - Audible high-pitch grinding or metallic whining.
- **Root Causes**:
  - Inadequate lubrication, grease starvation, or degraded lithium grease (grease coking).
  - Foreign particle contamination (silica, metallic dust).
  - Bearing fatigue spalling on outer raceway (BPFO) or inner raceway (BPFI).
  - False brinelling due to vibration during standstill.
- **Diagnostic Verification**:
  - Perform envelope demodulation analysis or FFT spectrum inspection. Check bearing fault frequencies (BPFO, BPFI, BSF, FTF).
  - Check acoustic emission and temperature gradient.
- **Prescribed Remediation**:
  1. Inspect grease replenishment schedule and grease port for blockage.
  2. If bearing temperature exceeds 85°C and peak acceleration is > 3.0 g, plan controlled shutdown within 4 hours.
  3. Replace drive-end (DE) or non-drive-end (NDE) deep groove ball / cylindrical roller bearing.
  4. Ensure proper shaft tolerance (k5/m5 fit) and induction heating bearing installation technique.

## 2. Fault Code: E204_MOTOR_OVERHEAT (Thermal Stator/Winding Stress)
- **Primary Symptoms**:
  - Winding / casing temperature rises above 95°C (Class F insulation limit is 155°C, but thermal trip setpoint is typically 105°C - 120°C).
  - Current draw increases by 10% - 25% above nameplate Full Load Amperes (FLA).
  - Hot motor odor / ozone smell.
- **Root Causes**:
  - Cooling fan cowl clogged with lint, sawdust, or industrial grime.
  - Ambient temperature exceeding 40°C in unventilated electrical enclosure.
  - Chronic mechanical overload or high friction from driven machine.
  - Low supply voltage causing inverse current rise to maintain shaft torque ($P = \sqrt{3} V I \cos\phi$).
- **Prescribed Remediation**:
  1. Measure line voltage on all three phases ($L_1, L_2, L_3$). Ensure voltage imbalance is under 1.5%.
  2. Inspect cooling fan blades and clean cowl shroud immediately using compressed dry air.
  3. Measure stator insulation resistance using 1000V DC Megger (> 50 Mega-ohms required).
  4. Reduce mechanical load or de-rate motor if ambient exceeds 45°C.

## 3. Fault Code: E401_ROTOR_UNBALANCE & MISALIGNMENT
- **Primary Symptoms**:
  - High vibration velocity RMS (Zone C or Zone D: 5.5 to 12.0 mm/s) predominantly at 1X running frequency (unbalance) or 2X running frequency (angular/parallel misalignment).
  - High axial vibration at motor drive-end bearing.
  - Elevated current draw with cyclic oscillation.
- **Root Causes**:
  - Accumulation of dirt on rotor fan or loss of balancing weights.
  - Thermal expansion or foundation shift causing shaft misalignment between motor and driven gearbox/pump.
  - Flexible coupling insert (spider elastomer) shredded or worn.
  - Soft foot condition on mounting feet.
- **Prescribed Remediation**:
  1. Verify dial indicator or laser alignment tolerances (maximum allowable offset 0.05 mm, angularity 0.05 mm/100mm).
  2. Perform dynamic two-plane balancing in accordance with ISO 1940 Grade G2.5.
  3. Inspect and tighten foundation hold-down bolts to rated torque using a calibrated torque wrench.
  4. Replace damaged flexible coupling insert.

## 4. Fault Code: E502_PHASE_IMBALANCE
- **Primary Symptoms**:
  - Current imbalance exceeding 5% between phases: $Imbalance\% = \frac{\max|I - I_{avg}|}{I_{avg}} \times 100\%$.
  - 2X slip frequency sidebands around line frequency (100 Hz / 120 Hz).
  - Rapid temperature rise in stator core ($Temperature \propto I^2 R$).
- **Prescribed Remediation**:
  1. Check VFD output or incoming contactor terminal lugs for high-resistance loose connections.
  2. Inspect contactor contacts for pitting or arc erosion.
  3. Conduct winding phase resistance test using micro-ohmmeter; variance must be < 2%.
