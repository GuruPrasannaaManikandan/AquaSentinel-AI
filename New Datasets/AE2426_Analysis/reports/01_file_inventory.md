# Report 01: File Inventory and Format Forensics

This report inventories all files within the AE2426 dataset and catalogs their physical and syntactic formats.

## Original Files Inventory

| Filename | Extension | Size (Bytes) | Format | Encoding | Delimiter | Rows | Columns | Description |
|---|---|---|---|---|---|---|---|---|
| `documents.tgz` | `.tgz` | 4,026,004 | Binary (tar.gz) | N/A | N/A | N/A | N/A | Compressed documentation archive |
| `NES-LTER_AE2426_HPLC_20241106_1628_R1.sb` | `.sb` | 11,287 | Text (SeaBASS) | UTF-8 | Comma | 32 | 51 | HPLC pigment concentrations |
| `NES-LTER_AE2426_ag_202411061634_003m_R1.sb` | `.sb` | 13,616 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411070844_003m_R1.sb` | `.sb` | 13,621 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411071321_004m_R1.sb` | `.sb` | 13,624 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411081114_003m_R1.sb` | `.sb` | 13,648 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411081827_003m_R1.sb` | `.sb` | 13,576 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411090118_004m_R1.sb` | `.sb` | 13,633 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411100355_004m_R1.sb` | `.sb` | 13,612 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411100657_003m_R1.sb` | `.sb` | 13,616 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411100954_003m_R1.sb` | `.sb` | 13,624 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411101306_002m_R1.sb` | `.sb` | 13,611 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411110300_004m_R1.sb` | `.sb` | 13,617 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |
| `NES-LTER_AE2426_ag_202411110643_003m_R1.sb` | `.sb` | 13,626 | Text (SeaBASS) | UTF-8 | Comma | 551 | 3 | CDOM absorption spectrum |

---

## SeaBASS format details

All `.sb` files conform to NASA's SeaBASS data file specification:

1. **Header Structure**:
   - The header begins with `/begin_header` and ends with `/end_header`.
   - Lines inside the header starting with `/` denote key-value metadata pairs (e.g. `/fields=`, `/units=`, `/missing=`).
   - Lines starting with `!` are comments, which are ignored during data parsing.
2. **Tabular Data Structure**:
   - The data block starts immediately after `/end_header`.
   - Values are comma-separated (specified by `/delimiter=comma`).
   - The encoding is ASCII/UTF-8 text.
3. **Missing Value Conventions**:
   - `/missing=-9999` is used across all files to indicate missing observations.
   - `/below_detection_limit=-8888` is used in the HPLC file to indicate values below the instrument detection threshold.
4. **Variable Definitions**:
   - **CDOM**:
     - `wavelength`: Wavelength in nanometers (unit: `nm`).
     - `ag`: Gelbstoff/CDOM absorption coefficient (unit: `1/m`).
     - `abs_ag`: Gelbstoff/CDOM absorbance (unit: `unitless`).
   - **HPLC**:
     - Contains 51 fields including `station`, `bottle`, `depth`, `sample` (HSL ID), `hplc_gsfc_id`, `volfilt` (Liters filtered), `Tot_Chl_a`, `Tot_Chl_b`, `Tot_Chl_c` (pigment concentrations in $mg/m^3$), accessory pigments, and derived ratios.
