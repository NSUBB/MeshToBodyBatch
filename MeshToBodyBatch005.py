import FreeCAD
import FreeCADGui
import Mesh
import Part
import PartDesign
from PySide import QtGui, QtCore
import time

# --- Fallback comprehensive manual repair ---
def attempt_comprehensive_manual_repair(mesh_obj):
    """
    Comprehensive manual repair using direct Mesh API methods.
    This function now handles the mutable object creation internally.
    """
    try:
        # Get the current mesh data (which might be immutable if directly from doc object property)
        original_mesh_topology = mesh_obj.Mesh.Topology
        # Create a new, independent, and mutable Mesh.Mesh object for modifications
        mutable_mesh = Mesh.Mesh(original_mesh_topology)
        FreeCAD.Console.PrintMessage(f"🔧 Falling back to manual comprehensive repair for '{mesh_obj.Name}'...\n")

        repairs_applied = []
        # Flag to track if self-intersections were successfully fixed on the mutable_mesh (internal check)
        self_intersections_fixed_on_mutable = False

        # --- DIAGNOSTIC: Initial solid status of mutable_mesh ---
        FreeCAD.Console.PrintMessage(f"📊 DIAGNOSTIC: Mutable mesh initial Solid: {mutable_mesh.isSolid()}, Points: {mutable_mesh.CountPoints}, Facets: {mutable_mesh.CountFacets}\n")


        # Prioritize fixing self-intersections immediately if detected
        initial_has_self_intersections = mutable_mesh.hasSelfIntersections()
        
        if initial_has_self_intersections:
            FreeCAD.Console.PrintMessage("🔧 Fix self-intersections (priority pass)...)\n")
            try:
                mutable_mesh.fixSelfIntersections()
                repairs_applied.append("Fix self-intersections (priority)")
                
                # --- DIAGNOSTIC: Solid status after fixSelfIntersections ---
                FreeCAD.Console.PrintMessage(f"📊 DIAGNOSTIC: Solid after fixSelfIntersections: {mutable_mesh.isSolid()}, Points: {mutable_mesh.CountPoints}, Facets: {mutable_mesh.CountFacets}\n")

                # After fixing self-intersections, harmonize normals as they often get messed up
                FreeCAD.Console.PrintMessage("🔧 Harmonize Normals (after self-intersection fix)...\n")
                mutable_mesh.harmonizeNormals()
                repairs_applied.append("Harmonize Normals (after self-intersection fix)")

                # --- DIAGNOSTIC: Solid status after harmonizeNormals (post-self-intersection) ---
                FreeCAD.Console.PrintMessage(f"📊 DIAGNOSTIC: Solid after Harmonize Normals (post-SI fix): {mutable_mesh.isSolid()}, Points: {mutable_mesh.CountPoints}, Facets: {mutable_mesh.CountFacets}\n")

                # Re-check self-intersections on the mutable_mesh itself
                if not mutable_mesh.hasSelfIntersections():
                    FreeCAD.Console.PrintMessage("✅ Self-intersections fixed in mutable mesh (internal check).\n")
                    self_intersections_fixed_on_mutable = True # Mark as fixed
                else:
                    FreeCAD.Console.PrintMessage("❌ Self-intersections persist in mutable mesh after priority fix (internal check).\n")

            except Exception as e:
                FreeCAD.Console.PrintMessage(f"🔧 Fix self-intersections (priority pass) failed: {e}\n")


        # Apply other general repair methods on the mutable_mesh
        # Exclude 'fixSelfIntersections' and 'harmonizeNormals' from this loop if they were handled above
        repair_methods = [
            ("removeDuplicatedPoints", "Remove duplicate points"),
            ("removeDuplicatedFacets", "Remove duplicate facets"),
            ("removeInvalidPoints", "Remove invalid points"),
            ("removeNonManifolds", "Remove non-manifolds"),
            ("removeFoldsOnSurface", "Remove surface folds"),
        ]

        for method_name, description in repair_methods:
            try:
                if hasattr(mutable_mesh, method_name):
                    FreeCAD.Console.PrintMessage(f"🔧 {description}...\n")
                    method = getattr(mutable_mesh, method_name)
                    method()
                    repairs_applied.append(description)
                    # --- DIAGNOSTIC: Solid status after each general repair step ---
                    FreeCAD.Console.PrintMessage(f"📊 DIAGNOSTIC: Solid after {method_name}: {mutable_mesh.isSolid()}, Points: {mutable_mesh.CountPoints}, Facets: {mutable_mesh.CountFacets}\n")

            except Exception as e:
                FreeCAD.Console.PrintMessage(f"🔧 {description} failed: {e}\n")

        # Try additional cleanup (on the mutable mesh)
        try:
            FreeCAD.Console.PrintMessage("🔧 Fill small holes...\n")
            mutable_mesh.fillupHoles(100)
            repairs_applied.append("Fill small holes")
            # --- DIAGNOSTIC: Solid status after fillupHoles ---
            FreeCAD.Console.PrintMessage(f"📊 DIAGNOSTIC: Solid after fillupHoles: {mutable_mesh.isSolid()}, Points: {mutable_mesh.CountPoints}, Facets: {mutable_mesh.CountFacets}\n")

        except Exception as e:
            FreeCAD.Console.PrintMessage(f"🔧 Fill small holes failed: {e}\n")

        if repairs_applied:
            # Assign the modified mutable mesh back to the original document object
            mesh_obj.Mesh = mutable_mesh
            
            # Recompute multiple times to ensure FreeCAD's internal caches are fully updated
            FreeCAD.ActiveDocument.recompute()
            FreeCAD.ActiveDocument.recompute()
            FreeCAD.ActiveDocument.recompute()

            # Get the latest state from the document object AFTER recompute
            current_mesh_data = mesh_obj.Mesh
            is_solid = current_mesh_data.isSolid()
            has_non_manifolds = current_mesh_data.hasNonManifolds()
            
            # Determine the final self-intersection status based on the internal check if performed
            # Otherwise, rely on the document object's updated report.
            final_has_self_intersections = current_mesh_data.hasSelfIntersections() # Default to document's report
            if initial_has_self_intersections: # Only override if the priority fix was attempted
                final_has_self_intersections = not self_intersections_fixed_on_mutable


            FreeCAD.Console.PrintMessage(f"🔧 Manual repairs applied: {', '.join(repairs_applied)}\n")
            FreeCAD.Console.PrintMessage(f"🔧 Result: Solid={is_solid}, Non-manifolds={has_non_manifolds}, Self-intersections={final_has_self_intersections}\n")

            # Adjust return condition to use the accurate self-intersection status
            return is_solid and not has_non_manifolds and not final_has_self_intersections
        else:
            FreeCAD.Console.PrintMessage("🔧 No manual repairs were successfully applied.\n")
            return False # No repairs means no success

    except Exception as e:
        FreeCAD.Console.PrintError(f"Manual repair error for '{mesh_obj.Name}': {e}\n")
        return False


# --- Updated main repair function that tries all methods ---
def attempt_mesh_repair(mesh_obj, has_non_manifolds=None, has_self_intersections=None):
    """
    Main repair function that only attempts the comprehensive manual repair approach.
    Returns True if repair was successful, False otherwise.
    """
    try:
        FreeCAD.Console.PrintMessage(f"🔧 === Starting repair for '{mesh_obj.Name}' ===\n")

        # Only call the comprehensive manual repair, as it's the one that can be fixed
        success = attempt_comprehensive_manual_repair(mesh_obj)

        if success:
            FreeCAD.Console.PrintMessage("🔧 REPAIR: Automatic repair successful - proceeding with conversion\n")
            return True
        else:
            FreeCAD.Console.PrintMessage("🔧 REPAIR: Automatic repair failed - skipping this mesh\n")
            return False

    except Exception as e:
        FreeCAD.Console.PrintError(f"All repair methods failed for '{mesh_obj.Name}': {e}\n")
        return False


# --- Automated mesh evaluation function ---
def evaluate_mesh_automated(selected_mesh):
    """
    Automated mesh evaluation that replaces the GUI popup.
    Returns: 'proceed', 'repair', or 'cancel' based on mesh quality.
    """
    try:
        mesh = selected_mesh.Mesh

        # Core evaluation
        is_solid = mesh.isSolid()
        has_non_manifolds = mesh.hasNonManifolds()
        has_self_intersections = mesh.hasSelfIntersections()

        # Log the evaluation results
        FreeCAD.Console.PrintMessage(f"\n=== MESH EVALUATION: {selected_mesh.Name} ===\n")
        FreeCAD.Console.PrintMessage(f"Points: {mesh.CountPoints}, Facets: {mesh.CountFacets}\n")
        FreeCAD.Console.PrintMessage(f"Is Solid: {'YES' if is_solid else 'NO'}\n")
        FreeCAD.Console.PrintMessage(f"Has Non-Manifolds: {'YES' if has_non_manifolds else 'NO'}\n")
        FreeCAD.Console.PrintMessage(f"Has Self-Intersections: {'YES' if has_self_intersections else 'NO'}\n")

        if is_solid:
            FreeCAD.Console.PrintMessage(f"Volume: {mesh.Volume:.3f}\n")
            FreeCAD.Console.PrintMessage(f"Surface Area: {mesh.Area:.3f}\n")

        # Decision logic
        if is_solid and not has_non_manifolds and not has_self_intersections:
            FreeCAD.Console.PrintMessage("✅ DECISION: Mesh is clean - proceeding with conversion\n")
            return "proceed"

        elif is_solid and (has_non_manifolds or has_self_intersections):
            FreeCAD.Console.PrintMessage("⚠️  DECISION: Mesh is solid but has issues - attempting automatic repair\n")

            # Attempt automatic repair using improved repair system
            # Pass existing evaluation results to avoid re-calculating (though not strictly necessary now)
            repair_success = attempt_mesh_repair(selected_mesh, has_non_manifolds, has_self_intersections)

            if repair_success:
                FreeCAD.Console.PrintMessage("🔧 REPAIR: Automatic repair successful - proceeding with conversion\n")
                return "proceed"
            else:
                # If repair failed, it should return 'repair' to indicate it needs further attention
                FreeCAD.Console.PrintMessage("🔧 REPAIR: Automatic repair failed - skipping this mesh\n")
                return "repair"

        else:
            FreeCAD.Console.PrintMessage("❌ DECISION: Mesh is not solid - skipping this mesh\n")
            return "repair"

    except Exception as e:
        FreeCAD.Console.PrintError(f"Mesh evaluation error for '{selected_mesh.Name}': {e}\n")
        return "cancel"


# --- Function to find all mesh objects in document ---
def find_all_mesh_objects(doc=None):
    """
    Find all mesh objects in the document.
    Returns list of mesh objects and summary info.
    """
    if doc is None:
        doc = FreeCAD.ActiveDocument

    if not doc:
        FreeCAD.Console.PrintError("No active document found.\n")
        return [], {}

    all_objects = doc.Objects
    mesh_objects = []

    for obj in all_objects:
        if hasattr(obj, 'Mesh') and isinstance(obj.Mesh, Mesh.Mesh):
            mesh_objects.append(obj)

    # Generate summary
    summary = {
        'total_objects': len(all_objects),
        'mesh_objects': len(mesh_objects),
        'mesh_names': [obj.Name for obj in mesh_objects]
    }

    return mesh_objects, summary


# --- Single mesh conversion function ---
def convert_single_mesh(mesh_obj, base_transaction=False):
    """
    Convert a single mesh to PartDesign Body.
    Returns (success: bool, body_name: str or None)
    """
    doc = FreeCAD.ActiveDocument

    if not base_transaction:
        doc.openTransaction(f"Convert Mesh: {mesh_obj.Name}")

    try:
        # Evaluate mesh
        evaluation_result = evaluate_mesh_automated(mesh_obj)

        if evaluation_result != "proceed":
            if not base_transaction:
                doc.abortTransaction()
            return False, None

        FreeCAD.Console.PrintMessage(f"🔄 Starting conversion of '{mesh_obj.Name}'...\n")

        base_name = mesh_obj.Name

        # Convert Mesh to Shape
        shape_obj = doc.addObject('Part::Feature', base_name + "_shape")
        shape = Part.Shape()
        # Pass the entire Topology tuple here as well
        shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1, False)
        shape_obj.Shape = shape
        shape_obj.purgeTouched()

        # Convert to Solid
        solid_obj = doc.addObject("Part::Feature", base_name + "_solid")
        solid_obj.Shape = Part.Solid(Part.Shell(shape_obj.Shape.Faces))

        # Refine Shape
        refined_obj = doc.addObject("Part::Refine", base_name + "_solid_refined")
        refined_obj.Source = solid_obj
        solid_obj.Visibility = False

        doc.recompute()

        if refined_obj.Shape and refined_obj.Shape.isValid():
            simple_copy_obj = doc.addObject("Part::Feature", base_name + "_solid_simple")
            simple_copy_obj.Shape = refined_obj.Shape

            body_obj = doc.addObject("PartDesign::Body", base_name + "_Body")
            body_obj.BaseFeature = simple_copy_obj
            simple_copy_obj.Visibility = False

            # Cleanup intermediate objects
            doc.removeObject(shape_obj.Name)
            doc.removeObject(solid_obj.Name)
            doc.removeObject(refined_obj.Name)

            # Remove original mesh
            doc.removeObject(mesh_obj.Name)

            doc.recompute()

            FreeCAD.Console.PrintMessage(f"✅ Successfully created: {body_obj.Name}\n")

            if not base_transaction:
                doc.commitTransaction()

            return True, body_obj.Name

        else:
            raise ValueError("Refined solid was invalid")

    except Exception as e:
        # Cleanup on error
        temp_objects = [name for name in [
            base_name + "_shape",
            base_name + "_solid",
            base_name + "_solid_refined",
            base_name + "_solid_simple"
        ] if doc.getObject(name)]

        for obj_name in temp_objects:
            try:
                doc.removeObject(obj_name)
            except:
                pass

        if not base_transaction:
            doc.abortTransaction()

        FreeCAD.Console.PrintError(f"❌ Conversion failed for '{mesh_obj.Name}': {e}\n")
        return False, None


# --- Document-wide conversion function ---
def convert_all_document_meshes(show_summary=True):
    """
    Convert all mesh objects in the current document to PartDesign Bodies.
    Returns conversion statistics.
    """
    start_time = time.time()
    doc = FreeCAD.ActiveDocument

    if not doc:
        FreeCAD.Console.PrintError("No active document found.\n")
        return None

    # Find all mesh objects
    mesh_objects, summary = find_all_mesh_objects(doc)

    if not mesh_objects:
        FreeCAD.Console.PrintMessage("No mesh objects found in document.\n")
        return {'total_meshes': 0, 'converted': 0, 'failed': 0, 'skipped': 0}

    # Show initial summary
    FreeCAD.Console.PrintMessage(f"\n{'='*60}\n")
    FreeCAD.Console.PrintMessage(f"DOCUMENT-WIDE MESH CONVERSION\n")
    FreeCAD.Console.PrintMessage(f"{'='*60}\n")
    FreeCAD.Console.PrintMessage(f"Document: {doc.Name}\n")
    FreeCAD.Console.PrintMessage(f"Total objects: {summary['total_objects']}\n")
    FreeCAD.Console.PrintMessage(f"Mesh objects found: {summary['mesh_objects']}\n")

    if show_summary:
        FreeCAD.Console.PrintMessage(f"Meshes to process: {', '.join(summary['mesh_names'])}\n")

    FreeCAD.Console.PrintMessage(f"{'='*60}\n")

    # Open master transaction
    doc.openTransaction("Convert All Document Meshes")

    # Process each mesh
    results = {
        'total_meshes': len(mesh_objects),
        'converted': 0,
        'failed': 0,
        'skipped': 0,
        'converted_objects': [],
        'failed_objects': [],
        'skipped_objects': []
    }

    try:
        for i, mesh_obj in enumerate(mesh_objects, 1):
            FreeCAD.Console.PrintMessage(f"\n[{i}/{len(mesh_objects)}] Processing: {mesh_obj.Name}\n")
            FreeCAD.Console.PrintMessage("-" * 50 + "\n")

            # Store original name for tracking
            original_name = mesh_obj.Name

            success, body_name = convert_single_mesh(mesh_obj, base_transaction=True)

            if success:
                results['converted'] += 1
                results['converted_objects'].append({'original': original_name, 'body': body_name})
            else:
                # Check if it was skipped due to quality issues vs actual failure
                if doc.getObject(original_name) and doc.getObject(original_name).TypeId == 'Mesh::Feature':  # Original mesh still exists
                    results['skipped'] += 1
                    results['skipped_objects'].append(original_name)
                else:
                    results['failed'] += 1
                    results['failed_objects'].append(original_name)

        # Commit the master transaction
        doc.commitTransaction()

    except Exception as e:
        doc.abortTransaction()
        FreeCAD.Console.PrintError(f"Master conversion process failed: {e}\n")
        return None

    # Final recompute
    doc.recompute()

    # Calculate timing
    end_time = time.time()
    total_time = end_time - start_time

    # Print final summary
    FreeCAD.Console.PrintMessage(f"\n{'='*60}\n")
    FreeCAD.Console.PrintMessage(f"CONVERSION COMPLETE\n")
    FreeCAD.Console.PrintMessage(f"{'='*60}\n")
    FreeCAD.Console.PrintMessage(f"Total meshes processed: {results['total_meshes']}\n")
    FreeCAD.Console.PrintMessage(f"✅ Successfully converted: {results['converted']}\n")
    FreeCAD.Console.PrintMessage(f"⏭️  Skipped (quality issues): {results['skipped']}\n")
    FreeCAD.Console.PrintMessage(f"❌ Failed (errors): {results['failed']}\n")
    FreeCAD.Console.PrintMessage(f"⏱️  Total time: {total_time:.2f} seconds\n")

    if results['converted'] > 0:
        FreeCAD.Console.PrintMessage(f"⚡ Average time per conversion: {total_time/results['converted']:.2f} seconds\n")

    if results['converted_objects']:
        FreeCAD.Console.PrintMessage(f"\nConverted objects:\n")
        for item in results['converted_objects']:
            FreeCAD.Console.PrintMessage(f"  {item['original']} → {item['body']}\n")

    if results['skipped_objects']:
        FreeCAD.Console.PrintMessage(f"\nSkipped objects (need manual repair):\n")
        for name in results['skipped_objects']:
            FreeCAD.Console.PrintMessage(f"  {name}\n")

    if results['failed_objects']:
        FreeCAD.Console.PrintMessage(f"\nFailed objects:\n")
        for name in results['failed_objects']:
            FreeCAD.Console.PrintMessage(f"  {name}\n")

    FreeCAD.Console.PrintMessage(f"{'='*60}\n")

    return results


# --- Quick document analysis function ---
def analyze_document_meshes():
    """
    Analyze all meshes in document without converting them.
    Useful for previewing what would happen.
    """
    mesh_objects, summary = find_all_mesh_objects()

    if not mesh_objects:
        FreeCAD.Console.PrintMessage("No mesh objects found in document.\n")
        return

    FreeCAD.Console.PrintMessage(f"\n{'='*60}\n")
    FreeCAD.Console.PrintMessage(f"DOCUMENT MESH ANALYSIS\n")
    FreeCAD.Console.PrintMessage(f"{'='*60}\n")

    analysis_results = {
        'clean': 0,
        'repairable': 0,
        'problematic': 0
    }

    for mesh_obj in mesh_objects:
        # Pass the mesh_obj to evaluate_mesh_automated so it can perform repairs
        evaluation = evaluate_mesh_automated(mesh_obj)
        if evaluation == "proceed":
            analysis_results['clean'] += 1
        elif evaluation == "repair":
            analysis_results['repairable'] += 1
        else: # 'cancel' or other error
            analysis_results['problematic'] += 1

    FreeCAD.Console.PrintMessage(f"\nSUMMARY:\n")
    FreeCAD.Console.PrintMessage(f"✅ Clean meshes (ready to convert): {analysis_results['clean']}\n")
    FreeCAD.Console.PrintMessage(f"🔧 Meshes needing repair (or failed repair): {analysis_results['repairable']}\n")
    FreeCAD.Console.PrintMessage(f"❌ Problematic meshes (evaluation error): {analysis_results['problematic']}\n")
    FreeCAD.Console.PrintMessage(f"{'='*60}\n")


# --- Main execution ---
if __name__ == "__main__":
    # Choose your execution mode:

    # Convert all meshes in document:
    convert_all_document_meshes()

    # Just analyze without converting:
    # analyze_document_meshes()

    # Get detailed summary:
    # results = convert_all_document_meshes(show_summary=True)
    # if results:
    #     print(f"Conversion efficiency: {results['converted']/results['total_meshes']*100:.1f}%")