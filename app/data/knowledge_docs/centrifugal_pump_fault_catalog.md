# Centrifugal Pump Diagnostic Catalog & Fault Codes

## 1. Fault Code: E305_PUMP_CAVITATION (Hydrodynamic Cavitation)
- **Primary Symptoms**:
  - Crackling or popping sound resembling "pumping gravel, rocks, or marbles" inside the pump casing.
  - High-frequency random vibration peaking between 1,000 Hz and 5,000 Hz.
  - Discharge pressure fluctuates erratically (e.g., dropping 20% to 40% below setpoint).
  - Volumetric flow rate drops below rated capacity ($Q < Q_{rated}$).
- **Root Causes**:
  - Inadequate Net Positive Suction Head Available ($NPSH_A < NPSH_R$).
  - Suction line strainer or foot valve clogged with debris.
  - Suction valve partially throttled or closed accidentally.
  - Entrained air or gas bubbles in liquid stream.
  - Operating too far out on the pump curve (excessive flow causing extreme suction friction drop).
- **Physical Damage**:
  - Severe micro-jet pitting on the suction eye of impeller vanes.
  - Premature degradation of mechanical face seals.
  - Rapid destruction of shaft sleeves and throat bushings.
- **Prescribed Remediation**:
  1. Check suction pressure gauge immediately. Ensure suction head meets minimum operating requirement.
  2. Inspect and clear the suction basket strainer and suction piping inlet.
  3. Verify suction isolation valve is 100% fully open.
  4. Throttle discharge control valve slightly to move pump operating point back toward Best Efficiency Point (BEP).
  5. Check liquid temperature; hot liquids require higher suction pressure to prevent flashing.

## 2. Fault Code: E308_SEAL_LEAKAGE_AND_DRY_RUN
- **Primary Symptoms**:
  - Mechanical seal temperature surges above 80°C.
  - High casing vibration and audible screeching.
  - Fluid dripping or aerosol vapor mist escaping from seal gland drain port.
- **Root Causes**:
  - Loss of quench/flush fluid plan (API Plan 11, 23, or 53).
  - O-ring elastomeric chemical swelling or hardening.
  - Silicon carbide / carbon face cracking due to thermal shock.
- **Prescribed Remediation**:
  1. Verify seal flush plan flow rate and filter cleanliness.
  2. Perform controlled machine stop if leakage exceeds 5 drops/minute for hazardous fluids or 60 drops/min for clean water.
  3. Replace mechanical seal cartridge; verify shaft runout < 0.05 mm prior to installation.

## 3. Fault Code: E312_IMPELLER_CLOGGING_OR_WEAR
- **Primary Symptoms**:
  - Motor current spikes above rated FLA while head and discharge pressure drop.
  - Elevated 1X vane-pass frequency vibration ($Vane\_Pass = RPM \times Z_{vanes}$).
- **Prescribed Remediation**:
  1. Isolate and lock-out/tag-out (LOTO) pump electrical supply.
  2. Disassemble casing split or back pull-out assembly.
  3. Remove fibrous debris or foreign particulates lodged between impeller shrouds.
  4. Measure impeller wear ring clearances; replace rings if clearance exceeds 2x original OEM specification.
