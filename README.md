# MeshToBodyBatch
FreeCAD Macro to Convert All Meshes in the Active Document to Separate PartDesign Bodies

![MeshToBodyBATCH](https://github.com/user-attachments/assets/45d65306-9ca2-43cb-a51d-5f9f1ae65853)

https://forum.freecad.org/viewtopic.php?t=97700

## Overview

This FreeCAD macro automates the process of converting multiple mesh objects into PartDesign Bodies while ensuring mesh integrity through automatic repair routines. It evaluates each mesh, attempts automatic repairs when required, and converts valid meshes into solid bodies.

## Features

- **Automated Mesh Evaluation**: Determines if a mesh is solid and free of non-manifolds or self-intersections.
- **Comprehensive Repair System**: Applies multiple repair techniques, including fixing self-intersections, harmonizing normals, and removing duplicate points/facets.
- **Batch Processing**: Converts all mesh objects in the document in a single operation.
- **Detailed Diagnostics**: Logs mesh properties before and after repair attempts.
- **Transaction-Based Execution**: Ensures clean rollback in case of errors.

## Installation

1. Download the macro file (`MeshToBodyBatch005.py`).
2. Rename the file to `MeshToBodyBatch005.FCMacro` (optional in FreeCAD v1.0.1 which can run PY files directly).
3. Place it in your FreeCAD macros directory.
4. Open FreeCAD and run the macro from the Macro Manager.

## Usage

This macro does not require any selection to be made prior to execution. Upon execution the macro will find all mesh objects within the active document and attempt to convert them to solid bodies. This operation performs a series of tests prior to conversion, attempted automatic repairs upon failed tests, followed by **Create Shape from Mesh > Convert to Solid > Create Refined Copy > Create Simple Copy > Create New Body > Drop Simple Copy into New Body > Delete interim objects (mesh, shape, solid, refined copy)**. Meshes that fail auto repair will be aborted and the next mesh will be processed.

## Repair Methods Applied

The macro applies the following repair techniques:
- **Fix Self-Intersections**
- **Harmonize Normals**
- **Remove Duplicate Points**
- **Remove Duplicate Facets**
- **Remove Invalid Points**
- **Remove Non-Manifolds**
- **Remove Surface Folds**
- **Fill Small Holes**

## Output Summary

After execution, the macro provides a summary of the conversion process, including:
- Number of meshes processed
- Successfully converted meshes
- Skipped meshes (requiring manual repair)
- Failed conversions due to errors
- Execution time and efficiency metrics

## Example Output

```
============================================================
DOCUMENT-WIDE MESH CONVERSION
============================================================
Total meshes processed: 10
✅ Successfully converted: 7
⏭️  Skipped (quality issues): 2
❌ Failed (errors): 1
⏱️  Total time: 12.45 seconds
⚡ Average time per conversion: 1.78 seconds
============================================================
```

## Notes

- Ensure meshes are properly structured before conversion.
- If a mesh fails automatic repair, manual intervention may be required. You can try the Mesh_Evaluation tool in Mesh Workbench
- The macro removes original mesh objects after successful conversion.

## Tested on:
- Windows 11
- FreeCAD v1.0.1

## License

This macro is provided under the GPL 3.0 License. Feel free to modify and distribute.

## Author

Developed by NSUBB (DesignWeaver). Contributions and feedback are welcome!
