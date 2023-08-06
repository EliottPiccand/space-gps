# Space GPS

The goal of this project is to create an algorithme taking as input :
- a solar system
- a starting astre
- a target astre

and output a list of `(pos, tst)` tuple where `tst` is the thrust the engine should give when the position `pos` is reached.

## Hypotesis
The goal is to make this algorithme as accurate as possible with respect to the laws of physics, but the problem must first be simplified :
- the astres follow only circular orbits
- relativistic phyisic is not taken into account
- there is no other astre in the system that the starting one and the target one
