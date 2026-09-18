# Abaqus coordinate load mapper

Convert coordinate-defined paired forces into nearest-node loads and a CLOAD include fragment. Adapted and refactored from research preprocessing scripts with generic identifiers and entirely synthetic examples.

## Run

Python 3.9 or newer; no third-party packages required.

```sh
python map_loads.py nodes.csv forces.csv --tolerance 0.05 --output loads.inp --audit mapping.csv
python -m unittest discover -s tests -v
```

The example maps two tensile force pairs (10 and 5 force units) onto four nodes in two instances. `mapping.csv` records each endpoint's selected node and distance. All coordinates and the tolerance must share a common length unit and assembly coordinate frame. Forces must use the model's consistent force unit.

## Input and mapping rules

- Node columns: `instance,node_id,x,y,z`.
- Force columns: `load_id,origin_instance,insertion_instance,ox,oy,oz,ix,iy,iz,force`.
- Each row's `force` is the magnitude of that pair. Divide a group's total force among rows before calling the tool if distributing it across multiple pairs.
- Origin force points toward the insertion; insertion receives the opposite force. This convention represents a tensile connector between endpoints.
- Each endpoint maps only within its explicitly named instance. Equal-distance ties and mappings beyond the supplied tolerance fail.
- Contributions at the same instance/node are added. Instance-qualified node labels avoid collisions across parts.

## Abaqus use and limits

Insert the generated CLOAD fragment inside the intended analysis step. Use an appropriate load operation when combining with existing load definitions; inspect the assembled deck before solving. This tool does not edit or validate an existing analysis model.

Unlike local part-node coordinates, these node coordinates must already include instance translations and rotations. The companion node parser does not perform those transforms. The nearest-node method does not distribute load across a surface or preserve moments after snapping. Check mapping distances, resultant forces and moments for your application. No solver run is part of the standalone tests. The implementation uses a direct node search suitable for small examples; large meshes may benefit from a spatial index.

No research geometry, measured forces or project identifiers are included.
